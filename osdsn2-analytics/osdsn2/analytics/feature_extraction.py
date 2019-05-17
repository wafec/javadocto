import re
import os
import bisect
import json
import numpy as np
from suffix_trees import STree


class TraceFile(object):
    _main_pattern = r'\S(?P<b>\s+File)\s"(?P<file_path>.*)",\s(line)\s(?P<file_line_number>\d+),' \
                    r'\s(in)\s(?P<function_name>[\w_]+)'
    _raise_pattern = r'raise\s\w'

    def __init__(self, log_line, subsequent_log_line):
        self.file_path = None
        self.file_line_number = None
        self.function_name = None
        self.function_line_code = None
        self.start = None
        self._load(log_line, subsequent_log_line)

    def _load(self, log_line, subsequent_log_line):
        m = re.search(TraceFile._main_pattern, log_line)
        if not m:
            raise ValueError('main_pattern is not matching log_line')
        self.file_path = m.group('file_path')
        self.file_line_number = int(m.group('file_line_number'))
        self.function_name = m.group('function_name')
        self.start = m.start('b')
        self.function_line_code = subsequent_log_line[self.start:].lstrip()

    def __str__(self):
        return '{}, {}, {}'.format(self.file_path_simple_qualified, self.file_line_number, self.function_name)

    @property
    def file_path_basename(self):
        return os.path.basename(self.file_path)

    @property
    def file_path_dirname(self):
        return os.path.basename(os.path.dirname(self.file_path))

    @property
    def file_path_simple_qualified(self):
        return '.../' + self.file_path_dirname + '/' + self.file_path_basename

    def has_raise_expression(self):
        return re.search(TraceFile._raise_pattern, self.function_line_code)

    @staticmethod
    def is_trace_file(log_line):
        return re.search(TraceFile._main_pattern, log_line)

    def are_completely_equal(self, other):
        return self.file_path_simple_qualified == other.file_path_simple_qualified and\
               self.file_line_number == other.file_line_number and\
               self.function_name == other.function_name and\
               self.function_line_code == other.function_line_code

    @property
    def value(self):
        return "".join([self.file_path_simple_qualified, str(self.file_line_number), self.function_name])


class MyList(object):
    def __init__(self, sequence):
        self.sequence = sequence

    def __instancecheck__(self, instance):
        print('instancecheck')
        pass

    def __subclasscheck__(self, subclass):
        print('subclasscheck')
        pass


class StackTraceGraph(object):
    def __init__(self, trace_files, error_message):
        self.trace_files = trace_files
        self.error_message = error_message

    def number_of_hooks(self, other):
        for i in range(0, min(len(self.trace_files), len(other.trace_files))):
            if not self.trace_files[i].are_completely_equal(other.trace_files[i]):
                return i
        return min(len(self.trace_files), len(other.trace_files))

    def intersections(self, other):
        search_list = sorted(other.trace_files, key=lambda trace_file: trace_file.value)
        keys = [trace_file.value for trace_file in search_list]
        intersection = []
        for trace_file in self.trace_files:
            i = bisect.bisect_left(keys, trace_file.value)
            if i != len(keys) and keys[i] == trace_file.value:
                intersection.append(search_list[i])
        # Repeated items on self might to appear more than once
        # This leads to different amounts, so the inverse of comparisons can not be equal
        return intersection

    def number_of_intersections(self, other):
        return len(self.intersections(other))

    def generalized_suffix_tree(self, other):
        seq_a = [trace_file.value for trace_file in self.trace_files]
        seq_b = [trace_file.value for trace_file in other.trace_files]
        st = STree.STree([MyList(seq_a), MyList(seq_b)])
        return st.lcs()

    @staticmethod
    def build(log_lines):
        stack_trace_graphs = []
        trace_files = []
        index = 0
        while index < len(log_lines):
            if TraceFile.is_trace_file(log_lines[index]) and index + 1 < len(log_lines):
                trace_file = TraceFile(log_lines[index], log_lines[index + 1])
                index += 2
                trace_files.append(trace_file)
                if trace_file.has_raise_expression():
                    error_message = None
                    if index < len(log_lines):
                        error_message = log_lines[index][trace_file.start:].lstrip()
                        index += 1
                    stack_trace_graph = StackTraceGraph(trace_files, error_message)
                    stack_trace_graphs.append(stack_trace_graph)
                    trace_files = []
            else:
                index += 1
        return stack_trace_graphs


class StackTraceVectorizer(object):
    def __init__(self, stack_trace_graphs):
        self.stack_trace_graphs = stack_trace_graphs

    def get_stacks(self):
        stacks = [stack for stack in self.stack_trace_graphs]
        i = 0
        while i < len(stacks):
            j = i + 1
            while j < len(stacks):
                if stacks[i].number_of_hooks(stacks[j]) == len(stacks[i].trace_files):
                    del stacks[j]
                else:
                    j += 1
            i += 1
        return stacks

    def generate_array_by_stacks(self):
        stacks = self.get_stacks()
        array = np.arange(len(self.stack_trace_graphs) * len(stacks)).reshape(len(self.stack_trace_graphs), len(stacks))
        for i in range(0, len(self.stack_trace_graphs)):
            for j in range(0, len(stacks)):
                array[i, j] = self.stack_trace_graphs[i].generalized_suffix_tree(stacks[j])
        return array

    def transform(self):
        array = self.generate_array_by_stacks()
        return array


def get_graph(file_path, process_name):
    with open(file_path, 'r', encoding='iso-8859-1') as r:
        data = json.load(r)
        return StackTraceGraph.build(data[process_name])


graph1 = get_graph('out/tests/traceback_1.json', 'nova-conductor')
graph2 = get_graph('out/tests/traceback_2.json', 'nova-compute')
graph3 = get_graph('out/tests/traceback_3.json', 'nova-compute')

graphs = []
graphs += graph1
graphs += graph2
graphs += graph3

vectorizer = StackTraceVectorizer(graphs)
array = vectorizer.transform()
print(array)