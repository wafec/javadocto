from osdsn2 import program
from osdsn2 import interceptor
from osdsn2 import driver
from osdsn2 import files
from osdsn2 import population
from osdsn2 import mutation
from osdsn2 import input

import logging
from logging.handlers import RotatingFileHandler
import argparse
import random
import signal
import os
import time
from ruamel.yaml import YAML
import pathlib
import threading
import psutil

LOGGER = logging.getLogger(__name__)
LOG_FORMAT = ('%(levelname) -8s %(asctime)s %(name) -25s %(funcName) -20s '
              '%(lineno) -3d: %(message)s')

AMQP_URL = 'amqp://stackrabbit:supersecret@localhost:5672/'
HOSTNAME = 'wallacec-ubuntu'


def interceptor_conductor():
    return interceptor.Interceptor(amqp_url="%s%s" % (AMQP_URL, '%2F'),
                                   exchange='nova', exchange_type='topic',
                                   queue='conductor', routing_key='conductor')


def interceptor_compute():
    return interceptor.Interceptor(amqp_url="%s%s" % (AMQP_URL, 'nova_cell1'),
                                   exchange='nova', exchange_type='topic',
                                   queue='compute.%s' % HOSTNAME, routing_key='compute.%s' % HOSTNAME)


def interceptor_scheduler():
    return interceptor.Interceptor(amqp_url="%s%s" % (AMQP_URL, 'nova_cell1'),
                                   exchange='nova', exchange_type='topic',
                                   queue='scheduler.%s' % HOSTNAME, routing_key='scheduler.%s' % HOSTNAME)


def raw_inputs_to_prepared_inputs(raw_inputs):
    for raw_input in raw_inputs:
        waits = raw_input.waits
        raw_input.waits = []
        for wait in waits:
            if wait == 'RESIZED':
                raw_input.waits.append('verify_resize')
            elif wait == 'RUNNING':
                raw_input.waits.append('active')
            elif wait == 'STOPPED':
                raw_input.waits.append('shutoff')
            elif wait == 'SHELVED':
                raw_input.waits.append('shelved_offloaded')
            else:
                raw_input.waits.append(wait)
    return raw_inputs


class PCHealthMonitor(object):
    MONITORING_INTERVAL = 20

    def __init__(self):
        self._stopped = False

    def run(self):
        while self._stopped is False:
            time.sleep(self.MONITORING_INTERVAL)
            LOGGER.info('CPU=%s, MEM=%s, SWAP=%s',
                        psutil.cpu_percent(), psutil.virtual_memory().percent, psutil.swap_memory().percent)

    def start(self):
        threading.Thread(target=self.run).start()

    def stop(self):
        self._stopped = True


