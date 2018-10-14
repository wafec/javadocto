from openspy.openstack_proxy import OpenStackRestProxy, IdentityFaker
from openspy.rabbit_proxy import RabbitProxy, RabbitFaker
import logging
from munch import munchify
import json
import os

class TestInspector:
    LOG = logging.getLogger("TestInspector")

    def __init__(self, conf):
        self.identity_faker = IdentityFaker(conf)
        self.openstack_proxy = OpenStackRestProxy(conf)
        self.rabbit_faker = RabbitFaker(conf)
        self.rabbit_proxy = RabbitProxy(conf)
        self._current_test_input = None
        self._dest = None
        self._aux_counter = 0

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

    def inspect(self, test_manager, dest):
        self._dest = dest
        self._aux_counter = 0
        test_manager.add_listener(self)
        test_manager.run_tests()
        test_manager.remove_listener(self)

    def on_test_input_arrival(self, target, test_input):
        self.LOG.debug(f"TEST {test_input.qualifiedName} run")
        self._current_test_input = test_input

    def handle_injection(self, operation, message, direction, tag):
        self.LOG.debug(f"Op={operation}, Direction={direction}, Tag={tag}")
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
        if self._current_test_input is None:
            return

        data, properties = message
        oslo_message = json.loads(data)
        app_message = munchify(json.loads(oslo_message["oslo.message"]))
        method = "NA" if not hasattr(app_message, 'method') else app_message.method

        filename = f"%03d_{self._current_test_input.qualifiedName}_AMQP_{operation}_{direction}_{method}.json" % self._aux_counter
        with open(os.path.join(self._dest, filename), 'w') as writter:
            writter.write(
                json.dumps(app_message, sort_keys=True, indent=4)
            )
        self.LOG.debug(f"FILE {os.path.join(self._dest, filename)}")

    def _handle_HTTP(self, operation, message, direction):
        pass