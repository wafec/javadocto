

class TracebackNode(object):
    def __init__(self, prev, file_name, line, place, code):
        self.prev = prev
        self.file_name = file_name
        self.line = line
        self.place = place
        self.code = code
        self.next = None

    def get_last(self):
        last_candidate = self
        while last_candidate.next is not None:
            last_candidate = last_candidate.next
        return last_candidate

    def size(self):
        counter = 0
        candidate = self
        while candidate:
            counter += 1
            candidate = candidate.next
        return counter

    def extract(self, f):
        extraction_list = []
        candidate = self
        while candidate:
            extraction_list.append(f(candidate))
            candidate = candidate.next
        return extraction_list

    def _to_text(self, candidate):
        return '%s, %s, %s\n    %s' % (candidate.file_name, candidate.line, candidate.place, candidate.code)

    def to_text(self):
        return '\n'.join(self.extract(self._to_text))

    @staticmethod
    def _from_text(r, prev):
        first_line = r.readline()
        second_line = r.readline()
        if first_line and second_line:
            parts = first_line.split(',')
            file_name = parts[0]
            line = parts[1]
            place = parts[2]
            code = second_line[4:]
            node = TracebackNode(prev, file_name, line, place, code)
            node.next = TracebackNode._from_text(r, node)
            return node
        else:
            return None

    @staticmethod
    def from_text(r):
        return TracebackNode._from_text(r, None)


class TracebackObject(object):
    def __init__(self, logger, traceback_time, method_name, chain, param_type, mutation_name,
                 test_case, test_summary, target_transition, wait_timeout, wait_timeout_time):
        self._root_node = None
        self.logger = logger
        self.traceback_time = traceback_time
        self.method_name = method_name
        self.chain = chain
        self.param_type = param_type
        self.mutation_name = mutation_name
        self.test_case = test_case
        self.test_summary = test_summary
        self.target_transition = target_transition
        self.wait_timeout = wait_timeout
        self._name_suggestion = None
        self.wait_timeout_time = wait_timeout_time

    def get_depth(self):
        return self._root_node.size()

    def do_extraction(self, f):
        return self._root_node.extract(f)

    def add_traceback_node_data(self, file_name, line, place, code):
        node = TracebackNode(None, file_name, line, place, code)
        if self._root_node is None:
            self._root_node = node
        else:
            last = self._root_node.get_last()
            last.next = node
            node.prev = last

    def parse_traceback_time_for_file_name(self):
        return self.traceback_time.replace(' ', '').replace(':', '').lower()

    def parse_for_file_name(self):
        return self.target_transition + '_' + \
               self.parse_traceback_time_for_file_name() + '_' + self.logger.replace('[', '').replace(']', '') \
               + '_' + self._root_node.get_last().place + self._root_node.get_last().line

    def suggest_name(self, name):
        self._name_suggestion = name

    def to_text(self, path):
        if not path and self._name_suggestion:
            path = self._name_suggestion
        elif not path:
            raise ValueError('Path cannot be None')

        with open(path, 'w') as w:
            w.write(self.traceback_time + '\n')
            w.write(self.logger + '\n')
            w.write(self.method_name + '\n')
            w.write(self.chain + '\n')
            w.write(self.param_type + '\n')
            w.write(self.mutation_name + '\n')
            w.write(self.test_case + '\n')
            w.write(self.test_summary + '\n')
            w.write(self.target_transition + '\n')
            w.write('True' if self.wait_timeout else 'False')
            if self.wait_timeout:
                w.write(' ' + self.wait_timeout_time)
            w.write('\n')
            w.write(self._root_node.to_text())

    def from_text(self, path):
        with open(path, 'r') as r:
            self.traceback_time = r.readline()
            self.logger = r.readline()
            self.method_name = r.readline()
            self.chain = r.readline()
            self.param_type = r.readline()
            self.mutation_name = r.readline()
            self.test_case = r.readline()
            self.test_summary = r.readline()
            self.target_transition = r.readline()
            wait_timeout_line = r.readline()
            self.wait_timeout = False if wait_timeout_line.startswith('False') else True
            if self.wait_timeout:
                self.wait_timeout_time = wait_timeout_line[len('True') + 1:]
            self._root_node = TracebackNode.from_text(r)
