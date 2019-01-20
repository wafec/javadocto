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


def get_nova_interceptors():
    URL = 'amqp://stackrabbit:supersecret@localhost:5672/'
    HOSTNAME = 'wallacec-ubuntu'
    interceptors = [
        interceptor.Interceptor(amqp_url="%s%s" % (URL, '%2F'),
                                exchange='nova', exchange_type='topic',
                                queue='conductor', routing_key='conductor'),
        interceptor.Interceptor(amqp_url="%s%s" % (URL, 'nova_cell1'),
                                exchange='nova', exchange_type='topic',
                                queue='compute.%s' % HOSTNAME, routing_key='compute.%s' % HOSTNAME),
        interceptor.Interceptor(amqp_url="%s%s" % (URL, 'nova_cell1'),
                                exchange='nova', exchange_type='topic',
                                queue='scheduler.%s' % HOSTNAME, routing_key='scheduler.%s' % HOSTNAME)
    ]
    return interceptors


def experiment_transition_target(test_case, test_summary, target_transition):
    interceptors = get_nova_interceptors()
    inputs = files.file_to_inputs(test_case, test_summary)
    default_driver = driver.example_osdriver()
    default_program = program.ProgramSelect(inputs, default_driver, interceptors, target_transition)

    try:
        LOGGER.info('Running experiment target transition ...')
        default_program.run()
        default_driver.dispose()
        captured_messages = default_program.get_captured_messages()
        params = []
        LOGGER.info('Experiment with %i captured messages', len(captured_messages))
        for i, message_number, body in captured_messages:
            oslo_params = program.OsloParams(body)
            all_oslo_params = oslo_params.get_all_params()
            params += [(i, message_number, body, p) for p in all_oslo_params]
        LOGGER.info('Got %i parameters', len(params))
        k = population.sample_size(len(params))
        for i, message_number, body, param in random.sample(params, k):
            mutation_select = mutation.MutationSelect(param)
            while mutation_select.has_mutations():
                def callback(i, new_message_number, new_body):
                    if message_number == new_message_number:
                        new_oslo_params = program.OsloParams(new_body)
                        mutation_body = new_oslo_params.get_new_body(param,
                                                                     mutation_select.next_mutation_value(
                                                                         new_oslo_params.get_args_value(param)
                                                                     ))
                        LOGGER.info('Mutation name %s', mutation_select.get_current_mutation_name())
                        return mutation_body
                default_program.add_on_captured_message_callback(on_captured_message_callback=callback)
                default_program.run_inputs()
                default_driver.dispose()
    except Exception as e:
        LOGGER.error('Could not finish the experiment: %s', str(e))
    finally:
        default_program.stop()
        default_driver.dispose()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, handlers=[
        logging.StreamHandler(),
        logging.FileHandler('osdsn2.log')
    ])

    def func_parser_a(args):
        experiment_transition_target(args.test_case, args.test_summary, args.target_transition)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_a = subparsers.add_parser('experiment_transition')
    parser_a.add_argument('test_case')
    parser_a.add_argument('test_summary')
    parser_a.add_argument('target_transition')
    parser_a.set_defaults(func=func_parser_a)

    args = parser.parse_args()
    args.func(args)

