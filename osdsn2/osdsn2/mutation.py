from osdsn2 import constants
from hypothesis import strategies


class DataMutationOperator(object):
    def __init__(self, param, value):
        self._param = param
        self._value = value

    def get_mutation_list(self):
        if self._param.data_type:
            if self._param.data_type == constants.DTYPE_DICT:
                return [
                    None
                ]
            elif self._param.data_type == constants.DTYPE_LIST:
                aux = [
                    None,
                    []
                ]
                if len(self._value) > 1:
                    aux += [self._value[:1]]
                    aux += [self._value[1:]]
                    aux += [self._value[:1] + self._value[1:]]
                return aux
            elif self._param.data_type == constants.DTYPE_STRING:
                nprint = strategies.text(strategies.characters(max_codepoint=1000,
                                                               whitelist_categories=('Cc', 'Cs')),
                                         min_size=1)\
                                    .map(lambda s: s.strip()).filter(lambda s: len(s) > 0).example()
                alpha = strategies.text(strategies.characters(max_codepoint=1000,
                                                              whitelist_categories=('Nd', 'Nl', 'No', 'Lu', 'Ll', 'Lt', 'Lm', 'Lo')),
                                        min_size=1)\
                                    .map(lambda s: s.strip()).filter(lambda s: len(s) > 0).example()
                return [
                    None,
                    '',
                    nprint,
                    self._value + nprint,
                    alpha,
                    strategies.text(min_size=2500).example(),
                    strategies.text().example()
                ]
            elif self._param.data_type == constants.DTYPE_NUMBER:
                max_int = 100000000000000000
                min_int = -max_int
                return [
                    None,
                    '',
                    -1,
                    1,
                    0,
                    self._value + 1,
                    self._value - 1,
                    max_int,
                    min_int,
                    max_int + 1,
                    min_int - 1
                ]
            elif self._param.data_type == constants.DTYPE_BOOLEAN:
                return [
                    None,
                    '',
                    strategies.booleans().example()
                ]
        else:
            return []
