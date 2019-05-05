import re
import logging
from osdsn2.analytics import objects
import os
import argparse
import time
import datetime
import threading
from concurrent.futures import ThreadPoolExecutor
import json

LOG_FORMAT = '%(asctime)s %(levelname).1s %(thread)6d %(message)s'
THREADS = None


class TcLog(object):
    def __init__(self, log_line, date, service):
        self.log_line = log_line
        self.date = date
        self.service = service

    def to_json(self):
        return {
            'type': 'TcLog',
            'log_lines': [x for x in self.log_line.split('\n') if x.strip()],
            'date': self.date.strftime('%b %d %H:%M:%S,%f'),
            'service': self.service
        }


class TcTraceLog(TcLog):
    def __init__(self, log_lines, date, service):
        super(TcTraceLog, self).__init__("\n".join(log_lines), date, service)
        self.log_lines = log_lines

    def to_json(self):
        result = super(TcTraceLog, self).to_json()
        result['type'] = 'TcTraceLog'
        return result


class TcServiceLog(object):
    def __init__(self, service_name):
        self.service_name = service_name
        self.logs = []

    def has_traceback(self):
        return len([x for x in self.logs if isinstance(x, TcTraceLog)])

    def to_json(self):
        return {
            self.service_name: [x.to_json() for x in self.logs],
            'traces': len([x for x in self.logs if isinstance(x, TcTraceLog)])
        }


class TcParserObject(object):
    def __init__(self, name, args, waits, target, date):
        self.name = name
        self.args = args
        self.waits = waits
        self.target = target
        self.date = date
        self._logs = {}
        self.tester_logs = []

    def add_service_logs(self, service, logs):
        if service not in self._logs:
            self._logs[service] = TcServiceLog(service)
        self._logs[service].logs += logs

    def has_service_traceback(self):
        return len([x for x in self._logs.values() if x.has_traceback()]) > 0

    def has_tester_traceback(self):
        return len([x for x in self.tester_logs if isinstance(x, TcTraceLog)]) > 0

    def to_json(self):
        logs = {}
        for k in self._logs:
            logs[k] = self._logs[k].to_json()
        return {
            'name': self.name,
            'args': self.args,
            'waits': self.waits,
            'target': self.target,
            'date': self.date.strftime('%b %d %H:%M:%S,%f'),
            'logs': logs,
            'tester': [x.to_json() for x in self.tester_logs]
        }


class TsParserObject(object):
    def __init__(self, ts_callback):
        self.test_case_objects = []
        self._ts_callback = ts_callback

    def to_json(self):
        return [x.to_json() for x in self.test_case_objects]

    def save_as_json(self, dest_file_path):
        with open(dest_file_path, 'w', encoding='iso-8859-1') as writer:
            json.dump(self.to_json(), writer, indent=4, sort_keys=False)

    def complete_ts(self):
        if self._ts_callback:
            self._ts_callback(self.test_case_objects)
        self.test_case_objects = []


class TsParserFile(object):
    def __init__(self, base):
        self.test_case_objects = []
        self._base = base

    def to_json(self):
        pass

    def save_as_json(self, _):
        pass

    def complete_ts(self):
        if self.test_case_objects:
            begin_obj = self.test_case_objects[0]
            end_obj = begin_obj if len(self.test_case_objects) == 1 else self.test_case_objects[
                len(self.test_case_objects) - 1
            ]
            sub = 'tester_common' if len([obj for obj in self.test_case_objects if obj.has_tester_traceback()]) == 0 \
                else 'tester_traceback'
            subsub = 'service_common' if len([obj for obj in self.test_case_objects if obj.has_service_traceback()]) \
                == 0 else 'service_traceback'
            path = f'{self._base}/{sub}__{subsub}'
            if not os.path.exists(path):
                os.makedirs(path)
            date_str_pattern = "%b_%d_%H_%M_%S_%f"
            file_path = f'{path}/{begin_obj.date.strftime(date_str_pattern)}' \
                f'__{end_obj.date.strftime(date_str_pattern)}.json'
            with open(file_path, 'w', encoding='iso-8859-1') as writer:
                json.dump([x.to_json() for x in self.test_case_objects], writer, indent=4, sort_keys=False)
            self.test_case_objects = []


