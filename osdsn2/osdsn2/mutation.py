from osdsn2 import constants
from hypothesis import strategies
import logging

LOGGER = logging.getLogger(__name__)


class MutationSelect(object):
    def __init__(self, param):
        self._param = param
        self._mutations = []
        self._mutations_names = []
        self._mutation_index = -1

        self.build_mutations()

    def build_mutations(self):
        if self._param.data_type:
            if self._param.data_type == constants.DTYPE_DICT:
                self._mutations += [
                    lambda _: None
                ]
                self._mutations_names += [
                    'DICT_NONE'
                ]
            elif self._param.data_type == constants.DTYPE_LIST:
                aux = [
                    lambda _: None,
                    lambda _: []
                ]
                aux += [lambda value: value[:1]]
                aux += [lambda value: value[1:]]
                aux += [lambda value: value[:1] + value[1:]]
                self._mutations += aux
                self._mutations_names += [
                    'LIST_NONE',
                    'LIST_EMPTY',
                    'LIST_FIRST_ELEMENT',
                    'LIST_REMOVE_THE_FIRST',
                    'LIST_COPY_ONE_ELEMENT'
                ]
            elif self._param.data_type == constants.DTYPE_STRING:
                nonprintablefunc = lambda _: strategies.text(strategies.characters(max_codepoint=1000,
                                                                    whitelist_categories=('Cc', 'Cs')),
                                              min_size=1)\
                                          .map(lambda s: s.strip()).filter(lambda s: len(s) > 0).example()
                alphafunc = lambda _: strategies.text(strategies.characters(max_codepoint=1000,
                                                                        whitelist_categories=('Nd', 'Nl', 'No', 'Lu', 'Ll', 'Lt', 'Lm', 'Lo')),
                                                  min_size=1)\
                                    .map(lambda s: s.strip()).filter(lambda s: len(s) > 0).example()
                self._mutations += [
                    lambda _: None,
                    lambda _: '',
                    nonprintablefunc,
                    lambda value: value + nonprintablefunc(value),
                    alphafunc,
                    lambda _:strategies.text(min_size=1000, max_size=2000).example(),
                    lambda _:strategies.text(max_size=2000).example()
                ]
                self._mutations_names += [
                    'STRING_NONE',
                    'STRING_EMPTY',
                    'STRING_NON_PRINTABLE',
                    'STRING_VALUE_PLUS_NON_PRINTABLE',
                    'STRING_ALPHA',
                    'STRING_OVERFLOW',
                    'STRING_PRE_DEFINED'
                ]
            elif self._param.data_type == constants.DTYPE_NUMBER:
                max_int = 100000000000000000
                min_int = -max_int
                self._mutations += [
                    lambda _: None,
                    lambda _:'',
                    lambda _:-1,
                    lambda _:1,
                    lambda _: 0,
                    lambda value: value + 1,
                    lambda value: value - 1,
                    lambda _: max_int,
                    lambda _: min_int,
                    lambda _: max_int + 1,
                    lambda _: min_int - 1
                ]
                self._mutations_names += [
                    'NUMBER_NONE',
                    'NUMBER_EMPTY',
                    'NUMBER_ABSOLUTE_MINUS_ONE',
                    'NUMBER_ABSOLUTE_PLUS_ONE',
                    'NUMBER_ABSOLUTE',
                    'NUMBER_VALUE_PLUS_ONE',
                    'NUMBER_VALUE_MINUS_ONE',
                    'NUMBER_MAX',
                    'NUMBER_MIN',
                    'NUMBER_MAX_PLUS_ONE',
                    'NUMBER_MIN_MINUS_ONE'
                ]
            elif self._param.data_type == constants.DTYPE_BOOLEAN:
                self._mutations += [
                    lambda _: None,
                    lambda _: '',
                    lambda _: strategies.booleans().example()
                ]
                self._mutations_names += [
                    'BOOLEAN_NONE',
                    'BOOLEAN_EMPTY',
                    'BOOLEAN_PRE_DEFINED'
                ]
        else:
            self._mutations += []

    def has_mutations(self):
        return self._mutation_index + 1 < len(self._mutations)

    def next_mutation_value(self, value):
        self._mutation_index += 1
        if self._mutation_index < len(self._mutations):
            try:
                LOGGER.info('Got mutation "%s"', self._mutations_names[self._mutation_index])
                new_value = self._mutations[self._mutation_index](value)
                LOGGER.info('New value %s', new_value)
                return new_value
            except Exception as e:
                LOGGER.warning('Could not use the mutation: %s', str(e))
        else:
            raise IndexError()

    def get_current_mutation_name(self):
        if self._mutation_index < len(self._mutations):
            return self._mutations_names[self._mutation_index]
        else:
            return None

    def mutation_size(self):
        return len(self._mutations)

    def incr(self):
        self._mutation_index += 1

