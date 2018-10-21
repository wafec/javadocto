from shooter import tester
from openhurricane.drivers import ComputeTestDriver
from openhurricane.monitors import ComputeTestMonitor
from openspy.openstack_proxy import OpenStackRestProxy, IdentityFaker
from openspy.rabbit_proxy import RabbitProxy, RabbitFaker


class ComputeTestManager(tester.TestManager):
    def __init__(self, test_case, conf, state_map):
        test_driver = ComputeTestDriver(conf)
        super(ComputeTestManager, self).__init__(
            test_case,
            test_driver,
            ComputeTestMonitor(conf, state_map, test_driver)
        )
        self._listeners = []

    def add_listener(self, listener):
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _update_listeners(self, test_input):
        for listener in self._listeners:
            listener.on_test_input_arrival(self, test_input)

    def _run_test_input(self, test_input):
        self._update_listeners(test_input)

        super(ComputeTestManager, self)._run_test_input(test_input)

    def run_tests(self):
        super(ComputeTestManager, self).run_tests()

