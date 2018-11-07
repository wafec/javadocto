from openspy.openstack_proxy import OpenStackRestProxy, IdentityFaker
from openspy.rabbit_proxy import RabbitProxy, RabbitFaker
import logging
from munch import munchify
import json
import os
from openhurricane import hypotest
import sys
import traceback
from openhurricane.hypotest import FaultMapper
import re
import ast
import time


class InspectionBase:
    LOG = logging.getLogger("InspectionBase")

    def __init__(self, conf):
        self.identity_faker = IdentityFaker(conf)
        self.openstack_proxy = OpenStackRestProxy(conf)
        self.rabbit_faker = RabbitFaker(conf)
        self.rabbit_proxy = RabbitProxy(conf)

    def start_services(self):
        self.openstack_proxy.start()
        self.identity_faker.safely_alter_urls()

        self.rabbit_faker.restore_bindings()
        self.rabbit_faker.alter_bindings()
        self.rabbit_proxy.start()

        OpenStackRestProxy.default_injector.handler = self
        RabbitProxy.default_injector.handler = self

    def stop_services(self):
        self.rabbit_proxy.stop()
        self.rabbit_faker.restore_bindings()
        self.openstack_proxy.stop()
        self.identity_faker.restore_urls()

        OpenStackRestProxy.default_injector.handler = None
        RabbitProxy.default_injector.handler = None

    def _get_app_json_from_amqp_data(self, data):
        return json.loads(json.loads(data)["oslo.message"])

    def _get_app_message_from_amqp_data(self, data):
        oslo_message = json.loads(data)
        app_message = munchify(json.loads(oslo_message["oslo.message"]))
        return app_message

    def _get_method_from_amqp_data(self, data):
        app_message = self._get_app_message_from_amqp_data(data)
        method = "NA" if not hasattr(app_message, 'method') else app_message.method
        return method

    def handle_injection(self, operation, message, direction, tag):
        self.LOG.debug(f"Op={operation}, Direction={direction}, Tag={tag}")
        return message


class TestInspector(InspectionBase):
    LOG = logging.getLogger("TestInspector")

    def __init__(self, conf):
        super(TestInspector, self).__init__(conf)
        self._current_test_input = None
        self._dest = None
        self._aux_counter = 0

    def inspect(self, test_manager, dest):
        self._dest = dest
        test_manager.add_listener(self)
        test_manager.run_tests()
        test_manager.remove_listener(self)

    def on_test_input_arrival(self, target, test_input):
        self.LOG.debug(f"TEST {test_input.qualifiedName} run")
        self._current_test_input = test_input

    def handle_injection(self, operation, message, direction, tag):
        message = super(TestInspector, self).handle_injection(operation, message, direction, tag)
        try:
            if tag == "AMQP":
                self._handle_AMQP(operation, message, direction)
            elif tag == "HTTP":
                self._handle_HTTP(operation, message, direction)
        except Exception as exception:
            self.LOG.error(exception)
        self._aux_counter += 1
        return message

    def _handle_AMQP(self, operation, message, direction):
        if self._current_test_input is None or self._dest is None:
            return

        data, properties = message
        method = self._get_method_from_amqp_data(data)
        app_message = self._get_app_message_from_amqp_data(data)

        filename = f"%03d_{self._current_test_input.qualifiedName}_AMQP_{operation}_{direction}_{method}.json" % self._aux_counter
        with open(os.path.join(self._dest, filename), 'w') as writter:
            writter.write(
                json.dumps(app_message, sort_keys=True, indent=4)
            )
        self.LOG.debug(f"FILE {os.path.join(self._dest, filename)}")

    def _handle_HTTP(self, operation, message, direction):
        pass

    def start_services(self):
        super(TestInspector, self).start_services()
        OpenStackRestProxy.default_injector.handler = self
        RabbitProxy.default_injector.handler = self

    def stop_services(self):
        super(TestInspector, self).stop_services()
        OpenStackRestProxy.default_injector.handler = None
        RabbitProxy.default_injector.handler = None


