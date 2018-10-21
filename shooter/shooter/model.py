import yaml
from munch import munchify


class TestCase(yaml.YAMLObject):
    yaml_tag = u'!testcase'

    def __init__(self, fictitiousName, inputSet, metadata):
        self.fictitiousName = fictitiousName
        self.metadata = metadata
        self.inputSet = inputSet

    @staticmethod
    def from_file(file_path):
        with open(file_path) as istream:
            instance = yaml.load(istream)
            instance._munchify()
            return instance

    def _munchify(self):
        self.metadata = munchify(self.metadata)
        for inputData in self.inputSet:
            inputData._munchify()


class TestInput(yaml.YAMLObject):
    yaml_tag = u'!input'

    def __init__(self, qualifiedName, args, expectedSet):
        self.qualifiedName = qualifiedName
        self.args = args
        self.expectedSet = expectedSet

    def _munchify(self):
        for expected in self.expectedSet:
            expected._munchify()


class TestExpected(yaml.YAMLObject):
    yaml_tag = u'!expected'

    def __init__(self, qualifiedName, index, extras):
        self.qualifiedName = qualifiedName
        self.index = index
        self.extras = extras

    def _munchify(self):
        self.extras = munchify(self.extras)


class TestSummary(yaml.YAMLObject):
    yaml_tag = u'!testSummary'

    def __init__(self, fictitiousName, generatedTestCases, states, statesIdentifier,
        transitions, transitionsIdentifier):
        self.fictitiousName = fictitiousName
        self.generatedTestCases = generatedTestCases
        self.states = states
        self.statesIdentifier = statesIdentifier
        self.transitions = transitions
        self.transitionsIdentifier = transitionsIdentifier

    @staticmethod
    def from_file(file_path):
        with open(file_path) as istream:
            instance = yaml.load(istream)
            instance._munchify()
            return instance

    def _munchify(self):
        self.states = munchify(self.states)
        self.transitions = munchify(self.transitions)