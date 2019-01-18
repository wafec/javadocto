import threading

class ProgramSelect(object):
    def __init__(self, inputs, program_driver, interceptors):
        self._inputs = inputs
        self._program_driver = program_driver
        self._interceptors = interceptors

    def run(self):
        self.start_interceptors()
        self.run_inputs()

    def start_interceptors(self):
        for interceptor in self._interceptors:
            threading.Thread(target=interceptor.run).start()
            