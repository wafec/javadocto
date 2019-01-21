import threading
import logging
import json
from osdsn2 import constants

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
        self._on_captured_message_callback = None

        self._lock = threading.Lock()

    def add_on_captured_message_callback(self, on_captured_message_callback):
        self._on_captured_message_callback = on_captured_message_callback

    def run(self):
        self.start_interceptors()
        self.run_inputs()

    def start_interceptors(self):
        LOGGER.info('Starting interceptors')
        i = 0
        self._aux_interceptor_count = 0
        self._aux_interceptor_condition = threading.Condition()
        while i < len(self._interceptors):
            ti = threading.Thread(name="interceptor%i" % i, target=self.run_interceptor, args=(i,))
            ti.start()
            i += 1
        with self._aux_interceptor_condition:
            self._aux_interceptor_condition.wait_for(self.interceptor_condition_evaluate_on_running)
        LOGGER.info('Interceptors started')

    def run_interceptor(self, i):
        try:
            self._interceptors[i].add_on_running_callback(self.on_interceptor_running)
            self._interceptors[i].add_on_stopping_callback(self.on_interceptor_stopping)
            self._interceptors[i].add_on_message_callback(self.on_message)
            LOGGER.info('Running interceptor %i', i)
            self._interceptors[i].run()
        except Exception as e:
            LOGGER.error(e, exc_info=True)
        finally:
            self._interceptors[i].stop()

    def on_interceptor_running(self):
        self._aux_interceptor_count += 1
        with self._aux_interceptor_condition:
            self._aux_interceptor_condition.notifyAll()

    def on_interceptor_stopping(self):
        self._aux_interceptor_count -= 1
        with self._aux_interceptor_condition:
            self._aux_interceptor_condition.notifyAll()

    def interceptor_condition_evaluate_on_running(self):
        return self._aux_interceptor_count >= len(self._interceptors)

    def interceptor_condition_evaluate_on_stopping(self):
        return self._aux_interceptor_count <= 0

    def run_inputs(self):
        self._captured_messages = []
        self._capturing = False
        self._message_number = 0
        self._input_running = None
        for inp in self._inputs:
            if self._target in inp.state_trans:
                self._capturing = True
            self._input_running = inp
            self._program_driver.run_input(inp)
            self._capturing = False
            self._input_running = None

    def on_message(self, body):
        if self._message_number is None:
            return
        with self._lock:
            self._message_number += 1
            if self._capturing:
                LOGGER.info('Message %r and %i and %s', self._input_running, self._message_number, body)
                self._captured_messages.append((self._input_running, self._message_number, body))

                new_body = self.call_on_captured_message_callback(body)
                if new_body:
                    LOGGER.info('Message changed by captured message callback')
                    LOGGER.info('%s', new_body)
                    return new_body

    def call_on_captured_message_callback(self, body):
        if self._on_captured_message_callback is None:
            return None
        new_body = self._on_captured_message_callback(self._input_running, self._message_number, body)
        return new_body

    def get_captured_messages(self):
        return self._captured_messages

    def stop(self):
        for interceptor in self._interceptors:
            interceptor.stop()
        with self._aux_interceptor_condition:
            self._aux_interceptor_condition.wait_for(self.interceptor_condition_evaluate_on_stopping)


class OsloParams(object):
    def __init__(self, body):
        self._body = body
        self._message = None
        self._method_name = None
        self._args = None
        self._params = None

    def extract_all(self):
        self.extract_message()
        self.extract_method()
        self.extract_args()

    def get_all_params(self):
        self._params = []
        self.extract_all()
        self.build_chain([], self._args)
        return self._params

    def build_chain(self, chain, arg):
        if arg is None:
            return
        if isinstance(arg, dict):
            for key in arg.keys():
                self.build_chain(chain + [key], arg[key])
                if len(chain) > 0:
                    self._params.append(Param(method_name=self._method_name,
                                              chain=chain, data_type=constants.DTYPE_DICT))
        elif isinstance(arg, list):
            if len(arg) > 0:
                self.build_chain(chain, arg[0])
                if len(chain) > 0:
                    self._params.append(Param(method_name=self._method_name,
                                              chain=chain, data_type=constants.DTYPE_LIST))
        else:
            if len(chain) > 0:
                param = Param(method_name=self._method_name,
                              chain=chain, data_type=None)
                param.infer_type(arg)
                if param.data_type:
                    self._params.append(param)
                else:
                    LOGGER.warning('Could not infer data type for %r', param)

    def extract_message(self):
        data = self._body
        if not isinstance(data, dict):
            data = json.loads(data)
        if 'oslo.message' in data:
            self._message = json.loads(data['oslo.message'])
        else:
            raise ValueError()

    def extract_method(self):
        if self._message:
            if 'method' in self._message:
                self._method_name = self._message['method']

    def extract_args(self):
        if self._message:
            if 'args' in self._message:
                self._args = self._message['args']
            else:
                raise ValueError()

    def get_new_body(self, param, new_value):
        self.extract_all()
        self.build_new_body(self._args, param.chain, new_value)
        return self.build_body()

    def build_new_body(self, arg, chain, new_value):
        if len(chain) > 1:
            if isinstance(arg, dict):
                self.build_new_body(arg[chain[0]], chain[1:], new_value)
            elif isinstance(arg, list):
                self.build_new_body(arg[0], chain, new_value)
        else:
            if len(chain) == 1:
                if isinstance(arg, dict):
                    arg[chain[0]] = new_value
                elif isinstance(arg, list):
                    arg[0] = new_value
                else:
                    LOGGER.warning('Could not to insert %s in %s to %s', new_value, chain, arg)

    def build_body(self):
        if not isinstance(self._body, dict):
            new_body = json.loads(self._body)
        else:
            new_body = dict(self._body)
        new_message = dict(self._message)
        new_message['args'] = dict(self._args)
        new_body['oslo.message'] = json.dumps(new_message)
        return json.dumps(new_body)

    def get_args_value(self, param):
        LOGGER.info('Getting args value for %r', param)
        self.extract_all()
        return self.visit_arg(self._args, param.chain)

    def visit_arg(self, arg, chain):
        if len(chain) > 1:
            if isinstance(arg, dict):
                return self.visit_arg(arg[chain[0]], chain[1:])
            elif isinstance(arg, list):
                return self.visit_arg(arg[0], chain)
            else:
                LOGGER.error('Could not continue with %s to %s', arg, chain)
                raise ValueError
        else:
            if isinstance(arg, dict):
                return arg[chain[0]]
            elif isinstance(arg, list):
                return arg[0]
            else:
                LOGGER.error('Could not continue to get for %s to %s', arg, chain)
                raise ValueError()

    def get_method_name(self):
        self.extract_all()
        return self._method_name


class Param(object):
    def __init__(self, method_name, chain, data_type):
        self.method_name = method_name
        self.chain = chain
        self.data_type = data_type

    def infer_type(self, value):
        if isinstance(value, str):
            self.data_type = constants.DTYPE_STRING
        elif isinstance(value, int):
            self.data_type = constants.DTYPE_NUMBER
        elif isinstance(value, float):
            self.data_type = constants.DTYPE_NUMBER
        elif isinstance(value, bool):
            self.data_type = constants.DTYPE_BOOLEAN

    def __repr__(self):
        return 'Method=%s, Chain=%s, Type=%s' % (self.method_name, self.chain, self.data_type)


def main():
    pass
