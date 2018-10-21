from hypothesis import strategies
import random
import copy
import datetime
import re
import logging
import hashlib


class StringFaults:
    @staticmethod
    def str_null(_):
        return None

    @staticmethod
    def str_empty(_):
        return ''

    @staticmethod
    def str_predefined(_):
        return strategies.text(min_size=1000).example()

    @staticmethod
    def str_non_printable(_):
        return strategies.text(strategies.characters(max_codepoint=1000, whitelist_categories=('Cc', 'Cs')), min_size=1)\
            .map(lambda s: s.strip()).filter(lambda s: len(s) > 0).example()

    @staticmethod
    def str_add_non_printable(target):
        return target + StringFaults.str_non_printable(target)

    @staticmethod
    def str_alpha_numeric(_):
        return strategies.text(strategies.characters(max_codepoint=1000, whitelist_categories=('Nd', 'Nl', 'No', 'Lu', 'Ll', 'Lt', 'Lm', 'Lo')), min_size=1)\
            .map(lambda s: s.strip()).filter(lambda s: len(s) > 0).example()

    @staticmethod
    def str_overflow(_):
        return strategies.text(min_size=100000).example()

    @staticmethod
    def str_malicious(_):
        raise NotImplemented()

    @staticmethod
    def all():
        this = StringFaults
        return [
            this.str_null,
            this.str_empty,
            this.str_predefined,
            this.str_non_printable,
            this.str_non_printable,
            this.str_add_non_printable,
            this.str_alpha_numeric,
            this.str_alpha_numeric,
            this.str_overflow,
            this.str_malicious
        ]


class NumberFaults:
    MAX_INT = 10000000000000000000000
    MIN_INT = -10000000000000000000000

    @staticmethod
    def num_null(_):
        return None

    @staticmethod
    def num_empty(_):
        return ''

    @staticmethod
    def num_absolute_minus_one(_):
        return -1

    @staticmethod
    def num_absolute_one(_):
        return 1

    @staticmethod
    def num_absolute_zero(_):
        return 0

    @staticmethod
    def num_add_one(target):
        return int(target) + 1

    @staticmethod
    def num_subtract_one(target):
        return int(target) - 1

    @staticmethod
    def num_max(_):
        return NumberFaults.MAX_INT

    @staticmethod
    def num_min(_):
        return NumberFaults.MIN_INT

    @staticmethod
    def num_max_plus_one(target):
        return NumberFaults.num_max(target) + 1

    @staticmethod
    def num_min_minus_one(target):
        return NumberFaults.num_min(target) - 1

    @staticmethod
    def num_max_range(_):
        raise NotImplemented()

    @staticmethod
    def num_min_range(_):
        raise NotImplemented()

    @staticmethod
    def num_max_range_plus_one(_):
        raise NotImplemented()

    @staticmethod
    def num_min_range_minus_one(_):
        raise NotImplemented()

    @staticmethod
    def all():
        this = NumberFaults
        return [
            this.num_empty,
            this.num_null,
            this.num_absolute_minus_one,
            this.num_absolute_one,
            this.num_absolute_zero,
            this.num_add_one,
            this.num_subtract_one,
            this.num_max,
            this.num_min,
            this.num_max_plus_one,
            this.num_min_minus_one,
            this.num_max_range,
            this.num_min_range,
            this.num_max_range_plus_one,
            this.num_min_range_minus_one
        ]


