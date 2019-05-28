import re
import datetime
from osdsn2.analytics import exception
import string
import nltk
from datasketch import MinHash
import argparse
import json
import os


CRITICAL_SERVICES = [
    'systemd',
    'kernel',
    'systemd-udevd',
    'apachectl,'
    'systemd-resolved'
]


FRONTIER_SERVICES = [
    'devstack@n-api.service'
]

TESTING_SERVICES = [
    'nova-compute',
    'nova-conductor',
    'nova-scheduler',
    'devstack@n-api.service'
]


class BaseAnalyzer(object):
    def __init__(self, test_object):
        self.test_object = test_object

    def iter_over_logs(self, consumer, stop_at_first=True):
        results = []
        for test_input in self.test_object:
            for log_process in test_input["logs"]:
                if log_process in test_input["logs"][log_process]:
                    for log in test_input["logs"][log_process][log_process]:
                        if consumer(log['log_lines'], log):
                            if stop_at_first:
                                return log
                            else:
                                results.append(log)
        if stop_at_first:
            return None
        else:
            return results

    def iter_over_tester(self, consumer, stop_at_first=True):
        results = []
        for test_input in self.test_object:
            for log in test_input['tester']:
                if consumer(log['log_lines'], log):
                    if stop_at_first:
                        return log
                    else:
                        results.append(log)
        if stop_at_first:
            return None
        else:
            return results

    def service_name(self, full_name):
        m = re.match(r'^(?P<s_name>[\w\-\._@]+)(\[\d+\])?$', full_name)
        if m:
            name = m.group('s_name')
            return name
        return full_name


class FailureAnalyzer(BaseAnalyzer):
    DTM_FORMAT = '%b %d %H:%M:%S,%f'

    def __init__(self, test_object):
        super(FailureAnalyzer, self).__init__(test_object)

    def got_mutation_at(self):
        log = super(FailureAnalyzer, self).iter_over_tester(lambda log_lines, _: [x for x in log_lines if re.search(r'Got mutation', x)], True)
        if log is None:
            raise exception.NoMutationFound()
        return log['date']

    def got_errors_at(self):
        logs = super(FailureAnalyzer, self).iter_over_logs(lambda log_lines, _: [x for x in log_lines if re.search(r'vm_state.*error', x)], False)
        if not logs:
            raise exception.NoErrorFound()
        return [x['date'] for x in logs]

    def is_faulty(self):
        try:
            mutation_date = self.got_mutation_at()
            errors_date = self.got_errors_at()
            format = FailureAnalyzer.DTM_FORMAT
            no_error = not [x for x in errors_date if datetime.datetime.strptime(x, format) >
                            datetime.datetime.strptime(mutation_date, format)]
            tester = super(FailureAnalyzer, self).iter_over_tester(lambda log_lines, log: log['type'] == 'TcTraceLog')
            return tester and no_error
        except exception.NoMutationFound:
            return False
        except exception.NoErrorFound:
            return True

    def behave_as_expected(self):
        return not super(FailureAnalyzer, self).iter_over_tester(lambda log_lines, log: log['type'] == 'TcTraceLog')

    def iter_over_logs(self, consumer, stop_at_first=True, ignore=False):
        logs = super(FailureAnalyzer, self).iter_over_logs(consumer, False)
        if ignore:
            return logs
        if logs:
            mutation_at = datetime.datetime.strptime(self.got_mutation_at(), FailureAnalyzer.DTM_FORMAT)
            logs = [x for x in logs if datetime.datetime.strptime(x['date'], FailureAnalyzer.DTM_FORMAT) > mutation_at]
            if stop_at_first and logs:
                return logs[0]
        return logs


class CatastrophicAnalyzer(FailureAnalyzer):
    def __init__(self, test_object):
        super(CatastrophicAnalyzer, self).__init__(test_object)

    def is_catastrophic(self):
        return self.iter_over_logs(lambda log_lines, log: self.service_name(log['service']) in CRITICAL_SERVICES and
                                   log['type'] == 'TcTraceLog')


class RestartAnalyzer(FailureAnalyzer):
    def __init__(self, test_object):
        super(RestartAnalyzer, self).__init__(test_object)

    def convert(self, logs):
        services = {}
        for log in logs:
            m = re.search(r'(?P<service_name>[\w\-\.@_]+)', log['service'])
            if m:
                service_name = m.group('service_name')
                pid = -1
                m = re.search(r'\[(?P<pid>\d+)\]$', log['service'])
                if m:
                    pid = int(m.group('pid'))
                if service_name not in services:
                    services[service_name] = []
                services[service_name].append(pid)
        for service_name in services:
            services[service_name] = list(set(services[service_name]))
        return services

    def is_restart(self):
        mutation_at = datetime.datetime.strptime(self.got_mutation_at(), FailureAnalyzer.DTM_FORMAT)
        later = self.iter_over_logs(lambda log_lines, log: datetime.datetime.strptime(log['date'], FailureAnalyzer.DTM_FORMAT) < mutation_at, False, True)
        after = self.iter_over_logs(lambda log_lines, log: datetime.datetime.strptime(log['date'], FailureAnalyzer.DTM_FORMAT) >= mutation_at, False, True)
        after_converted = self.convert(after)
        later_converted = self.convert(later)
        for later_service in later_converted:
            later_pids = later_converted[later_service]
            if later_service in after_converted:
                after_pids = after_converted[later_service]
                for later_pid in later_pids:
                    if later_pid not in after_pids:
                        return True
        return False