class TestMapper(InspectionBase):
    LOG = logging.getLogger("TestMapper")

    def __init__(self, conf):
        super(TestMapper, self).__init__(conf)
        self.test_manager = None
        self.test_slot_spec = None
        self.targeted_operation = None
        self.test_mapping = None
        self.fault_type = None

    def map(self, test_manager, test_slot_spec, fault_type=None):
        self.LOG.info(f"Start mapping for {test_slot_spec}")
        self.test_manager = test_manager
        self.test_slot_spec = test_slot_spec
        self.fault_type = fault_type
        self.targeted_operation = test_slot_spec.split(FaultMapper.REGULAR_SEPARATOR)[0]
        self.test_mapping = set()
        self.test_manager.add_listener(self)
        self.test_manager.run_tests()
        self.test_manager.remove_listener(self)
        res = [test_item for test_item in self.test_mapping if test_item.path.startswith(self.test_slot_spec)\
               and (self.fault_type is None or test_item.fault_type == self.fault_type)]
        self.LOG.info(f"{len(res)} item(s) found")
        return sorted(res, key=lambda test_item: test_item.path)

    def on_test_input_arrival(self, target, test_input):
        pass

    def handle_injection(self, operation, message, direction, tag):
        super(TestMapper, self).handle_injection(operation, message, direction, tag)
        if tag == 'AMQP':
            data, properties = message

            method = self._get_method_from_amqp_data(data)
            if method == self.targeted_operation:
                self.LOG.debug(f"Method {method} accepted")
                app_json = self._get_app_json_from_amqp_data(data)
                mapping = hypotest.FaultMapper.map(app_json, method)
                self.test_mapping.update(mapping)
        return message


