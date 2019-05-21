import os
import bisect
import json
import numpy as np
import string
from sklearn.feature_extraction.text import TfidfVectorizer
import shutil
import re
import stringdist
from osdsn2.analytics.utils import UnorderedProgress
import sys
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

    def longest_common_subsequence_size(self, other):
        uniques = list(set([x.value for x in self.trace_files] + [x.value for x in other.trace_files]))
        uniques = sorted(uniques)
        mine = "".join([chr(ord('a') + bisect.bisect_left(uniques, x.value)) for x in self.trace_files])
        theirs = "".join([chr(ord('a') + bisect.bisect_left(uniques, x.value)) for x in other.trace_files])
        st = STree.STree([mine, theirs])
        common = st.lcs()
        return len(common)

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
    BY_STACK = 0x001
    BY_MESSAGE = 0x002
    WITH_TFIDF = 0x010
    WITH_LEVENSHTEIN = 0x020
    _WITH_MASK_MESSAGE = 0x0F0
    WITH_INTERSECTIONS = 0x100
    WITH_LCS = 0x200
    _WITH_MASK_STACK = 0xF00

    def __init__(self, stack_trace_graphs):
        self.stack_trace_graphs = stack_trace_graphs
        self.flags = None

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

    @staticmethod
    def _normalize(a):
        amin = np.amin(a)
        amax = np.amax(a)
        for i in range(a.shape[0]):
            for j in range(a.shape[1]):
                norm_value = (a[i, j] - amin) / float(amax)
                if a[i, j] != 0:
                    a[i, j] = norm_value
        return a

    @staticmethod
    def _apply_scale(a, scale):
        amin = np.amin(a)
        for i in range(a.shape[0]):
            for j in range(a.shape[1]):
                scale_value = (a[i, j] - amin) * scale
                if a[i, j] != 0:
                    a[i, j] = scale_value

    @staticmethod
    def _scale(a, b):
        amin = np.amin(a)
        bmin = np.amin(b)
        amax = np.amax(a)
        bmax = np.amax(b)
        scale = (amax - amin) / float((bmax - bmin))
        StackTraceVectorizer._apply_scale(b, scale)

    def _print_mask_by_stack_description(self):
        msg = ''
        if self.flags & self._WITH_MASK_STACK == self.WITH_INTERSECTIONS:
            msg = 'With intersections'
        elif self.flags & self._WITH_MASK_STACK == self.WITH_LCS:
            msg = 'With lcs'
        print(msg)

    def generate_array_by_stacks(self):
        print('Array by stacks')
        self._print_mask_by_stack_description()
        stacks = self.get_stacks()
        array = np.arange(len(self.stack_trace_graphs) * len(stacks), dtype=np.float).reshape(len(self.stack_trace_graphs), len(stacks))
        for i in range(0, len(self.stack_trace_graphs)):
            for j in range(0, len(stacks)):
                if self.flags & self._WITH_MASK_STACK == self.WITH_INTERSECTIONS:
                    array[i, j] = self.stack_trace_graphs[i].number_of_intersections(stacks[j])
                elif self.flags & self._WITH_MASK_STACK == self.WITH_LCS:
                    array[i, j] = self.stack_trace_graphs[i].longest_common_subsequence_size(stacks[j])
        return array

    def _messages_preprocessor(self, text):
        text = re.sub(r"[{}]".format(string.punctuation), " ", text.lower())
        return text

    def _generate_array_by_messages_using_tidif(self):
        print('TFIDF init')
        tfidf_vectorizer = TfidfVectorizer(preprocessor=self._messages_preprocessor)
        tfidf = tfidf_vectorizer.fit_transform([stack.error_message for stack in self.stack_trace_graphs])
        print('TFIDF end')
        return tfidf

    def _generate_array_by_messages_using_levenshtein(self):
        dimension = len(self.stack_trace_graphs)
        array = np.arange(dimension * dimension, dtype=np.float).reshape(dimension, dimension)
        pg = UnorderedProgress(0, dimension * dimension)
        print('Levenshtein init')
        for i in range(dimension):
            for j in range(i + 1, dimension):
                distance = stringdist.levenshtein(self.stack_trace_graphs[i].error_message, self.stack_trace_graphs[j].error_message)
                array[i, j] = distance
                array[j, i] = distance
                pg.incr(2)
                sys.stdout.write('\r' + str(pg))
        print('Levenshtein end')
        return array

    def generate_array_by_messages(self):
        print('Array by messages')
        if self.flags & StackTraceVectorizer._WITH_MASK_MESSAGE == StackTraceVectorizer.WITH_TFIDF:
            return self._generate_array_by_messages_using_tidif()
        if self.flags & StackTraceVectorizer._WITH_MASK_MESSAGE == StackTraceVectorizer.WITH_LEVENSHTEIN:
            return self._generate_array_by_messages_using_levenshtein()
        return None

    @staticmethod
    def _concatenate(a, b):
        if a is not None and b is None:
            return a
        if b is not None and a is None:
            return b
        StackTraceVectorizer._scale(a, b)
        rows = a.shape[0]
        cols = a.shape[1] + b.shape[1]
        final = np.arange(rows * cols, dtype=np.float).reshape(rows, cols)
        for i in range(0, rows):
            for j in range(0, cols):
                if j < a.shape[1]:
                    final[i, j] = a[i, j]
                else:
                    final[i, j] = b[i, j - a.shape[1]]
        return final

    def transform(self, flags):
        result = None
        self.flags = flags
        if flags & StackTraceVectorizer.BY_STACK:
            by_stacks = self.generate_array_by_stacks()
            result = StackTraceVectorizer._concatenate(result, by_stacks)
        if flags & StackTraceVectorizer.BY_MESSAGE:
            by_messages = self.generate_array_by_messages()
            result = StackTraceVectorizer._concatenate(result, by_messages)
        return StackTraceVectorizer._normalize(result)


