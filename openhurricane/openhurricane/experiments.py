from shooter.model import TestSummary, TestCase
import yaml
from munch import munchify
from openhurricane.manager import ComputeTestManager
from openhurricane.inspection import TestInspector, TestInjector, TestMapper
import logging
import argparse
from openspy.openstack_proxy import OpenStackRestProxy, IdentityFaker
from openspy.rabbit_proxy import RabbitProxy, RabbitFaker
import sys
import time
import threading
import os

LOG = logging.getLogger("Experiments")


class ExternalLogger(threading.Thread):
    def __init__(self, logger):
        threading.Thread.__init__(self)
        self.terminate = False
        self.logger = logger

    def run(self):
        with open(self.logger) as flogger:
            size = os.path.getsize(self.logger)
            flogger.seek(max(size - 10, 0))

            while not self.terminate:
                line = flogger.readline()
                if line:
                    print(line, end='')
                else:
                    time.sleep(1)

    def stop(self):
        self.terminate = True


def remove_inopportune_inputs(test_case):
    LOG.debug(f"TEST CASE SIZE BEFORE {len(test_case.inputSet)}")
    test_case.inputSet = [
        test_input for test_input in test_case.inputSet
        if any("GoodTransition" in expected.qualifiedName for expected in test_input.expectedSet)
    ]
    LOG.warn(f"TEST CASE SIZE AFTER {len(test_case.inputSet)}")
    return test_case


def experiment_compute_inspection(test_summary, test_case, conf, destination):
    test_summary = TestSummary.from_file(test_summary)
    test_case = TestCase.from_file(test_case)
    test_case = remove_inopportune_inputs(test_case)
    with open(conf, 'r') as stream:
        conf = munchify(yaml.load(stream))
    compute_manager = None
    test_inspector = None
    try:
        test_inspector = TestInspector(conf)
        test_inspector.start_services()
        compute_manager = ComputeTestManager(test_case, conf, test_summary.states)
        test_inspector.inspect(compute_manager, destination)
    finally:
        if compute_manager:
            compute_manager.test_driver.clear()
        if test_inspector:
            test_inspector.stop_services()


def experiment_compute_injection(test_summary, test_case, conf, test_operation, injections, fault_types, fault_values=None, ignore=None, start=None, end=None):
    test_summary = TestSummary.from_file(test_summary)
    test_case = TestCase.from_file(test_case)
    test_case = remove_inopportune_inputs(test_case)
    with open(conf, 'r') as stream:
        conf = munchify(yaml.load(stream))
    compute_manager = None
    test_injector = None
    try:
        test_injector = TestInjector(conf)
        test_injector.start_services()
        compute_manager = ComputeTestManager(test_case, conf, test_summary.states)
        test_injector.inject(compute_manager, test_operation, injections, fault_types, fault_values, ignore, start, end)
    finally:
        if compute_manager:
            try:
                compute_manager.test_driver.clear()
            except Exception as exception:
                print(exception)
        if test_injector:
            try:
                test_injector.stop_services()
            except Exception as exception:
                print(exception)


def experiment_compute_mapping(test_summary, test_case, conf, test_slot_spec, only_path, test_type):
    test_summary = TestSummary.from_file(test_summary)
    test_case = TestCase.from_file(test_case)
    test_case = remove_inopportune_inputs(test_case)
    with open(conf, 'r') as stream:
        conf = munchify(yaml.load(stream))
    compute_manager = None
    test_mapper = None
    try:
        test_mapper = TestMapper(conf)
        test_mapper.start_services()
        compute_manager = ComputeTestManager(test_case, conf, test_summary.states)
        fault_model = test_mapper.map(compute_manager, test_slot_spec)
        fault_set = set()
        for fault_item in fault_model:
            if fault_item.fault_type not in test_type:
                continue
            if not only_path:
                fault_set.add(repr(fault_item))
            else:
                fault_set.add(fault_item.path)
        for fault_item in fault_set:
            print(fault_item)
    finally:
        if compute_manager:
            compute_manager.test_driver.clear()
        if test_mapper:
            test_mapper.stop_services()