class ListFaults:
    @staticmethod
    def list_null(_):
        return None

    @staticmethod
    def _check_list(target):
        if not target or len(target) is 0:
            raise ValueError()

    @staticmethod
    def list_remove(target):
        ListFaults._check_list(target)
        del target[random.randint(0, len(target) - 1)]
        return target

    @staticmethod
    def list_add(target):
        raise NotImplemented()

    @staticmethod
    def list_duplicate(target):
        ListFaults._check_list(target)
        position = random.randint(0, len(target) -1)
        aux = copy.deepcopy(target[position])
        target.append(aux)
        return target

    @staticmethod
    def list_remove_all_but_first(target):
        ListFaults._check_list(target)
        return target[:1]

    @staticmethod
    def list_remove_all(_):
        return []

    @staticmethod
    def all():
        this = ListFaults
        return [
            this.list_null,
            this.list_remove,
            this.list_add,
            this.list_duplicate,
            this.list_remove_all_but_first,
            this.list_remove_all
        ]


class BooleanFaults:
    @staticmethod
    def boolean_null(_):
        return None

    @staticmethod
    def boolean_empty(_):
        return ''

    @staticmethod
    def boolean_predefined(_):
        return strategies.booleans().example()

    @staticmethod
    def boolean_overflow(_):
        return StringFaults.str_overflow(_)

    @staticmethod
    def all():
        this = BooleanFaults
        return [
            this.boolean_null,
            this.boolean_empty,
            this.boolean_predefined,
            this.boolean_overflow
        ]


class DateTimeFaults:
    @staticmethod
    def date_null(_):
        return None

    @staticmethod
    def date_empty(_):
        return ''

    @staticmethod
    def date_max_range(_):
        maxd = datetime.date.max
        return f"{maxd.year}-{'%02d' % maxd.month}-{'%02d' % maxd.day}T00:00:00.00"

    @staticmethod
    def date_min_range(_):
        mind = datetime.date.min
        return f"{'%04d' % mind.year}-{'%02d' % mind.month}-{'%02d' % mind.day}T00:00:00.00"

    @staticmethod
    def date_max_range_plus_one(_):
        raise NotImplemented()

    @staticmethod
    def date_min_range_minus_one(_):
        raise NotImplemented()

    @staticmethod
    def _convert_str_to_date(target):
        return datetime.datetime.strptime(target, '%Y-%m-%dT%H:%M:%S.%f')

    @staticmethod
    def _convert_date_to_str(target):
        return target.strftime('%Y-%m-%dT%H:%M:%S.%f')

    @staticmethod
    def date_add_100(target):
        target = DateTimeFaults._convert_str_to_date(target)
        return DateTimeFaults._convert_date_to_str(target.replace(year=target.year + 100))

    @staticmethod
    def date_subtract_100(target):
        target = DateTimeFaults._convert_str_to_date(target)
        return DateTimeFaults._convert_date_to_str(target.replace(year=target.year - 100))

    @staticmethod
    def date_02_29_1984(_):
        return '1984-29-02T00:00:00.00'

    @staticmethod
    def date_04_31_1998(_):
        return '1998-31-04T00:00:00.00'

    @staticmethod
    def date_13_01_1997(_):
        return '1997-01-13T00:00:00.00'

    @staticmethod
    def date_12_00_1994(_):
        return '1994-00-12T00:00:00.00'

    @staticmethod
    def date_09_31_1992(_):
        return '1992-31-09T00:00:00.00'

    @staticmethod
    def date_08_31_1993(_):
        return '1993-31-08T00:00:00.00'

    @staticmethod
    def date_08_32_1993(_):
        return '1993-32-08T00:00:00.00'

    @staticmethod
    def date_31_12_1999(_):
        return '1999-12-31T00:00:00.00'

    @staticmethod
    def date_01_01_2000(_):
        return '2000-01-01T00:00:00.00'

    @staticmethod
    def all():
        this = DateTimeFaults
        return [
            this.date_null,
            this.date_empty,
            this.date_max_range,
            this.date_min_range,
            this.date_max_range_plus_one,
            this.date_min_range_minus_one,
            this.date_add_100,
            this.date_subtract_100,
            this.date_02_29_1984,
            this.date_04_31_1998,
            this.date_13_01_1997,
            this.date_12_00_1994,
            this.date_08_32_1993,
            this.date_08_31_1993,
            this.date_31_12_1999,
            this.date_01_01_2000
        ]


