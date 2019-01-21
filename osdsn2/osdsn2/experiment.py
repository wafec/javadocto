from osdsn2 import program
from osdsn2 import interceptor
from osdsn2 import driver
from osdsn2 import files
from osdsn2 import population
from osdsn2 import mutation

import logging
import argparse
import random

LOGGER = logging.getLogger(__name__)
LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -15s %(funcName) -20s '
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


class ExperimentTransitionTarget(object):
    def __init__(self, test_case, test_summary, target_transition, ignore_injection):
        self._test_case = test_case
        self._test_summary = test_summary
        self._target_transition = target_transition
        self._ignore_injection = ignore_injection

        self._param_in_the_loop = None
        self._mutation_select_in_the_loop = None
        self._message_number_in_the_loop = None
        self._mutation_select_used = None

    def on_captured_message_callback(self, input_running, message_number, body):
        LOGGER.info('Running captured message callback')
        new_oslo_params = program.OsloParams(body)
        method_name = new_oslo_params.get_method_name()
        LOGGER.info('Param Method=%s, Message method=%s', self._param_in_the_loop.method_name, method_name)
        LOGGER.info('Msg ITL=%i, Message number=%i', self._message_number_in_the_loop, message_number)
        if self._param_in_the_loop.method_name == method_name:
            LOGGER.info('Methods match')
            if self._message_number_in_the_loop <= message_number and self._mutation_select_used is False:
                LOGGER.info('Message numbers match')
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
                    LOGGER.info('Mutation used. Skipping')
        return None

    def run(self, interceptors, default_driver):
        default_program = program.ProgramSelect(
            files.file_to_inputs(self._test_case, self._test_summary),
            default_driver,
            interceptors,
            self._target_transition
        )

        try:
            LOGGER.info('Running experiment target transition ...')
            default_program.run()
            default_driver.delete_created_resources()
            captured_messages = default_program.get_captured_messages()
            params = []
            LOGGER.info('Experiment with %i captured messages', len(captured_messages))
            for i, message_number, body in captured_messages:
                oslo_params = program.OsloParams(body)
                all_oslo_params = oslo_params.get_all_params()
                params += [(i, message_number, body, p) for p in all_oslo_params]
                LOGGER.info('Method=%s, Message number=%i ()', oslo_params.get_method_name(), message_number)
            LOGGER.info('Got %i parameters', len(params))
            if not self._ignore_injection:
                default_driver.set_max_waiting_use(default_driver.get_max_waiting() + 20)
                k = population.sample_size(len(params))
                for i, message_number, body, param in random.sample(params, k):
                    self._param_in_the_loop = param
                    self._message_number_in_the_loop = message_number
                    self._mutation_select_in_the_loop = mutation.MutationSelect(param)
                    while self._mutation_select_in_the_loop.has_mutations():
                        default_program.add_on_captured_message_callback(self.on_captured_message_callback)
                        self._mutation_select_used = False
                        try:
                            default_program.run_inputs()
                        except TimeoutError as time_error:
                            LOGGER.error(time_error, exc_info=True)
                        default_driver.delete_created_resources()
                        if self._mutation_select_used is False:
                            self._mutation_select_in_the_loop.incr()
                            LOGGER.warning('Mutation %s skipped',
                                           self._mutation_select_in_the_loop.get_current_mutation_name())
            else:
                LOGGER.warning('Error injection skipped by the user')
        except KeyboardInterrupt:
            LOGGER.info('Stopped by the user')
        except Exception as e:
            LOGGER.error(e, exc_info=True)
        finally:
            default_program.stop()
            default_driver.delete_created_resources()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, handlers=[
        logging.StreamHandler(),
        logging.FileHandler('osdsn2.log', mode='w')
    ])

    def func_parser_a(args):
        ExperimentTransitionTarget(args.test_case, args.test_summary, args.target_transition, args.ignore_injection)\
            .run([
                    interceptor_compute(), interceptor_conductor(), interceptor_scheduler()
                 ], driver.example_osdriver())

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_a = subparsers.add_parser('experiment_transition')
    parser_a.add_argument('--ignore-injection', action='store_true')
    parser_a.add_argument('test_case')
    parser_a.add_argument('test_summary')
    parser_a.add_argument('target_transition')
    parser_a.set_defaults(func=func_parser_a)

    args = parser.parse_args()
    args.func(args)