class TestCaseWorker(object):
    LOGGER = logging.getLogger('TestCaseWorker')

    def __init__(self, executor, test_case_logs, ts_object):
        self._executor = executor
        self._ts_object = ts_object
        self._test_case_logs = test_case_logs
        self._test_case_input_begin_pattern = r'.*Run Name=(?P<name>\w+), Args=\w+\((?P<args>.*)\), ' \
                                              r'Waits=(?P<waits>.*), ' \
                                              r'.*Target=(?P<target>.*)$'
        self._test_case_input_end_pattern = r'.*Ran Name='
        self._logs_of_tc_object = []
        self._system_log_pattern = r'^(?P<date>\w+\s+\d+\s+\d+:\d+:\d+)\s.{5,20}\s(?P<service>\S+):.*$'
        self._system_traceback_begin_pattern = r'.*#033\[.{1,10}ERROR'
        self._system_traceback_end_pattern = r'.*#033\[00m$'
        self._test_date_pattern = r'^\S+\s+(?P<date>\d+-\d+-\d+\s+\d+:\d+:\d+,\d+)'
        self._total_of_services = None

    def parse_test_case_log(self):
        if THREADS > 1:
            self._executor.submit(self._parse_test_case_log)
        else:
            self._parse_test_case_log()

    def _parse_test_case_log(self):
        self.LOGGER.info(f'Executing concurrently in {threading.current_thread()}.')
        i = 0
        last_date = None
        while i < len(self._test_case_logs):
            m = re.match(self._test_case_input_begin_pattern, self._test_case_logs[i])
            m_date = re.match(self._test_date_pattern, self._test_case_logs[i])
            if m_date:
                last_date = datetime.datetime.strptime(m_date.group('date'), '%Y-%m-%d %H:%M:%S,%f')
            if m and last_date:
                date = last_date
                date = datetime.datetime(datetime.datetime.now().year, date.month, date.day, date.hour, date.minute,
                                         date.second, date.microsecond)
                tc_object = TcParserObject(
                    name=m.group('name'),
                    args=m.group('args'),
                    waits=m.group('waits'),
                    target=m.group('target'),
                    date=date
                )
                i += 1
                self._logs_of_tc_object = []
                while i < len(self._test_case_logs) and not re.match(self._test_case_input_end_pattern,
                                                                     self._test_case_logs[i]):
                    self._logs_of_tc_object.append(self._test_case_logs[i])
                    i += 1
                if self._logs_of_tc_object:
                    c = 0
                    for service in self._list_services_from_logs_of_tc_objects():
                        # self.LOGGER.info(f'Examining service {service}, {c + 1}/{self._total_of_services}.')
                        tc_object.add_service_logs(service, self._parse_logs_of_tc_object(service))
                        c += 1
                    tc_object.tester_logs = self._parse_logs_for_tester_proc()
                self._ts_object.test_case_objects.append(tc_object)
            else:
                i += 1
        self._ts_object.complete_ts()

    def _list_services_from_logs_of_tc_objects(self):
        services = []
        for i in range(0, len(self._logs_of_tc_object)):
            line = self._logs_of_tc_object[i]
            m = re.match(self._system_log_pattern, line)
            if m:
                service = m.group('service')
                if service not in services:
                    services.append(service)
        self.LOGGER.info(f'Found {len(services)} services.')
        self._total_of_services = len(services)
        return services

    def _parse_logs_of_tc_object(self, target_service):
        i = 0
        logs = []
        logs_of_tc_object_for_service = [x for x in self._logs_of_tc_object if
                                         re.match(self._system_log_pattern, x) and
                                         re.match(self._system_log_pattern, x).group('service') == target_service]
        while i < len(logs_of_tc_object_for_service):
            m = re.match(self._system_log_pattern, logs_of_tc_object_for_service[i])
            if m:
                date = datetime.datetime.strptime(m.group('date'), '%b %d %H:%M:%S')
                date = datetime.datetime(datetime.datetime.now().year,
                                         date.month, date.day, date.hour, date.minute, date.second)
                service = m.group('service')
                log_object = TcLog(logs_of_tc_object_for_service[i], date, service)
                m = re.match(self._system_traceback_begin_pattern, logs_of_tc_object_for_service[i])
                if m:
                    traceback_logs = [logs_of_tc_object_for_service[i]]
                    i += 1
                    while i < len(logs_of_tc_object_for_service) and not re.match(self._system_traceback_end_pattern,
                                                                                  logs_of_tc_object_for_service[i]):
                        traceback_logs.append(logs_of_tc_object_for_service[i])
                        i += 1
                    if i < len(logs_of_tc_object_for_service):
                        traceback_logs.append(logs_of_tc_object_for_service[i])
                        i += 1
                    log_object = TcTraceLog(traceback_logs, date, service)
                else:
                    i += 1
                logs.append(log_object)
            else:
                i += 1
        return logs

    def _parse_logs_for_tester_proc(self):
        i = 0
        logs = []
        logs_of_tc_object = [x for x in self._logs_of_tc_object if
                             not re.match(self._system_log_pattern, x)]
        while i < len(logs_of_tc_object):
            line = logs_of_tc_object[i]
            m = re.match(self._test_date_pattern, line)
            if m:
                date = datetime.datetime.strptime(m.group('date'), '%Y-%m-%d %H:%M:%S,%f')
                date = datetime.datetime(datetime.datetime.now().year, date.month, date.day, date.hour, date.minute,
                                         date.second, date.microsecond)
                log = TcLog(line, date, 'tester')
                if line.startswith('ERROR') and i + 1 < len(logs_of_tc_object) and \
                        logs_of_tc_object[i + 1].startswith('Traceback'):
                    lines = [line]
                    i += 1
                    while i < len(logs_of_tc_object) and not re.match(self._test_date_pattern,
                                                                      logs_of_tc_object[i]):
                        lines.append(logs_of_tc_object[i])
                        i += 1
                    if lines:
                        log = TcTraceLog(lines, date, 'tester')
                else:
                    i += 1
                logs.append(log)
            else:
                i += 1
        return logs


