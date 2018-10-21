from openspy.openstack_proxy import OpenStackRestProxy, IdentityFaker
from openspy.rabbit_proxy import RabbitProxy, RabbitFaker
import logging
from munch import munchify
import json
import os
from openhurricane import hypotest
import sys
import traceback


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


class TestInjector(InspectionBase):
    LOG = logging.getLogger("TestInjector")

    def __init__(self, conf):
        super(TestInjector, self).__init__(conf)
        self.test_manager = None
        self.targeted_operation = None
        self.test_mapping = None
        self.no_injections = 1

    def inject(self, test_manager, targeted_operation, no_injections=1):
        self.test_manager = test_manager
        self.targeted_operation = targeted_operation
        self.no_injections = no_injections
        self.test_mapping = set()
        self._inspection_phase()
        self.LOG.debug(f"{len(self.test_mapping)} mapping(s) to use")
        self.LOG.debug(self.test_mapping)
        self._injection_phase()

    def _inspection_phase(self):
        inspection_handler = TestInjector.InspectionHandler(self)
        inspection_handler.run()
        self.test_manager.test_driver.delete_existent_server()

    def _injection_phase(self):
        aux_counter = 0
        for test_unit_mapping in self.test_mapping:
            self.LOG.debug(f"ROBTEST {aux_counter}/{len(self.test_mapping)} BEGIN")
            injection_handler = TestInjector.InjectionHandler(self, test_unit_mapping)
            injection_handler.run()
            self.test_manager.test_driver.delete_existent_server()
            self.LOG.debug(f"ROBTEST {aux_counter}/{len(self.test_mapping)} END")
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
            path_split = mapping.path.split('.')
            current_obj = app_json
            path_item = path_split[0]
            for i in range(1, len(path_split) - 1):
                path_item = path_split[i]
                if path_item not in current_obj:
                    self.LOG.error(f"{path_item} is not in {current_obj.keys()}")
                current_obj = current_obj[path_item]
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