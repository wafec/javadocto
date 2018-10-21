import logging
import time

class TestManager:
    LOG = logging.getLogger("TestManager")

    def __init__(self, test_case, test_driver, test_monitor):
        self.test_case = test_case
        self.test_driver = test_driver
        self.test_monitor = test_monitor

    def run_tests(self):
        self.LOG.debug(f"TEST BEGIN {self.test_case.fictitiousName}")
        start_time = time.time()

        for test_input in self.test_case.inputSet:
            self._run_test_input(test_input)

        elapsed_time = time.time() - start_time
        self.LOG.debug(f"OVERALL TIME {elapsed_time}")

    def _run_test_input(self, test_input):
        self.LOG.debug(f"TEST INPUT {test_input.qualifiedName}")
        start_time = time.time()

        self.test_driver.run_test_input(op_name=test_input.qualifiedName)
        self.test_monitor.await_and_monitor_execution(expected_set=test_input.expectedSet)

        elapsed_time = time.time() - start_time
        self.LOG.debug(f"TEST INPUT EXECUTION END {test_input.qualifiedName}, ELAPSED {elapsed_time}")
