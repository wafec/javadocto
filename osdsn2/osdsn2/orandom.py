from osdsn2 import program
from osdsn2 import input as input2
import random
from osdsn2 import experiment
from osdsn2 import driver
import logging
import argparse
import pickle
from osdsn2 import mutation
from osdsn2 import exceptions
from osdsn2 import population


LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)


class MessageInput(input2.Input):
    def __init__(self, name, args, waits, state_trans, timeout_p1=None, timeout_p2=None):
        super(MessageInput, self).__init__(name, args, waits, state_trans, timeout_p1, timeout_p2)
        self._message_map = {}

    def add_message(self, index, message):
        if index not in self._message_map:
            self._message_map[index] = []
        self._message_map[index].append(message)
        LOGGER.info(f"Message ({index}, {str(message)[0:15]}) added to input {repr(self)[0:15]}")

    def get_messages(self):
        messages = []
        for index in sorted(self._message_map.keys()):
            for message in self._message_map[index]:
                messages.append((index, message))
        return messages

    def number_of_messages(self):
        return len(self.get_messages())

    def __repr__(self):
        return super(MessageInput, self).__repr__() + ", NoMsg=%d" % (self.number_of_messages())


class InputSpec(object):
    RANDOM_TAG = driver.OSDriver.GENERIC_WAIT

    def __init__(self, name, args, limits, waits=[], timeout_p1=120, timeout_p2=20):
        self._name = name
        self._args = args
        self._range = limits
        self._waits = waits
        self._timeout_p1 = timeout_p1
        self._timeout_p2 = timeout_p2

    def random_instance(self):
        inp2 = MessageInput(
            name=self._name,
            args=self.random_args(),
            waits=[InputSpec.RANDOM_TAG] + self._waits,
            state_trans=InputSpec.RANDOM_TAG,
            timeout_p1=self._timeout_p1,
            timeout_p2=self._timeout_p2
        )
        return inp2

    def random_args(self):
        args = {}
        for arg, ran in zip(self._args, self._range):
            args[arg] = random.randrange(ran[0], ran[1])
        return args


class RandomWorkload(object):
    def __init__(self, input_spec_set, program_driver, interceptors):
        self._input_spec_set = input_spec_set
        self.workload = None
        self.program_driver = program_driver
        self.interceptors = interceptors

    def define_workload(self, workload_size):
        self.workload = []
        for _ in range(0, workload_size):
            i = random.randrange(0, len(self._input_spec_set))
            input_spec = self._input_spec_set[i]
            instance = input_spec.random_instance()
            self.workload.append(instance)
            LOGGER.info(f"Workload Input, {repr(instance)}")

    def run(self, workload_size):
        self.define_workload(workload_size)
        pg = program.ProgramSelect(
            inputs=self.workload,
            program_driver=self.program_driver,
            interceptors=self.interceptors,
            target=InputSpec.RANDOM_TAG
        )

        pg.add_on_captured_message_callback(self.on_captured_message)

        try:
            pg.run()
        finally:
            self.program_driver.delete_created_resources()
            pg.stop()

    def on_captured_message(self, message_input, message_index, message_itself):
        if isinstance(message_input, MessageInput):
            message_input.add_message(message_index, message_itself)
        else:
            LOGGER.warning(f"Input {repr(message_input)} is not an instance of MessageInput")
        return None


class RandomOptions(object):
    def __init__(self):
        self._options = None
        self._workload = None

    def create_options(self, workload):
        self._workload = workload
        self.initialize_options()
        return self._options

    def get_options(self):
        return self._options

    def initialize_options(self):
        self._options = []
        for workload_input in self._workload:
            for index, message in workload_input.get_messages():
                oslo_params = program.OsloParams(message).get_all_params()
                for oslo_param in oslo_params:
                    self._options.append((oslo_param, message, index, workload_input))
        self.turn_options_elements_distinct()
        self.initialize_sample()
        self._dump_options()

    def turn_options_elements_distinct(self):
        def is_in(option, options):
            option_param, _, option_index, _ = option
            for x in options:
                x_param, _, x_index, _ = x
                if x_index == option_index:
                    if x_param.method_name == option_param.method_name:
                        if len(x_param.chain) == len(option_param.chain):
                            flg = True
                            for e1, e2 in zip(x_param.chain, option_param.chain):
                                if e1 != e2:
                                    flg = False
                                    break
                            if flg:
                                return True
            return False

        aux = []
        for option in self._options:
            if not is_in(option, aux):
                aux.append(option)
        LOGGER.warning(f"Options reduced from {len(self._options)} to {len(aux)}")
        self._options = aux

    def initialize_sample(self):
        n = len(self._options)
        desired = population.sample_size(n)
        self._options = random.sample(self._options, desired)
        LOGGER.debug(f"Sample from {n} to {len(self._options)}")

    def _dump_options(self):
        for oslo_params, _, index, _ in self._options:
            LOGGER.info(f"Chain={oslo_params}, Index={index}")


