import time


class BaseWaiter:
    def __init__(self, test_monitor):
        self.test_monitor = test_monitor

    def is_needed(self, expected, state_name):
        if expected.qualifiedName.endswith(".GoodTransitionResult"):
            if expected.extras.destination in self.test_monitor.state_map:
                return self.get_state_name(expected) == state_name
        return False

    def get_state_name(self, expected):
        return self.test_monitor.state_map[expected.extras.destination]


class InstanceRunningWaiter(BaseWaiter):
    def __init__(self, test_monitor):
        super(InstanceRunningWaiter, self).__init__(test_monitor)

    def await_if_needed(self, expected):
        if self.is_needed(expected, "InstanceRunning"):
            start = time.time()
            while True:
                server = self.test_monitor.compute_client.servers.get(self.test_monitor.test_driver.server.id)
                elapsed = time.time() - start
                if server.status == "ACTIVE" or elapsed > 10:
                    break
                time.sleep(1)