class ExperimentTransitionTarget(object):
    ERROR_MARGIN = 1

    def __init__(self, test_case, test_summary, target_transition, ignore_errors, parent_pid):
        self._test_case = test_case
        self._test_summary = test_summary
        self._target_transition = target_transition
        self._ignore_errors = ignore_errors
        self._parent_pid = parent_pid

        self._param_in_the_loop = None
        self._mutation_select_in_the_loop = None
        self._message_number_in_the_loop = None
        self._mutation_select_used = None
        self._interceptors = None

        self._default_driver = None
        self._default_program = None
        self._max_waiting_time = None
        self._captured_messages = None
        self._params = None
        self._selected_params = None

        LOGGER.info('Test Case=%s, Test Summary=%s, Target Transition=%s', test_case, test_summary, target_transition)

    def on_captured_message_callback(self, unused_input, message_number, body):
        LOGGER.info('Running captured message callback')
        new_oslo_params = program.OsloParams(body)
        method_name = new_oslo_params.get_method_name()
        LOGGER.info('Param Method=%s, Message method=%s', self._param_in_the_loop.method_name, method_name)
        LOGGER.info('Msg ITL=%i, Message number=%i', self._message_number_in_the_loop, message_number)
        if self._param_in_the_loop.method_name == method_name:
            LOGGER.info('Methods match')
            if self._message_number_in_the_loop - self.ERROR_MARGIN <= message_number \
                    and self._mutation_select_used is False:
                LOGGER.info('Message numbers match %i +- %i', message_number, self.ERROR_MARGIN)
                mutation_body = new_oslo_params.get_new_body(self._param_in_the_loop,
                                                             self._mutation_select_in_the_loop.next_mutation_value(
                                                                 new_oslo_params.get_args_value(self._param_in_the_loop)
                                                             ))
                self._mutation_select_used = True
                return mutation_body
            else:
                if self._mutation_select_used is False:
                    LOGGER.warning('Message numbers do not match')
                else:
                    LOGGER.info('Mutation used (Single). Skipping')
        return None

    def instantiate_driver_and_program(self):
        self._default_driver = driver.example_osdriver()
        self._default_program = program.ProgramSelect(
            raw_inputs_to_prepared_inputs(files.file_to_inputs(self._test_case, self._test_summary)),
            self._default_driver,
            self._interceptors,
            self._target_transition
        )

    def run_error_free_round(self):
        LOGGER.info('Running error-free round ...')
        self.notify_parent_process(signal.SIGUSR1, delay=60)

        self.instantiate_driver_and_program()
        try:
            self._default_program.run()
            self._max_waiting_time = self._default_driver.get_max_waiting()
        finally:
            self._default_driver.delete_created_resources()
            self._default_program.stop()

    def collect_params_after_error_free_round(self):
        self._captured_messages = self._default_program.get_captured_messages()
        params = []
        LOGGER.info('Experiment with %i captured messages', len(self._captured_messages))
        for i, message_number, body in self._captured_messages:
            oslo_params = program.OsloParams(body)
            all_oslo_params = oslo_params.get_all_params()
            params += [(i, message_number, body, p) for p in all_oslo_params]
            LOGGER.info('Method=%s, Message number=%i ()', oslo_params.get_method_name(), message_number)
        LOGGER.info('Got %i parameters', len(params))
        self._params = params

    def run(self, interceptors, skip_auto_mapping=False, end_callback=None):
        self._interceptors = interceptors
        default_program = None
        default_driver = None

        try:
            if skip_auto_mapping is False:
                self.run_error_free_round()
                self.collect_params_after_error_free_round()
                self.auto_set_selected_params()
            self.run_error_injection_round()
            if end_callback:
                end_callback(self)
            self.notify_parent_process(signal.SIGUSR2)
        except KeyboardInterrupt:
            LOGGER.info('Stopped by the user')
        except Exception as e:
            LOGGER.error(e, exc_info=True)
            self.notify_parent_process(signal.SIGINT)
        finally:
            if default_program:
                default_program.stop()
            if default_driver:
                default_driver.delete_created_resources()

    def run_error_injection_round(self):
        if not self._ignore_errors:
            LOGGER.info('Running error injection round ...')
            lc = 1
            for i, message_number, body, param in self._selected_params:
                LOGGER.info('Param %i of %i', lc, len(self._selected_params))
                lc += 1
                self.notify_parent_process(signal.SIGUSR1, delay=60)

                self.instantiate_driver_and_program()
                self._default_driver.set_max_waiting_use(self._max_waiting_time + 15)
                try:
                    self._default_program.prep_run()
                    self._param_in_the_loop = param
                    self._message_number_in_the_loop = message_number
                    self._mutation_select_in_the_loop = mutation.MutationSelect(param)
                    while self._mutation_select_in_the_loop.has_mutations():
                        self._default_program.add_on_captured_message_callback(self.on_captured_message_callback)
                        self._mutation_select_used = False
                        try:
                            self._default_program.run_inputs()
                        except TimeoutError as time_error:
                            LOGGER.error(time_error, exc_info=True)
                        self._default_driver.delete_created_resources()
                        if self._mutation_select_used is False:
                            self._mutation_select_in_the_loop.incr()
                            LOGGER.warning('Mutation %s skipped',
                                           self._mutation_select_in_the_loop.get_current_mutation_name())
                finally:
                    self._default_driver.delete_created_resources()
                    self._default_program.stop()
        else:
            LOGGER.warning('Error injection skipped by the user')

    def auto_set_selected_params(self):
        # It makes necessary because of we are not injecting into Oslo params
        filtered_params = [(i, m, b, p) for i, m, b, p in self._params if '.' not in p.chain[len(p.chain) - 1]]
        LOGGER.warning('There were filtered out %i param(s) from %i', len(self._params) - len(filtered_params),
                       len(self._params))
        LOGGER.info('Working with %i params on sampling', len(filtered_params))
        k = population.sample_size(len(filtered_params))

        self._selected_params = random.sample(filtered_params, k)
        LOGGER.info('Sample Size=%i', k)
        self.dump_selected_params()

    def dump_selected_params(self):
        for input_running, message_number, _, param in self._selected_params:
            LOGGER.info('I=%r, M=%i, P=%r', input_running, message_number, param)

    def notify_parent_process(self, signal_code, delay=10):
        if self._parent_pid is None:
            return
        LOGGER.info('%r sent to %i', signal_code, self._parent_pid)
        start_time = time.time()
        os.kill(self._parent_pid, signal_code)
        while start_time + delay > time.time():
            time.sleep(1)

    def set_selected_params(self, selected_params):
        self._selected_params = selected_params
        LOGGER.info('Set %i selected param(s)', len(selected_params))
        self.dump_selected_params()

    def set_max_waiting_time(self, max_waiting_time):
        self._max_waiting_time = max_waiting_time
        LOGGER.info('Set max waiting time to %i', max_waiting_time)

    def get_selected_params(self):
        return self._selected_params

    def get_params(self):
        return self._params

    def get_max_waiting_time(self):
        return self._max_waiting_time


