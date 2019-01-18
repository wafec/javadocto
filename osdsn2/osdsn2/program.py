import threading
import logging

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)


class ProgramSelect(object):
    def __init__(self, inputs, program_driver, interceptors, target):
        self._inputs = inputs
        self._program_driver = program_driver
        self._interceptors = interceptors
        self._aux_interceptor_count = None
        self._aux_interceptor_condition = None
        self._captured_messages = None
        self._target = target
        self._capturing = None
        self._input_running = None
        self._message_number = None

    def run(self):
        self.start_interceptors()
        self.run_inputs()

    def start_interceptors(self):
        i = 0
        self._aux_interceptor_count = 0
        self._aux_interceptor_condition = threading.Condition()
        while i < len(self._interceptors):
            ti = threading.Thread(name="interceptor%i" % i, target=self.run_interceptor, args=(i,))
            ti.start()
            i += 1
        with self._aux_interceptor_condition:
            self._aux_interceptor_condition.wait_for(self.interceptor_condition_evaluate)

    def run_interceptor(self, i):
        try:
            self._interceptors[i].add_on_running_callback(self.on_interceptor_running)
            self._interceptors[i].add_on_message_callback(self.on_message)
            self._interceptors[i].run()
        finally:
            self._interceptors[i].stop()

    def on_interceptor_running(self):
        self._aux_interceptor_count += 1
        with self._aux_interceptor_condition:
            self._aux_interceptor_condition.notifyAll()

    def interceptor_condition_evaluate(self):
        return self._aux_interceptor_condition >= len(self._interceptors)

    def run_inputs(self):
        self._captured_messages = []
        self._capturing = False
        self._message_number = 0
        self._input_running = None
        for inp in self._inputs:
            if inp.target == self._target:
                self._capturing = True
            self._input_running = inp
            self._program_driver.run_input(inp)
            self._capturing = False
            self._input_running = None

    def on_message(self, body):
        self._message_number += 1
        if self._capturing:
            self._captured_messages.append((self._input_running, self._message_number, body))

    def get_captured_messages(self):
        return self._captured_messages


def main():
    pass