class TestCaseParser(object):
    LOGGER = logging.getLogger('TestCaseParser')

    def __init__(self, threads=1):
        self._test_case_begin_log_pattern = r'.*Running inputs'
        # self._test_case_end_log_pattern = r'.*Created resources deleted'
        self._test_case_end_log_pattern = self._test_case_begin_log_pattern
        self._test_case_logs = []
        self._ts_object = None
        self._threads = threads
        self._executor = None

    def parse(self, file_name, ts_object):
        if not ts_object:
            raise ValueError('ts_object cannot be None')
        self._ts_object = ts_object
        with open(file_name, 'r', encoding='iso-8859-1') as reader, ThreadPoolExecutor(max_workers=self._threads)\
                as self._executor:
            line = reader.readline()
            while line:
                if re.match(self._test_case_begin_log_pattern, line):
                    line = self._reading_test_case_logs(reader)
                else:
                    line = reader.readline()
        return self._ts_object

    def _reading_test_case_logs(self, reader):
        line = reader.readline()
        self._test_case_logs = []
        while line and not re.match(self._test_case_end_log_pattern, line):
            self._test_case_logs.append(line)
            line = reader.readline()
        if self._test_case_logs:
            tc_worker = TestCaseWorker(self._executor, self._test_case_logs, self._ts_object)
            tc_worker.parse_test_case_log()
        return line


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
        with open(path, 'r', encoding='iso-8859-1') as s:
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
        with open(path, 'r', encoding='iso-8859-1') as s:
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
    parser.add_argument('--parser', type=str, default='traceback', choices=[
        'traceback', 'full'
    ])
    parser.add_argument('--start-from', type=str, default=None)
    parser.add_argument('--logging', type=str, default=None)
    parser.add_argument('--threads', type=int, default=1)

    args = parser.parse_args()
    path = args.path
    ext = args.ext
    THREADS = args.threads
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
        if args.parser == 'traceback':
            traceback_parser = TracebackParser()
            traceback_parser.process_file(x, start_from)
            logging.debug('%d traces gathered for %s' % (len(traceback_parser.get_traceback_objects()),
                                                         x))
        elif args.parser == 'full':
            full_parser = TestCaseParser(THREADS)
            dest = f'out/objects/{os.path.basename(x)}'
            if not os.path.exists(dest):
                os.makedirs(dest)
            result = TsParserFile(dest)
            result = full_parser.parse(x, result)
            result.save_as_json(f'{dest}/{os.path.basename(x)}.full.json')