def save_sampled_params_to_file(filename, max_waiting_time, params, selected_params):
    with open(filename, 'w') as writer:
        main = {
            'max_waiting_time': max_waiting_time,
            'len_params': len(params),
            'len_selected_params': len(selected_params)
        }
        entries = []
        for i, m, b, p in selected_params:
            di = {
                'name': i.name,
                'args': i.args,
                'waits': i.waits,
                'state_trans': i.state_trans
            }
            dp = {
                'method_name': p.method_name,
                'chain': p.chain,
                'data_type': p.data_type
            }
            entries.append({
                'input': di,
                'message_number': m,
                'body': b,
                'param': dp
            })
        main['selected_params'] = entries
        yaml = YAML()
        yaml.dump(main, writer)
        LOGGER.info('Sampled params saved to file "%s"', filename)


def load_sampled_params_from_file(filename):
    yaml = YAML()
    data = yaml.load(pathlib.Path(filename))
    entries = []
    for entry in data['selected_params']:
        i = input.Input(
            name=entry['input']['name'],
            args=entry['input']['args'],
            waits=entry['input']['waits'],
            state_trans=entry['input']['state_trans']
        )
        m = entry['message_number']
        b = entry['body']
        p = program.Param(
            method_name=entry['param']['method_name'],
            chain=entry['param']['chain'],
            data_type=entry['param']['data_type']
        )
        entries.append((i, m, b, p))
    return data['max_waiting_time'], entries


if __name__ == '__main__':
    LOGGER.info('Experiment PID=%i', os.getpid())

    def func_parser_brute_force(args):
        ExperimentTransitionTarget(args.test_case, args.test_summary, args.target_transition, args.ignore_errors,
                                   args.parent_pid)\
            .run([
                    interceptor_compute(), interceptor_conductor(), interceptor_scheduler()
                 ])

    def func_parser_error_free(args):
        x = ExperimentTransitionTarget(args.test_case, args.test_summary, args.target_transition, True, args.parent_pid)
        x.run([
            interceptor_compute(), interceptor_conductor(), interceptor_scheduler()
        ], end_callback=lambda _: save_sampled_params_to_file(args.outfile, x.get_max_waiting_time(), x.get_params(),
                                                              x.get_selected_params()))


    def func_parser_with_errors(args):
        x = ExperimentTransitionTarget(args.test_case, args.test_summary, args.target_transition, False, args.parent_pid)
        max_waiting_time, selected_params = load_sampled_params_from_file(args.infile)
        x.set_max_waiting_time(max_waiting_time)
        index_from = args.index_from if args.index_from else 0
        index_to = args.index_to if args.index_to else len(selected_params)
        x.set_selected_params(selected_params[index_from:index_to])
        x.run([
            interceptor_compute(), interceptor_conductor(), interceptor_scheduler()
        ], skip_auto_mapping=True)

    parser = argparse.ArgumentParser()

    parser.add_argument('--log-file', type=str, required=False, default=None)

    subparsers = parser.add_subparsers()

    parser_a = subparsers.add_parser('brute-force')
    parser_a.add_argument('--ignore-errors', action='store_true')
    parser_a.add_argument('--parent-pid', type=int, required=False, default=None)
    parser_a.add_argument('test_case')
    parser_a.add_argument('test_summary')
    parser_a.add_argument('target_transition')
    parser_a.set_defaults(func=func_parser_brute_force)

    parser_b = subparsers.add_parser('error-free')
    parser_b.add_argument('--parent-pid', type=int, required=False, default=None)
    parser_b.add_argument('test_case')
    parser_b.add_argument('test_summary')
    parser_b.add_argument('target_transition')
    parser_b.add_argument('outfile')
    parser_b.set_defaults(func=func_parser_error_free)

    parser_c = subparsers.add_parser('with-errors')
    parser_c.add_argument('--parent-pid', type=int, required=False, default=None)
    parser_c.add_argument('--index-from', type=int, required=False, default=None)
    parser_c.add_argument('--index-to', type=int, required=False, default=None)
    parser_c.add_argument('test_case')
    parser_c.add_argument('test_summary')
    parser_c.add_argument('target_transition')
    parser_c.add_argument('infile')
    parser_c.set_defaults(func=func_parser_with_errors)

    args = parser.parse_args()

    logging_handlers = [
        logging.StreamHandler(),
        RotatingFileHandler('logs/main/osdsn2.log', mode='a', maxBytes=15000, backupCount=100)
    ]

    if args.log_file:
        logging_handlers += [logging.FileHandler(args.log_file, mode='a')]

    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, handlers=logging_handlers)

    pchealth_monitor = PCHealthMonitor()
    pchealth_monitor.start()

    args.func(args)

    pchealth_monitor.stop()

