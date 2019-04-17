import re
import logging
from osdsn2.analytics import objects

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -15s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')


class TracebackParser(object):
    LOG = logging.getLogger('TracebackParser')

    def __init__(self):
        self._trace_pattern = r'^.*File (?P<file_name>".+"), line (?P<line>\d+), in (?P<place>[\w_\d]+)'
        self._traceback_pattern = r'^.*(Traceback)'
        self._logger_pattern = r'^(?P<time>\w+\s*\d+\s+\d+:\d+:\d+)\s+[\w\-_\d]+\s+(?P<logger>[\w\-_\d]+\[\d+\]):'
        self._traceback_objects = None
        self._loggers = None

    def get_traceback_objects(self):
        return self._traceback_objects

    def _find_loggers(self, path):
        self._loggers = []
        self.LOG.debug('Looking loggers.')
        with open(path, 'r', encoding='utf8') as s:
            line = s.readline()
            while line:
                m = re.match(self._logger_pattern, line)
                if m:
                    if m.group('logger') not in self._loggers:
                        self._loggers.append(m.group('logger'))
                        self.LOG.debug('Logger %s added.' % (m.group('logger')))
                line = s.readline()
        self.LOG.debug('Loggers search complete.')

    def process_file(self, path):
        self._traceback_objects = []
        self._find_loggers(path)
        self.LOG.debug('Starting processing.')
        if len(self._loggers) > 0:
            for logger in self._loggers:
                self._process_file(path, logger)

    def _process_file(self, path, logger):
        self.LOG.debug('Processing for logger %s' % logger)
        found_traceback = False
        is_next_file_line = False
        traceback_line = None
        traceback_position = 0
        traceback_time = None
        with open(path, 'r', encoding='utf8') as s:
            line = s.readline()
            while line:
                m = re.match(self._logger_pattern, line)
                if m and m.group('logger') == logger:
                    if not found_traceback and re.match(self._traceback_pattern, line):
                        found_traceback = True
                        is_next_file_line = True
                        traceback_line = line
                        traceback_position = re.match(self._traceback_pattern, line).start(1)
                        traceback_time = m.group('time')
                    elif found_traceback:
                        if is_next_file_line and re.match(self._trace_pattern, line):
                            is_next_file_line = False
                            traceback_line += '\n' + line
                        elif is_next_file_line:
                            found_traceback = False
                            self._parse_traceback_line(traceback_line.replace('\n\n', '\n'), logger, traceback_time)
                            traceback_line = None
                        elif not is_next_file_line:
                            is_next_file_line = True
                            traceback_line += '\n' + line[traceback_position:]
                line = s.readline()

    def _traceback_array_to_line(self, line):
        index_of = line.index("'Traceback")
        brackets_counter = 1
        content = ''
        while brackets_counter > 0 and index_of < len(line):
            char_at = line[index_of]
            content += char_at
            if char_at == '[':
                brackets_counter += 1
            elif char_at == ']':
                brackets_counter -= 1
            index_of += 1
        return "".join(eval('[' + content))

    def _parse_traceback_line(self, line, logger, traceback_time):
        if re.match(r".*\[u?'Traceback", line):
            line = self._traceback_array_to_line(line)
        lines_of_line = [x.strip() for x in line.split('\n') if x.strip()]
        traceback_object = objects.TracebackObject(logger, traceback_time)
        for i in range(1, len(lines_of_line), 2):
            if i + 1 >= len(lines_of_line):
                continue
            line_of_line = lines_of_line[i]
            code_of_line = lines_of_line[i+1]
            m = re.match(self._trace_pattern, line_of_line)
            if m:
                file_name = m.group('file_name')
                trace_line = m.group('line')
                place = m.group('place')
                code = code_of_line
                traceback_object.add_traceback_node_data(file_name, trace_line, place, code)
            else:
                self.LOG.warning('Problem with line segment "%s"' % line_of_line)
        self._traceback_objects.append(traceback_object)
        self.LOG.debug('At %s for %s then %d depth' % (traceback_object.traceback_time, traceback_object.logger,
                                              traceback_object.get_depth()))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, handlers=[
        logging.StreamHandler(),
        logging.FileHandler('default.log', 'w')
    ])
    traceback_parser = TracebackParser()
    traceback_parser.process_file('resources/log_example.log')
    logging.debug('%d traces gathered' % (len(traceback_parser.get_traceback_objects())))
