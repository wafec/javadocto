import re
import datetime
from osdsn2.analytics import exception


CRITICAL_SERVICES = [
    'systemd',
    'kernel'
]


FRONTIER_SERVICES = [
    'desvstack@n-api.service'
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
        m = re.match(r'^(?P<s_name>[\w\-\._]+)(\[\d+\])?$', full_name)
        if m:
            return m.group('s_name')
        return full_name


class FailureAnalyzer(BaseAnalyzer):
    def __init__(self, test_object):
        super(FailureAnalyzer, self).__init__(test_object)

    def got_mutation_at(self):
        log = self.iter_over_logs(lambda log_lines, _: [x for x in log_lines if re.search(r'Got mutation', x)], True)
        if log is None:
            raise exception.NoMutationFound()
        return log['date']

    def got_errors_at(self):
        logs = self.iter_over_logs(lambda log_lines, _: [x for x in log_lines if re.search(r'vm_state.*error', x)], False)
        if not logs:
            raise exception.NoErrorFound()
        return [x['date'] for x in logs]

    def is_faulty(self):
        try:
            mutation_date = self.got_mutation_at()
            errors_date = self.got_errors_at()
            format = '%b %d %H:%M:%S,%f'
            no_error = not [x for x in errors_date if datetime.datetime.strptime(x, format) >
                            datetime.datetime.strptime(mutation_date, format)]
            tester = self.iter_over_tester(lambda log_lines, log: log['type'] == 'TcTraceLog')
            return tester and no_error
        except exception.NoMutationFound:
            return False
        except exception.NoErrorFound:
            return True


class CatastrophicAnalyzer(BaseAnalyzer):
    def __init__(self, test_object):
        super(CatastrophicAnalyzer, self).__init__(test_object)

    def is_catastrophic(self):
        return self.iter_over_logs(lambda log_lines, log: self.service_name(log['service']) in CRITICAL_SERVICES and
                                   log['type'] == 'TcTraceLog')


class RestartAnalyzer(BaseAnalyzer):
    def __init__(self, test_object):
        super(RestartAnalyzer, self).__init__(test_object)

    def is_restart(self):
        return False


class AbortAnalyzer(BaseAnalyzer):
    def __init__(self, test_object):
        super(AbortAnalyzer, self).__init__(test_object)

    def is_abort(self):
        return self.iter_over_logs(lambda log_lines, log: log['type'] == 'TcTraceLog')


class SilentAnalyzer(BaseAnalyzer):
    def __init__(self, test_object):
        super(SilentAnalyzer, self).__init__(test_object)

    def is_silent(self):
        return self.iter_over_logs(lambda log_lines, log: log['type'] == 'TcTraceLog' and
                                   self.service_name(log['service']) in FRONTIER_SERVICES)


class HinderingAnalyzer(BaseAnalyzer):
    def __init__(self, test_object):
        super(HinderingAnalyzer, self).__init__(test_object)

    def is_hindering(self):
        results = self.iter_over_logs(lambda log_lines, log: log['type'] == 'TcTraceLog' and
                                      self.service_name(log['service']) in TESTING_SERVICES)
        return self.are_similar(results)

    def are_similar(self, logs):
        return True


class CrashAnalyzer(FailureAnalyzer, CatastrophicAnalyzer, RestartAnalyzer, AbortAnalyzer, SilentAnalyzer, HinderingAnalyzer):
    IT_IS_CATASTROPHIC = 0
    IT_IS_RESTART = 1
    IT_IS_ABORT = 2
    IT_IS_SILENT = 3
    IT_IS_HINDERING = 4
    IT_IS_NONE = 5

    def __init__(self, test_object):
        FailureAnalyzer.__init__(self, test_object)
        CatastrophicAnalyzer.__init__(self, test_object)
        RestartAnalyzer.__init__(self, test_object)
        AbortAnalyzer.__init__(self, test_object)
        SilentAnalyzer.__init__(self, test_object)
        HinderingAnalyzer.__init__(self, test_object)

    def it_is(self):
        if self.is_catastrophic():
            return self.IT_IS_CATASTROPHIC
        if self.is_restart():
            return self.IT_IS_RESTART
        if self.is_abort():
            if self.is_silent():
                return self.IT_IS_SILENT
            if self.is_hindering():
                return self.IT_IS_HINDERING
            return self.IT_IS_ABORT
        return self.IT_IS_NONE