class FaultMapper:
    LOG = logging.getLogger("FaultMapper")

    BOOLEAN_PATTERN = '[True|False]'
    NUMBER_PATTERN = '^\d+\.?\d*$'
    DATETIME_PATTERN = '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.?\d*Z?'

    OBJECT = 'object'
    LIST = 'list'
    NUMBER = 'number'
    STRING = 'string'
    BOOLEAN = 'boolean'
    DATETIME = 'datetime'
    NONE = 'none'
    UNKNOWN = 'unknown'

    @staticmethod
    def infer(target):
        if target:
            if isinstance(target, dict):
                return FaultMapper.OBJECT
            elif isinstance(target, list):
                return FaultMapper.LIST
            elif isinstance(target, bool):
                return FaultMapper.BOOLEAN
            elif isinstance(target, int) or isinstance(target, float):
                return FaultMapper.NUMBER
            else:
                if isinstance(target, str) and re.match(FaultMapper.DATETIME_PATTERN, target):
                    return FaultMapper.DATETIME
                elif isinstance(target, str):
                    return FaultMapper.STRING
                else:
                    return FaultMapper.UNKNOWN
        else:
            return FaultMapper.NONE

    @staticmethod
    def map(template, predefined_name=''):
        mappings = []
        FaultMapper._map(predefined_name, template, mappings)
        return mappings

    @staticmethod
    def _map(path, current, mappings):
        if not isinstance(current, dict) or hasattr(current, '__dict__'):
            FaultMapper.LOG.warn(f"{path} is neither an object nor a dict")
            FaultMapper.LOG.error(f"{path} is {type(current)}")
            return

        current_map = current if isinstance(current, dict) else current.__dict__
        if not isinstance(current_map, dict):
            FaultMapper.LOG.error(f"{path} is not an instance of dict")
            return
        attributes = current_map.keys()
        for attribute in attributes:
            actual_path = path + '.' + attribute
            if not attribute.startswith('__'):
                inferred = FaultMapper.infer(current_map[attribute])
                if inferred == FaultMapper.OBJECT:
                    FaultMapper._map(actual_path, current_map[attribute], mappings)
                elif inferred == FaultMapper.UNKNOWN:
                    FaultMapper.LOG.warn(f"UNKNOWN for {attribute} in {path}")
                elif inferred == FaultMapper.NONE:
                    FaultMapper.LOG.debug(f"NONE for {attribute} in {path}")
                else:
                    funcs = []
                    fault_type = None
                    if inferred == FaultMapper.LIST:
                        funcs = ListFaults.all()
                        fault_type = FaultMapper.LIST
                    elif inferred == FaultMapper.BOOLEAN:
                        funcs = BooleanFaults.all()
                        fault_type = FaultMapper.BOOLEAN
                    elif inferred == FaultMapper.NUMBER:
                        funcs = NumberFaults.all()
                        fault_type = FaultMapper.NUMBER
                    elif inferred == FaultMapper.DATETIME:
                        funcs = DateTimeFaults.all()
                        fault_type = FaultMapper.DATETIME
                    elif inferred == FaultMapper.STRING:
                        funcs = StringFaults.all()
                        fault_type = FaultMapper.STRING
                    for func in funcs:
                        fm = FaultMapper.FaultMapping(actual_path, func, fault_type)
                        mappings.append(fm)

    class FaultMapping:
        def __init__(self, path, func, fault_type):
            self.path = path
            self.func = func
            self.fault_type = fault_type

        def __hash__(self):
            content = f"{self.path}_{self.func.__name__}_{self.fault_type}"
            md5 = hashlib.md5()
            md5.update(bytes(content, 'utf8'))
            return int(md5.hexdigest(), 16) % 10**8

        def __repr__(self):
            return f"Path={self.path}, Func={self.func}, Type={self.fault_type}"
