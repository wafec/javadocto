import time
import logging


class BaseWaiter:
    TIMEOUT = 140

    def __init__(self, test_monitor):
        self.test_monitor = test_monitor

    def is_needed(self, expected, state_name):
        if expected.qualifiedName.endswith(".GoodTransitionResult"):
            if expected.extras.destination in self.test_monitor.state_map:
                return self.get_state_name(expected) == state_name
        return False

    def get_state_name(self, expected):
        return self.test_monitor.state_map[expected.extras.destination]


class InstanceWaiter(BaseWaiter):
    LOG = logging.getLogger("InstanceWaiter")

    def __init__(self, test_monitor, status, name):
        super(InstanceWaiter, self).__init__(test_monitor)
        self.status = status
        self.name = name

    def await_if_needed(self, expected):
        if self.is_needed(expected, self.name):
            self.LOG.debug(f"IS NEEDED {self.name}")
            start = time.time()
            while True:
                server = self.test_monitor.compute_client.servers.get(self.test_monitor.test_driver.server.id)
                elapsed = time.time() - start
                if server.status.lower() == self.status or elapsed > self.TIMEOUT:
                    break
                #assert server.status.lower() != 'error', 'Server status is error'
                self.LOG.warn(f"SERVER STATUS {server.status.lower()} != {self.status}")
                if server.status.lower() == 'error':
                    if server.fault:
                        self.LOG.error(repr(server.fault))

                        time.sleep(5)
                        break
                time.sleep(1)
            assert server.status.lower() == self.status, \
                f"Server status is {server.status.lower()} rather than {self.status} [{elapsed}]"


class InstanceRunningWaiter(InstanceWaiter):
    def __init__(self, test_monitor):
        super(InstanceRunningWaiter, self).__init__(test_monitor, "active", "InstanceRunning")


class InstanceShelvedWaiter(InstanceWaiter):
    def __init__(self, test_monitor):
        super(InstanceShelvedWaiter, self).__init__(test_monitor, "shelved_offloaded", "InstanceShelved")


class InstanceWaiterVMState(InstanceWaiter):
    def __init__(self, test_monitor, status, name, vm_state):
        super(InstanceWaiterVMState, self).__init__(test_monitor, status, name)
        self.vm_state = vm_state

    def await_if_needed(self, expected):
        super(InstanceWaiterVMState, self).await_if_needed(expected)
        if self.is_needed(expected, self.name):
            start = time.time()
            while True:
                server = self.test_monitor.compute_client.servers.get(self.test_monitor.test_driver.server.id)
                elapsed = time.time() - start
                if server.__dict__["OS-EXT-STS:vm_state"].lower() == self.vm_state or elapsed > self.TIMEOUT:
                    break
                self.LOG.warn(f"VM STATE {server.__dict__['OS-EXT-STS:vm_state'].lower()} != {self.vm_state}")
                time.sleep(1)
            assert server.__dict__["OS-EXT-STS:vm_state"].lower() == self.vm_state, \
                f"Server vm_state is {server.__dict__['OS-EXT-STS:vm_state'].lower()} rather than {self.vm_state} [{elapsed}]"


class InstanceFRVerifyResize(InstanceWaiterVMState):
    def __init__(self, test_monitor):
        super(InstanceFRVerifyResize, self).__init__(test_monitor, "verify_resize", "FR_VerifyResize", "resized")


class InstanceFAVerifyResize(InstanceWaiterVMState):
    def __init__(self, test_monitor):
        super(InstanceFAVerifyResize, self).__init__(test_monitor, "verify_resize", "FA_VerifyResize", "resized")