class TestInjector(InspectionBase):
    LOG = logging.getLogger("TestInjector")

    def __init__(self, conf):
        super(TestInjector, self).__init__(conf)
        self.test_manager = None
        self.test_slot_spec = None
        self.test_mapping = None
        self.no_injections = 1
        self.targeted_operation = None
        self.fault_types = None
        self.fault_values = None
        self.ignore_list = None
        self.start = None
        self.end = None

    def inject(self, test_manager, test_slot_spec, no_injections=1, fault_types=None, fault_values=None, ignore=False, start=None, end=None):
        self.test_manager = test_manager
        self.test_slot_spec = test_slot_spec
        self.fault_types = fault_types
        self.fault_values = fault_values
        self.start = start
        self.end = end
        self.targeted_operation = test_slot_spec.split(FaultMapper.REGULAR_SEPARATOR)[0]
        self.no_injections = no_injections
        self._read_ignore_list(ignore)
        self.test_mapping = set()
        self._inspection_phase()
        self.LOG.info(f"{len(self.test_mapping)} mapping(s) to use")
        self.LOG.debug(self.test_mapping)
        self._injection_phase()

    def _read_ignore_list(self, ignore):
        if ignore:
            self.ignore_list = []
            with open(ignore, 'r') as stream:
                line = stream.readline()
                while line:
                    self.ignore_list.append(line)
                    line = stream.readline()

    def _inspection_phase(self):
        inspection_handler = TestInjector.InspectionHandler(self)
        inspection_handler.run()
        self.test_manager.test_driver.delete_existent_server()
        self.LOG.info(f"Filtering by {self.test_slot_spec}")
        self.LOG.info(f"Before filtering {len(self.test_mapping)}")
        self.test_mapping = [fault_item for fault_item in self.test_mapping if fault_item.path.startswith(self.test_slot_spec)]
        if self.fault_types:
            self.LOG.debug(f"ADD Filtering by {str(self.fault_types)}")
            self.test_mapping = [fault_item for fault_item in self.test_mapping if fault_item.fault_type in self.fault_types]
        if self.ignore_list:
            self.LOG.debug("ADD Filtering by ignore list")
            self.test_mapping = [fault_item for fault_item in self.test_mapping if fault_item.path not in self.ignore_list]
        self.LOG.info(f"After filtering {len(self.test_mapping)}")

    def _make_injection_of_explicit_fault(self, test_item, fault_value):
        log = self.LOG

        def take(_):
            log.debug(f"Get fault value {fault_value}")
            return fault_value

        test_item.func = take

    def _check_for_explicit_fault(self):
        if self.fault_values:
            new_mapping = {}
            for fault_item in self.test_mapping:
                new_mapping[fault_item.path] = fault_item
            self.test_mapping = set(new_mapping.values())
            new_test_mapping = []
            for fault_item in self.test_mapping:
                for fault_value in self.fault_values:
                    fault_value = ast.literal_eval(fault_value)
                    new_item = FaultMapper.FaultMapping(fault_item.path, None, fault_item.fault_type)
                    self._make_injection_of_explicit_fault(new_item, fault_value)
                    new_test_mapping.append(new_item)
            self.test_mapping = new_test_mapping

            self.LOG.debug(f"The test will use the following value for all entries: {self.fault_values}")
            self.LOG.debug(f"New test size {len(self.test_mapping)}")

    def _injection_phase(self):
        aux_counter = 0

        self._check_for_explicit_fault()
        current_path = None
        start_time = time.time()

        start = 0 if not self.start else self.start
        end = len(self.test_mapping) if not self.end else self.end

        self.LOG.info(f"The injection will happen from fault {start} to fault {end}")

        for test_unit_mapping in sorted(self.test_mapping[start:end], key=lambda fault_item: fault_item.path):
            if current_path != test_unit_mapping.path:
                if current_path:
                    self.LOG.info(f"## PARTIAL TIMING RESULT")
                    spent_time = time.time() - start_time
                    self.LOG.info(f"##  path: {current_path}")
                    self.LOG.info(f"##  time: {spent_time}")
                    self.LOG.info(f"##")
                current_path = test_unit_mapping.path
                start_time = time.time()
            self.LOG.debug(f"ROBTEST {start+aux_counter}/{len(self.test_mapping)} BEGIN")
            self.LOG.debug(f"New path taken {test_unit_mapping.path}")
            injection_handler = TestInjector.InjectionHandler(self, test_unit_mapping)
            injection_handler.run()
            self.test_manager.test_driver.delete_existent_server()
            self.LOG.debug(f"ROBTEST {start+aux_counter}/{len(self.test_mapping)} END")
            aux_counter += 1

    class InspectionHandler:
        LOG = logging.getLogger("TestInjector.Inspection")

        def __init__(self, test_injector):
            self.test_injector = test_injector

        def handle_injection(self, operation, message, direction, tag):
            try:
                if tag == 'AMQP':
                    self._handle_AMQP(operation, message, direction, tag)
            except Exception as exception:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                self.LOG.error(f"{exc_tb.tb_frame.f_code.co_filename}, {exc_tb.tb_lineno}")
                self.LOG.error(exception)

            return message

        def _handle_AMQP(self, operation, message, direction, tag):
            data, properties = message

            method = self.test_injector._get_method_from_amqp_data(data)
            if method == self.test_injector.targeted_operation:
                self.LOG.debug(f"Method {method} accepted")
                app_json = self.test_injector._get_app_json_from_amqp_data(data)
                mapping = hypotest.FaultMapper.map(app_json, method)
                self.test_injector.test_mapping.update(mapping)

        def on_test_input_arrival(self, target, test_input):
            self.LOG.debug(f"TEST {test_input.qualifiedName} run")

        def run(self):
            self.test_injector.test_manager.add_listener(self)
            OpenStackRestProxy.default_injector.handler = self
            RabbitProxy.default_injector.handler = self
            self.test_injector.test_manager.run_tests()
            self.test_injector.test_manager.remove_listener(self)
            OpenStackRestProxy.default_injector.handler = None
            RabbitProxy.default_injector.handler = None

    class InjectionHandler:
        LOG = logging.getLogger("TestInjector.Injection")

        def __init__(self, test_injector, test_unit_mapping):
            self.test_injector = test_injector
            self.test_unit_mapping = test_unit_mapping
            self._old_value = None
            self._new_value = None
            self._injection_counter = 0

        def handle_injection(self, operation, message, direction, tag):
            if self._injection_counter < self.test_injector.no_injections:
                try:
                    if tag == "AMQP":
                        message = self._handle_AMQP(operation, message, direction, tag)
                except Exception as exception:
                    self.LOG.error(traceback.format_exc())
                    self.LOG.error(exception)
            return message

        def _handle_AMQP(self, operation, message, direction, tag):
            data, properties = message

            method = self.test_injector._get_method_from_amqp_data(data)
            if method == self.test_injector.targeted_operation:
                self.LOG.debug(f"Method {method} accepted")
                app_json = self.test_injector._get_app_json_from_amqp_data(data)
                app_json = self._inject_in_app_json(self.test_unit_mapping, app_json)
                json_oslo = json.loads(data)
                json_oslo["oslo.message"] = json.dumps(app_json)
                data = json.dumps(json_oslo)
            return data, properties

        def _inject_in_app_json(self, mapping, app_json):
            self.LOG.debug(f"Injecting {mapping.fault_type} in {mapping.path}")
            path_split = re.split(f"{FaultMapper.REGULAR_SEPARATOR}|{FaultMapper.LIST_SEPARATOR}", mapping.path)
            current_obj = app_json
            path_item = path_split[0]
            for i in range(1, len(path_split) - 1):
                path_item = path_split[i]
                if path_item not in current_obj:
                    self.LOG.error(f"{path_item} is not in {current_obj.keys()}")
                current_obj = current_obj[path_item]
                if isinstance(current_obj, list):
                    if len(current_obj):
                        current_obj = current_obj[0]
                    else:
                        self.LOG.error(f"{path_item} is an empty list")
            self.LOG.debug(f"Last path item {path_item}")

            last_item = path_split[len(path_split) - 1]
            self.LOG.debug(f"Actual path item {last_item}")
            old_value = current_obj[last_item]
            current_obj[last_item] = mapping.func(current_obj[last_item])
            current_value = current_obj[last_item]
            assert old_value != current_value, f"Must be different {old_value} != {current_value}"
            self.LOG.debug(f"OLD VALUE {old_value} AND CURRENT {current_value}")
            self._old_value = old_value
            self._new_value = current_value
            self._injection_counter += 1
            return app_json

        def on_test_input_arrival(self, target, test_input):
            self.LOG.debug(f"TEST {test_input.qualifiedName} run")

        def run(self):
            self.test_injector.test_manager.add_listener(self)
            OpenStackRestProxy.default_injector.handler = self
            RabbitProxy.default_injector.handler = self
            try:
                self._injection_counter = 0
                self.test_injector.test_manager.run_tests()
                self.LOG.warn("WEIRD?! It is still alive! Or not!")
            except Exception as exception:
                self.LOG.error(exception)
                self.LOG.warn("SUSPICIOUS!! An opportunity to catch logs for investigating further!!")
            self.LOG.debug(f"### TEST SUMMARY BEGIN")
            self.LOG.debug(f"###    TEST PATH: {self.test_unit_mapping.path}")
            self.LOG.debug(f"###    TEST ORIGINAL VALUE: {self._old_value}")
            self.LOG.debug(f"###    TEST INJECTED VALUE: {self._new_value}")
            self.LOG.debug(f"###    TEST INJECTION COUNTER: {self._injection_counter}")
            self.LOG.error(f"### TEST SUMMARY END")
            self.test_injector.test_manager.remove_listener(self)
            OpenStackRestProxy.default_injector.handler = None
            RabbitProxy.default_injector.handler = None