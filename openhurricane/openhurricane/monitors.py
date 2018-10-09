import logging
from openhurricane.base import ComputeTestBase
from openhurricane import waiters


class ComputeTestMonitor(ComputeTestBase):
    LOG = logging.getLogger("ComputeTestMonitor")

    def __init__(self, conf, state_map, test_driver):
        super(ComputeTestMonitor, self).__init__(conf)
        self.state_map = state_map
        self._waiters = [
            waiters.InstanceRunningWaiter(self)
        ]
        self.test_driver = test_driver

    def await_and_monitor_execution(self, expected_set):
        for waiter in self._waiters:
            for expected in expected_set:
                waiter.await_if_needed(expected)