class StackTraceGraphHelper(object):
    @staticmethod
    def _get_graph(file_path, process_name):
        with open(file_path, 'r', encoding='iso-8859-1') as r:
            data = json.load(r)
            if process_name in data:
                return StackTraceGraph.build(data[process_name])
        return []

    @staticmethod
    def get_graph(file_path, process_name):
        results = []
        pn_parsed = [x.strip() for x in process_name.split(' ')]
        for pn in pn_parsed:
            results += StackTraceGraphHelper._get_graph(file_path, pn)
        return results

    @staticmethod
    def map_graphs(file_path, graphs):
        return [(file_path, graph) for graph in graphs]

    @staticmethod
    def get_graphs_from_map(graphs_map):
        return [graph[1] for graph in graphs_map]

    @staticmethod
    def get_graphs_map(file_path, process_name):
        graphs = StackTraceGraphHelper.get_graph(file_path, process_name)
        return StackTraceGraphHelper.map_graphs(file_path, graphs)

    @staticmethod
    def copy_files_based_on_labels(graphs_map, labels, destination):
        for file_path, label in zip([graph[0] for graph in graphs_map], [str(x) for x in labels]):
            if not os.path.exists(os.path.join(destination, label)):
                os.makedirs(os.path.join(destination, label))
            destination_path = os.path.join(os.path.join(destination, label), os.path.basename(file_path))
            shutil.copy(file_path, destination_path)


class AbstractHelper(object):
    @staticmethod
    def load(file_path):
        with open(file_path, 'r', encoding='iso-8859-1') as r:
            data = json.load(r)
            return data

    @staticmethod
    def list_processes(raw):
        processes_names = []
        for file_path in [os.path.join(raw, file_path) for file_path in os.listdir(raw)]:
            data = AbstractHelper.load(file_path)
            for process_name in data.keys():
                processes_names.append(process_name)
        return list(set(processes_names))

    @staticmethod
    def print_processes_names(raw):
        for process_name in AbstractHelper.list_processes(raw):
            print(process_name)

    @staticmethod
    def print_processes_names_t(raw):
        d = AbstractHelper.list_processes_t(raw)
        for process_name_key in d.keys():
            value = d[process_name_key]
            print(process_name_key, value[0])

    @staticmethod
    def list_processes_t(raw):
        processes_names = {}
        for file_path in [os.path.join(raw, file_path) for file_path in os.listdir(raw) if
                          os.path.isfile(os.path.join(raw, file_path))]:
            data = AbstractHelper.load(file_path)
            for input in data:
                for log_key in input['logs']:
                    m = re.search(r'(?P<name>^[@\w\-\._]+)(\[\d+\])?$', log_key)
                    if m:
                        if m.group('name') not in processes_names:
                            processes_names[m.group('name')] = [0, 0]
                        processes_names[m.group('name')][0] = processes_names[m.group('name')][0] + \
                                                              input['logs'][log_key]['traces']
        return processes_names


if __name__ == '__main__':
    graph1 = StackTraceGraphHelper.get_graph('out/tests/short/traceback_1.json', 'nova-conductor')
    graph2 = StackTraceGraphHelper.get_graph('out/tests/short/traceback_2.json', 'nova-compute')
    graph3 = StackTraceGraphHelper.get_graph('out/tests/short/traceback_3.json', 'nova-compute')

    graphs = []
    graphs += graph1
    graphs += graph2
    graphs += graph3

    vectorizer = StackTraceVectorizer(graphs)
    array = vectorizer.transform(int(sys.argv[1], 16))
    print(array)
