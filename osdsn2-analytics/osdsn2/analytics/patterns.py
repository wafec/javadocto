import re


DATE_PATTERNS = [
    r'(?P<del>\w+\s+\d+\s+\d+:\d+:\d+)\s',
    r'(?P<del>\d+-\d+-\d+\s+\d+:\d+:\d+(,\d+)?)',
    r'(?P<del>\s+\d+-\d+\s+\d+:\d+:\d+\s?)',
    r'(?P<del>\d+-\d+-\d+T\d+:\d+:\d+Z)',
    r'(?P<del>\d{2,4}-\d{2}-\d{2})'
]

PROC_PATTERNS = [
    r'([\w\.@-]+(?P<del>\[\d+\])[:\s]?\s)',
    r'(?P<del>\(pid=\d+\))',
    r'pid[:=]\s*(?P<del>\d+)',
    r'tap(?P<del>[\w\d]{4,15}-[\w\d]{1,5})',
    r'kernel:\s+\[(?P<del>\d+(\.\d+)?)\]'
]

REQUEST_PATTERNS = [
    r'req(?P<del>[\w\d-]+)\s',
    r'(?P<del>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
    r'req:\s+(?P<del>\d+/?\d+)',
    r'(?P<del>([\w\d]{2}:){5,8})',
    r'(?P<del>([\w\d]{4}::?){4,6})'
]

ID_PATTERNS = [
    r'\w=(?P<del>\'?([\w\d-]{4,8}){6}\'?)',
    r'\'(?P<del>([\w\d-]{4,8}){6})\'',
    r'(?P<del>([\w\d]{4,8}-){5,6})'
]

NOISE_PATTERNS = [
    r'(?P<del>#\d{3}\[\d{0,2};?\d{0,2}m?)'
]


def _use_pattern_list_internal(pattern_list, lines):
    matches = []
    for i in range(0, len(pattern_list)):
        for j in range(0, len(lines)):
            pattern = pattern_list[i]
            line = lines[j]
            m = re.match(pattern, line)
            if m:
                matches.append((m, line))
    return matches


def _transform_to_list(obj):
    if not isinstance(obj, list):
        return [obj]
    return obj


def use_pattern(pattern, line):
    pattern_list = _transform_to_list(pattern)
    lines = _transform_to_list(line)
    _use_pattern_list_internal(pattern_list, lines)