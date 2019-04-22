import re
import logging
from osdsn2.analytics import objects
import os
import argparse
import time

LOG_FORMAT = '%(asctime)s %(levelname).1s %(message)s'


class TracebackParser(object):
    LOG = logging.getLogger('TracebackParser')

    def __init__(self):
        self._trace_pattern = r'^.*File (?P<file_name>".+"), line (?P<line>\d+), in (?P<place>[\w_\d]+)'
        self._traceback_pattern = r'^.*(Traceback)'
        self._logger_pattern = r'^(?P<time>\w+\s*\d+\s+\d+:\d+:\d+)\s+' \
                               r'[\w\-_\d]+\s+(?P<logger>[\w\-_\d]+\[\d+\]):'
        self._test_case_pattern = r'.*Test Case=(?P<test_case>.*), Test Summary=(?P<test_summary>.*), Target ' \
                                  r'Transition=(?P<target_transition>.*)$'
        self._got_mutation_pattern = r'.*Got mutation "(?P<mutation_name>[\w\s_]+)"'
        self._method_and_params_pattern = r'.*Getting args value for Method=(?P<method_name>.*), Chain=(?P<chain>.*),' \
                                          r' Type=(?P<param_type>.*)$'
        self._starting_pattern = r'.*Running inputs$'
        self._wait_timeout_pattern = r'^.*(?P<wait_timeout_time>\d{4}-\d+-\d+\s+\d+:\d+:\d+,\d+)' \
                                     r'\s.*Wait timeout.*elapsed'
        self._traceback_objects = None
        self._loggers = None
        self._start_from = None

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
        self.LOG.debug('Loggers search complete. %d found.' % len(self._loggers))
        if self._start_from:
            index = self._loggers.index(self._start_from);
            if index:
                self.LOG.debug('%s found at %d' % (self._start_from, index))
                self._loggers = self._loggers[index:]

    def process_file(self, path, start_from):
        self._start_from = start_from
        self._traceback_objects = []
        self._find_loggers(path)
        self.LOG.debug('Start processing.')
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
        default_unknown = 'unknown'
        method_name = default_unknown
        chain = default_unknown
        param_type = default_unknown
        mutation_name = default_unknown
        test_case = default_unknown
        target_transition = default_unknown
        test_summary = default_unknown
        wait_timeout = False
        wait_timeout_time = None
        traceback_objects_buffer = []
        with open(path, 'r', encoding='utf8') as s:
            line = s.readline()
            while line:
                try:
                    m = re.match(self._starting_pattern, line)
                    if m:
                        # TODO: elaborate a method to ensure that some names won't be None
                        wait_timeout = False
                        wait_timeout_time = None
                        for x in traceback_objects_buffer:
                            x.to_text(None)
                        traceback_objects_buffer.clear()
                        pass
                    m = re.match(self._test_case_pattern, line)
                    if m:
                        test_case = m.group('test_case')
                        test_summary = m.group('test_summary')
                        target_transition = m.group('target_transition')
                    m = re.match(self._wait_timeout_pattern, line)
                    if m:
                        wait_timeout = True
                        wait_timeout_time = m.group('wait_timeout_time')
                        for x in traceback_objects_buffer:
                            x.wait_timeout = wait_timeout
                            x.wait_timeout_time = wait_timeout_time
                    m = re.match(self._method_and_params_pattern, line)
                    if m:
                        method_name = m.group('method_name')
                        chain = m.group('chain')
                        param_type = m.group('param_type')
                    m = re.match(self._got_mutation_pattern, line)
                    if m:
                        mutation_name = m.group('mutation_name')
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
                                traceback_line += '\n' + line
                                traceback_object = self._parse_traceback_line(traceback_line.replace('\n\n', '\n'),
                                                                              logger, traceback_time,
                                                                              method_name, chain, param_type, mutation_name,
                                                                              test_case, test_summary, target_transition,
                                                                              wait_timeout, wait_timeout_time)
                                traceback_objects_buffer.append(traceback_object)
                                traceback_line = None
                            elif not is_next_file_line:
                                is_next_file_line = True
                                traceback_line += '\n' + line[traceback_position:]
                except Exception as exc:
                    self.LOG.error(exc)
                finally:
                    line = s.readline()
        if traceback_objects_buffer:
            for x in traceback_objects_buffer:
                x.to_text(None)
        traceback_objects_buffer.clear()

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

    def _parse_traceback_line(self, line, logger, traceback_time, method_name, chain, param_type, mutation_name,
                              test_case, test_summary, target_transition, wait_timeout, wait_timeout_time):
        if re.match(r".*\[u?'Traceback", line):
            line = self._traceback_array_to_line(line)
        lines_of_line = [x.strip() for x in line.split('\n') if x.strip()]
        traceback_object = objects.TracebackObject(logger, traceback_time, method_name, chain, param_type,
                                                   mutation_name, test_case, test_summary, target_transition,
                                                   wait_timeout, wait_timeout_time)
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
        traceback_object.suggest_name('out/objects/' + traceback_object.parse_for_file_name() +
                                      '.txt')
        return traceback_object


def ensure_that_out_dir_exists():
    if not os.path.exists('out'):
        os.mkdir('out')


def ensure_that_objects_dir_exists():
    ensure_that_out_dir_exists()
    if not os.path.exists('out/objects'):
        os.mkdir('out/objects')


if __name__ == '__main__':
    logging_handlers = [
        logging.StreamHandler(),
        logging.FileHandler('default.log', 'a')
    ]

    ensure_that_objects_dir_exists()

    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('ext')
    parser.add_argument('--start-from', type=str, default=None)
    parser.add_argument('--logging', type=str, default=None)

    args = parser.parse_args()
    path = args.path
    ext = args.ext
    start_from = args.start_from
    logging_file = args.logging

    if logging_file:
        logging_handlers.append(logging.FileHandler(logging_file, 'w'))

    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, handlers=logging_handlers)

    paths = []
    if os.path.isdir(path):
        logging.debug('Path %s is a dir' % path)
        paths = [path + '/' + x for x in os.listdir(path) if os.path.isfile(path + '/' + x) and (x == 'any' or
                                                                                                 x.endswith(ext))
                 and not x.endswith('.tmp')]
        logging.debug('Found %d files' % len(paths))
    else:
        if ext != 'any' and not path.endswith(ext):
            raise ValueError('path does not end with ext')
        paths.append(path)

    for x in paths:
        logging.debug('Processing path %s' % x)
        traceback_parser = TracebackParser()
        traceback_parser.process_file(x, start_from)
        logging.debug('%d traces gathered for %s' % (len(traceback_parser.get_traceback_objects()),
                                                     x))
