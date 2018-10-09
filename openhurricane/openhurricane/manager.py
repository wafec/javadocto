from shooter import tester
from openhurricane.drivers import ComputeTestDriver
from openhurricane.monitors import ComputeTestMonitor


class ComputeTestManager(tester.TestManager):
    def __init__(self, test_case, conf, state_map):
        test_driver = ComputeTestDriver(conf)
        super(ComputeTestManager, self).__init__(
            test_case,
            test_driver,
            ComputeTestMonitor(conf, state_map, test_driver)
        )