import re
import datetime
from osdsn2.analytics import exception
import string
import nltk
from datasketch import MinHash
import argparse
import json
import os
import statistics
from suffix_trees import STree


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
        logs = super(FailureAnalyzer, self).iter_over_logs(lambda log_lines, _: [x for x in log_lines if re.search(r'vm_state.{0,10}error', x)], False)
        if not logs:
            raise exception.NoErrorFound()
        return [x['date'] for x in logs]

    def is_faulty(self):
        tester = super(FailureAnalyzer, self).iter_over_tester(lambda log_lines, log: log['type'] == 'TcTraceLog')
        if not tester:
            return False
        try:
            mutation_date = self.got_mutation_at()
            errors_date = self.got_errors_at()
            format = FailureAnalyzer.DTM_FORMAT
            errors = not [x for x in errors_date if datetime.datetime.strptime(x, format) >
                          datetime.datetime.strptime(mutation_date, format)]
            return not errors
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
                                   [x for x in log_lines if 'ERROR' in x])


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
        return self.iter_over_logs(lambda log_lines, log: [x for x in log_lines if 'ERROR ' in x])


class SilentAnalyzer(FailureAnalyzer):
    def __init__(self, test_object):
        super(SilentAnalyzer, self).__init__(test_object)

    def is_silent(self):
        errors = self.iter_over_logs(lambda log_lines, log: [x for x in log_lines if 'ERROR ' in x and
                                       self.service_name(log['service']) in FRONTIER_SERVICES])
        return not errors


class HinderingAnalyzer(FailureAnalyzer):
    def __init__(self, test_object):
        super(HinderingAnalyzer, self).__init__(test_object)

    def is_hindering(self):
        results = self.iter_over_logs(lambda log_lines, log: self.service_name(log['service']) in TESTING_SERVICES and
                                      [x for x in log_lines if 'ERROR ' in x], False)
        return not self.are_similar(results)

    @staticmethod
    def get_anon_string(value):
        value = re.sub(r'([\w\d]{2,12}[-:\.]{1,2}){3,6}[\w\d]{2,12}', '', value)
        value = re.sub(r'[#\.\?!\-@_\\/:=\<\>\+&$"\'\[\]*]', ' ', value)
        value = re.sub('[{}]'.format(string.punctuation), ' ', value)
        value = value.replace('033', '').replace('01 31m', '').replace('01 35m', '')
        value = re.sub(r'01 3\dm', '', value)
        return value

    def are_similar(self, logs):
        error_messages = {}
        for log in logs:
            error_message = ''
            for log_line in log['log_lines']:
                if 'ERROR' in log_line:
                    m = re.match(r'^\S+\s+\S+\s+\S+\s\S+\s+\S+\s+(?P<log_content>.*)$', log_line)
                    if m:
                        content = m.group('log_content')
                        if not error_message:
                            error_message += content
                        else:
                            error_message += ' ' + content
            if error_message:
                if self.service_name(log['service']) not in error_messages:
                    error_messages[self.service_name(log['service'])] = []
                error_messages[self.service_name(log['service'])].append(error_message)
        error_messages = [" ".join(x) for x in error_messages.values()]
        if error_messages:
            error_messages = [self.get_anon_string(x) for x in error_messages]
            error_messages = [x for x in error_messages if x]
            error_messages = [re.sub(r'\s+', ' ', x) for x in error_messages]
            values = []
            for i in range(len(error_messages) - 1):
                for j in range(i + 1, len(error_messages)):
                    i_tokens = nltk.word_tokenize(error_messages[i])
                    j_tokens = nltk.word_tokenize(error_messages[j])
                    m1, m2 = MinHash(), MinHash()
                    for d in i_tokens:
                        m1.update(d.encode('iso-8859-1'))
                    for d in j_tokens:
                        m2.update(d.encode('iso-8859-1'))
                    value = m1.jaccard(m2)
                    values.append(value)
            if len(values) > 1:
                u_value = max(values)
            elif len(values) == 1:
                u_value = values[0]
            else:
                u_value = 0
            print(u_value)
            if u_value and u_value < 0.2:
                print(error_messages)
                input()
            if u_value < 0.5:
                return False
        else:
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

    @staticmethod
    def eval(value, enums):
        reprs = []
        for enum in enums:
            if enum.id & value:
                reprs.append(enum)
        result = ''
        for r in reprs:
            if not result:
                result += repr(r)
            else:
                result += ', ' + repr(r)
        return result


class CrashAnalyzer(BaseAnalyzer):
    IT_IS_CATASTROPHIC = CrashEnum(0x1, 'Catastrophic')
    IT_IS_RESTART = CrashEnum(0x2, 'Restart')
    IT_IS_ABORT = CrashEnum(0x4, 'Abort')
    IT_IS_SILENT = CrashEnum(0x8, 'Silent')
    IT_IS_HINDERING = CrashEnum(0x10, 'Hindering')
    IT_HAS_PASSED = CrashEnum(0x20, 'Passed')
    IT_BEHAVE_AS_EXPECTED = CrashEnum(0x40, 'Behave as expected')
    IT_IS_NONE = CrashEnum(0x80, 'Unknown')
    IT_ALL = [IT_IS_NONE, IT_BEHAVE_AS_EXPECTED, IT_HAS_PASSED, IT_IS_HINDERING, IT_IS_SILENT, IT_IS_ABORT, IT_IS_RESTART, IT_IS_CATASTROPHIC]

    def __init__(self, test_object):
        super(CrashAnalyzer, self).__init__(test_object)
        self._failure_analyzer = FailureAnalyzer(test_object)
        self._catastrophic_analyzer = CatastrophicAnalyzer(test_object)
        self._restart_analyzer = RestartAnalyzer(test_object)
        self._abort_analyzer = AbortAnalyzer(test_object)
        self._silent_analyzer = SilentAnalyzer(test_object)
        self._hindering_analyzer = HinderingAnalyzer(test_object)

    def it_is(self):
        value = 0x0
        if not self._failure_analyzer.is_faulty():
            value = value | self.IT_HAS_PASSED.id
        if self._catastrophic_analyzer.is_catastrophic():
            value = value | self.IT_IS_CATASTROPHIC.id
        if self._abort_analyzer.is_abort():
            value = value | self.IT_IS_ABORT.id
        if self._silent_analyzer.is_silent():
            value = value | self.IT_IS_SILENT.id
        if self._hindering_analyzer.is_hindering():
            value = value | self.IT_IS_HINDERING.id
        if self._restart_analyzer.is_restart():
            value = value | self.IT_IS_RESTART.id
        if self._failure_analyzer.behave_as_expected():
            value = value | self.IT_BEHAVE_AS_EXPECTED.id
        if value == 0x0:
            value = self.IT_IS_NONE.id
        return value


class App(object):
    def __init__(self):
        pass

    def use_file(self, file_name):
        with open(file_name, 'r', encoding='iso-8859-1') as r:
            test_object = json.load(r)
            crash_analyzer = CrashAnalyzer(test_object)
            result = crash_analyzer.it_is()
            print('CRASH result is', CrashEnum.eval(result, CrashAnalyzer.IT_ALL))

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
            print('{} has {} file(s)'.format(CrashEnum.eval(result, CrashAnalyzer.IT_ALL), results[result]))


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
