from shooter.model import TestSummary, TestCase
import yaml
from munch import munchify
from openhurricane.manager import ComputeTestManager
from openhurricane.inspection import TestInspector
import logging
import argparse
from openspy.openstack_proxy import OpenStackRestProxy, IdentityFaker
from openspy.rabbit_proxy import RabbitProxy, RabbitFaker
import sys
import time

logging.basicConfig(format='%(asctime)s %(levelname)-5s [%(name)s] %(message)s', level=logging.DEBUG, stream=sys.stdout)

LOG = logging.getLogger("Experiments")


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


def compute_inspection_func(args):
    experiment_compute_inspection(
        args.test_summary,
        args.test_case,
        args.test_conf,
        args.destination
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

    args = parser.parse_args()
    start_time = time.time()
    args.func(args)
    elapsed = time.time() - start_time
    LOG.debug(f"TOTAL TIME {elapsed}")


if __name__ == "__main__":
    parse_arguments()