class RandomFaultload(object):
    def __init__(self, interceptors):
        self._options = None
        self._workload = None
        self._mutation_select_il = None
        self._mutation_index_il = None
        self._mutation_param_il = None
        self._program = None
        self._interceptors = interceptors
        self._driver = None

    def initialize_test_system(self):
        self._driver = driver.example_osdriver()
        self._program = program.ProgramSelect(
            self._workload,
            self._driver,
            self._interceptors,
            None
        )

    def on_captured_message(self, message_input, message_index, message_itself):
        oslo_param = program.OsloParams(message_itself)
        if message_index == self._mutation_index_il:
            mb = oslo_param.get_new_body(self._mutation_param_il,
                                         self._mutation_select_il.next_mutation_value(
                                             oslo_param.get_args_value(self._mutation_param_il)
                                         ))
            LOGGER.info(f"Mutation going to be applied for {message_index}.")
            return mb
        return None

    def run(self, workload, options):
        self._options = options
        self._workload = workload

        # TODO: auto sample, stack and unstack auto via sysevents
        for param, message, index, workload_input in self._options:
            try:
                self.initialize_test_system()
                self._program.prep_run()

                self._mutation_index_il = index
                self._mutation_param_il = param
                self._mutation_select_il = mutation.MutationSelect(param)
                while self._mutation_select_il.has_mutations():
                    try:
                        self._program.add_on_captured_message_callback(self.on_captured_message)
                        self._program.run_inputs()
                    except TimeoutError as e:
                        LOGGER.error(e, exc_info=e)
                    except exceptions.ResourceNotFound as e:
                        LOGGER.error(e, exc_info=e)
                    finally:
                        self._program.add_on_captured_message_callback(None)
                        self._driver.delete_created_resources()
            except Exception as generic_exception:
                LOGGER.error(f"Generic exception for param {repr(param)}.", exc_info=generic_exception)
            finally:
                if self._program:
                    self._program.stop()
                if self._driver:
                    self._driver.delete_created_resources()


def default_input_spec_set():
    return [
        InputSpec("build", ["vcpus", "memory"], [(0, 10), (0, 1000)]),
        InputSpec("resize", ["vcpus", "memory"], [(0, 10), (0, 1000)]),
        InputSpec("pause", [], [], ["paused"]),
        InputSpec("unpause", [], []),
        InputSpec("shelve", [], []),
        InputSpec("unshelve", [], []),
        InputSpec("delete", [], [], ['deleted']),
        InputSpec("reset", [], []),
        InputSpec("suspend", [], []),
        InputSpec("resume", [], []),
        InputSpec("rebuild", [], []),
        InputSpec("confirm", [], []),
        InputSpec("revert", [], []),
        InputSpec("reboot", [], []),
        InputSpec("start", [], []),
        InputSpec("shutoff", [], [])
    ]


class WorkloadContainer(object):
    def __init__(self, workload):
        self.workload = workload


def get_default_interceptors():
    interceptors = [
        experiment.interceptor_compute(),
        experiment.interceptor_conductor(),
        experiment.interceptor_scheduler()
    ]
    return interceptors


def run_workload(size, destination_file):
    interceptors = get_default_interceptors()
    program_driver = driver.example_osdriver()

    logging.info(f"Workload generation # {size}")
    rw = RandomWorkload(default_input_spec_set(), program_driver, interceptors)
    try:
        rw.run(size)
    except Exception as ex:
        logging.error(str(ex), exc_info=ex)
    finally:
        visited = [x for x in rw.workload if x.visited]
        logging.info(f"Visited inputs # {len(visited)}")
        ineffective = [x for x in rw.workload if not x.number_of_messages() == 0]
        logging.warning(f"Ineffective inputs # {len(ineffective)}")
        effective = [x for x in rw.workload if x.number_of_messages() > 0]
        logging.info(f"Effective inputs # {len(effective)}")
        for inp in effective:
            logging.info(f"I={repr(inp)}")
        if len(effective) > 0:
            with open(destination_file, 'wb') as writer:
                workload_container = WorkloadContainer(effective)
                pickle.dump(workload_container, writer)


class OptionsContainer(object):
    def __init__(self, options):
        self.options = options


def run_options(source_file, destination_file):
    with open(source_file, 'rb') as reader:
        workload_container = pickle.load(reader)
    if workload_container:
        random_options = RandomOptions()
        options = random_options.create_options(workload_container.workload)
        options_container = OptionsContainer(options)
        with open(destination_file, 'wb') as writer:
            pickle.dump(options_container, writer)


def run_faultload(workload_file, options_file):
    with open(workload_file, 'rb') as workload_reader, open(options_file, 'rb') as options_reader:
        workload_container = pickle.load(workload_reader)
        options_container = pickle.load(options_reader)
    if workload_container and options_container:
        rf = RandomFaultload(get_default_interceptors())
        rf.run(workload_container.workload, options_container.options)


if __name__ == "__main__":
    handlers = [
        logging.FileHandler("orandom.log", mode='a'),
        logging.StreamHandler()
    ]

    parser = argparse.ArgumentParser()
    parser.add_argument("--log-to", type=str, required=False, default=None)
    subparsers = parser.add_subparsers()

    workload = subparsers.add_parser("workload")
    workload.add_argument("size", type=int)
    workload.add_argument("destination_file", type=str)
    workload.set_defaults(func=lambda args: run_workload(args.size, args.destination_file))

    options = subparsers.add_parser("options")
    options.add_argument("source_file", type=str)
    options.add_argument("destination_file", type=str)
    options.set_defaults(func=lambda args: run_options(args.source_file, args.destination_file))

    faultload = subparsers.add_parser("faultload")
    faultload.add_argument("workload_file", type=str)
    faultload.add_argument("options_file")
    faultload.set_defaults(func=lambda args: run_faultload(args.workload_file, args.options_file))

    args = parser.parse_args()

    if args.log_to:
        handlers.append(logging.FileHandler(args.log_to, mode='a'))

    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO, handlers=handlers)

    args.func(args)
