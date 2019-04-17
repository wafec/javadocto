

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


class TracebackObject(object):
    def __init__(self, logger, traceback_time):
        self._root_node = None
        self.logger = logger
        self.traceback_time = traceback_time

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
