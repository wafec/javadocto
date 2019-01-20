from ruamel.yaml import YAML
import pathlib
from osdsn2 import input


def file_to_inputs(test_file, summary_file):
    test = YAML().load(pathlib.Path(test_file))
    summary = YAML().load(pathlib.Path(summary_file))
    test_inputs = []
    for inp in test['inputSet']:
        name = inp['qualifiedName'].split('.')
        name = name[len(name) - 1]
        name = name.lower()
        args = {}
        sources = []
        destinations = []
        transitions = []
        for exp in inp['expectedSet']:
            if exp['qualifiedName'].endswith('.GoodTransitionResult'):
                source = exp['extras']['source']
                destination = exp['extras']['destination']
                transition = exp['extras']['transition']
                if 'states' in summary:
                    if source in summary['states']:
                        source = summary['states'][source]
                    if destination in summary['states']:
                        destination = summary['states'][destination]
                if 'transitions' in summary:
                    if transition in summary['transitions']:
                        transition = summary['transitions'][transition]
                sources.append(source)
                destinations.append(destination)
                transitions.append(transition)
        if 'args' in inp:
            args = inp['args']
        if len(destinations) > 0:
            test_inputs.append(input.Input(name, args, destinations, transitions))
    return test_inputs