def compute_inspection_func(args):
    experiment_compute_inspection(
        args.test_summary,
        args.test_case,
        args.test_conf,
        args.destination
    )


def compute_injection_func(args):
    experiment_compute_injection(
        args.test_summary,
        args.test_case,
        args.test_conf,
        args.test_operation,
        int(args.injections),
        args.type,
        args.fault,
        args.ignore,
        args.start,
        args.end
    )


def compute_mapping_func(args):
    experiment_compute_mapping(
        args.test_summary,
        args.test_case,
        args.test_conf,
        args.test_slot_spec,
        args.only_path,
        args.type
    )


def compute_restore_func(args):
    with open(args.test_conf) as stream:
        conf = munchify(yaml.load(stream))
    identity_faker = IdentityFaker(conf)
    openstack_proxy = OpenStackRestProxy(conf)
    rabbit_faker = RabbitFaker(conf)
    rabbit_proxy = RabbitProxy(conf)

    rabbit_proxy.stop()
    rabbit_faker.restore_bindings()
    identity_faker.restore_urls()
    openstack_proxy.stop()


def parse_arguments():
    parser = argparse.ArgumentParser(prog="Hurricane Experiments")

    parser.add_argument("--debug", default=False, action="store_true")
    parser.add_argument("--logger", default=False, nargs="*", type=str)

    subparser = parser.add_subparsers()

    compute_parser = subparser.add_parser("compute")
    compute_subparser = compute_parser.add_subparsers()

    compute_inspection_parser = compute_subparser.add_parser("inspection")
    compute_inspection_parser.add_argument("test_summary")
    compute_inspection_parser.add_argument("test_case")
    compute_inspection_parser.add_argument("test_conf")
    compute_inspection_parser.add_argument("destination")
    compute_inspection_parser.set_defaults(func=compute_inspection_func)

    compute_restore_parser = compute_subparser.add_parser("restore")
    compute_restore_parser.add_argument("test_conf")
    compute_restore_parser.set_defaults(func=compute_restore_func)

    compute_injection_parser = compute_subparser.add_parser("injection")
    compute_injection_parser.add_argument("test_summary")
    compute_injection_parser.add_argument("test_case")
    compute_injection_parser.add_argument("test_conf")
    compute_injection_parser.add_argument("test_operation")
    compute_injection_parser.add_argument("--injections", default=1)
    compute_injection_parser.add_argument("--type", nargs="*", default=None)
    compute_injection_parser.add_argument("--fault", nargs="*", default=None)
    compute_injection_parser.add_argument("--ignore", type=str, default=None, required=False)
    compute_injection_parser.add_argument("--start", type=int, default=None, required=False)
    compute_injection_parser.add_argument("--end", type=int, default=None, required=False)
    compute_injection_parser.set_defaults(func=compute_injection_func)

    compute_mapping_parser = compute_subparser.add_parser("mapping")
    compute_mapping_parser.add_argument("test_summary")
    compute_mapping_parser.add_argument("test_case")
    compute_mapping_parser.add_argument("test_conf")
    compute_mapping_parser.add_argument("test_slot_spec")
    compute_mapping_parser.add_argument("--type", default=None, type=str, nargs="*")
    compute_mapping_parser.add_argument("--only-path", default=False, action='store_true')
    compute_mapping_parser.set_defaults(func=compute_mapping_func)

    args = parser.parse_args()

    logging_level = logging.INFO

    if args.debug:
        logging_level = logging.DEBUG

    logging.basicConfig(format='%(asctime)s %(levelname)-5s [%(name)s] %(message)s', level=logging_level,
                        stream=sys.stdout)

    external_loggers = []

    if args.logger:
        for logger in args.logger:
            external_logger = ExternalLogger(logger)
            external_loggers.append(external_logger)
            external_logger.start()

    start_time = time.time()
    args.func(args)
    elapsed = time.time() - start_time
    LOG.info(f"TOTAL TIME {elapsed}")

    for external_logger in external_loggers:
        external_logger.stop()

if __name__ == "__main__":
    parse_arguments()