import yaml
from shooter import model
from openhurricane.manager import ComputeTestManager
from munch import munchify
import logging

#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')


def test_basic_test():
    summary = model.TestSummary.from_file("./tests/test-summary-Omari.yaml")
    test_case = model.TestCase.from_file("./tests/test-case-Warren.yaml")
    with open("./tests/CONF.example.yaml") as istream:
        conf = yaml.load(istream)
        conf = munchify(conf)
    manager = ComputeTestManager(test_case, conf, summary.states)
    manager.run_tests()