class AbortAnalyzer(FailureAnalyzer):
    def __init__(self, test_object):
        super(AbortAnalyzer, self).__init__(test_object)

    def is_abort(self):
        return self.iter_over_logs(lambda log_lines, log: log['type'] == 'TcTraceLog')


class SilentAnalyzer(FailureAnalyzer):
    def __init__(self, test_object):
        super(SilentAnalyzer, self).__init__(test_object)

    def is_silent(self):
        return not self.iter_over_logs(lambda log_lines, log: [x for x in log_lines if re.search(r'vm_state.*error', x)] and
                                       self.service_name(log['service']) in FRONTIER_SERVICES)


class HinderingAnalyzer(FailureAnalyzer):
    def __init__(self, test_object):
        super(HinderingAnalyzer, self).__init__(test_object)

    def is_hindering(self):
        results = self.iter_over_logs(lambda log_lines, log: log['type'] == 'TcTraceLog' and
                                      self.service_name(log['service']) in TESTING_SERVICES, False)
        return self.are_similar(results)

    def are_similar(self, logs):
        error_messages = []
        for log in logs:
            if len(log['log_lines']) > 2:
                m = re.search(r'#00m(?P<error_message>.*)$', log['log_lines'][len(log['log_lines']) - 2])
                if m:
                    error_message = m.group('error_message')
                    error_messages.append(error_message)
        if error_messages:
            error_messages = [re.sub('[{}]'.format(string.punctuation), x) for x in error_messages]
            for i in range(len(error_messages) - 1):
                for j in range(i + 1, len(error_messages)):
                    i_tokens = nltk.word_tokenize(error_messages[i])
                    j_tokens = nltk.word_tokenize(error_messages[j])
                    m1, m2 = MinHash(), MinHash()
                    for d in i_tokens:
                        m1.update(d)
                    for d in j_tokens:
                        m2.update(d)
                    value = m1.jaccard(m2)
                    if value < 0.5:
                        return False
        return True


class CrashEnum(object):
    def __init__(self, id, description):
        self.id = id
        self.description = description

    def __str__(self):
        return 'ID={}, Description={}'.format(self.id, self.description)

    def __repr__(self):
        return self.description


class CrashAnalyzer(BaseAnalyzer):
    IT_IS_CATASTROPHIC = CrashEnum(0, 'Catastrophic')
    IT_IS_RESTART = CrashEnum(1, 'Restart')
    IT_IS_ABORT = CrashEnum(2, 'Abort')
    IT_IS_SILENT = CrashEnum(3, 'Silent')
    IT_IS_HINDERING = CrashEnum(4, 'Hindering')
    IT_HAS_PASSED = CrashEnum(5, 'Passed')
    IT_BEHAVE_AS_EXPECTED = CrashEnum(6, 'Behave as expected')
    IT_IS_NONE = CrashEnum(7, 'Unknown')

    def __init__(self, test_object):
        super(CrashAnalyzer, self).__init__(test_object)
        self._failure_analyzer = FailureAnalyzer(test_object)
        self._catastrophic_analyzer = CatastrophicAnalyzer(test_object)
        self._restart_analyzer = RestartAnalyzer(test_object)
        self._abort_analyzer = AbortAnalyzer(test_object)
        self._silent_analyzer = SilentAnalyzer(test_object)
        self._hindering_analyzer = HinderingAnalyzer(test_object)

    def it_is(self):
        if not self._failure_analyzer.is_faulty():
            return self.IT_HAS_PASSED
        if self._failure_analyzer.behave_as_expected():
            return self.IT_BEHAVE_AS_EXPECTED
        if self._catastrophic_analyzer.is_catastrophic():
            return self.IT_IS_CATASTROPHIC
        if self._abort_analyzer.is_abort():
            if self._silent_analyzer.is_silent():
                return self.IT_IS_SILENT
            if self._hindering_analyzer.is_hindering():
                return self.IT_IS_HINDERING
            return self.IT_IS_ABORT
        if self._restart_analyzer.is_restart():
            return self.IT_IS_RESTART
        return self.IT_IS_NONE


class App(object):
    def __init__(self):
        pass

    def use_file(self, file_name):
        with open(file_name, 'r', encoding='iso-8859-1') as r:
            test_object = json.load(r)
            crash_analyzer = CrashAnalyzer(test_object)
            result = crash_analyzer.it_is()
            print('CRASH result is', repr(result))

    def use_directory(self, directory_name):
        results = {}
        for file_name in os.listdir(directory_name):
            path = os.path.join(directory_name, file_name)
            if os.path.isfile(path):
                with open(path, 'r', encoding='iso-8859-1') as r:
                    test_object = json.load(r)
                    crash_analyzer = CrashAnalyzer(test_object)
                    result = crash_analyzer.it_is()
                    if result not in results:
                        results[result] = 0
                    results[result] += 1
        for result in results:
            print('{} has {} file(s)'.format(repr(result), results[result]))


if __name__ == '__main__':
    app = App()
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()

    f = sub.add_parser('file')
    f.add_argument('file_name')
    f.set_defaults(callback=lambda opts: app.use_file(opts.file_name))

    d = sub.add_parser('directory')
    d.add_argument('directory_name')
    d.set_defaults(callback=lambda opts: app.use_directory(opts.directory_name))

    opts = parser.parse_args()
    opts.callback(opts)
