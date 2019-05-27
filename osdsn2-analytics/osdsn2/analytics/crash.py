import re
import datetime
from osdsn2.analytics import exception


CRITICAL_SERVICES = [
    'systemd',
    'kernel'
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
                        if consumer(log.log_lines, log):
                            if stop_at_first:
                                return log
                            else:
                                results.append(log)
        if stop_at_first:
            return None
        else:
            return results


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
            return not [x for x in errors_date if datetime.datetime.strptime(x, format) >
                        datetime.datetime.strptime(mutation_date, format)]
        except exception.NoMutationFound:
            return False
        except exception.NoErrorFound:
            return True


class CatastrophicAnalyzer(BaseAnalyzer):
    def __init__(self, test_object):
        super(CatastrophicAnalyzer, self).__init__(test_object)

    def is_catastrophic(self):
        return self.iter_over_logs(lambda log_lines, log: log['service'] in CRITICAL_SERVICES and
                                   log['type'] == 'TcTraceLog')


class RestartAnalyzer(BaseAnalyzer):
    def __init__(self, test_object):
        super(RestartAnalyzer, self).__init__(test_object)


class AbortAnalyzer(BaseAnalyzer):
    def __init__(self, test_object):
        super(AbortAnalyzer, self).__init__(test_object)

    def is_abort(self):
        return self.iter_over_logs(lambda log_lines, log: log['type'] == 'TcTraceLog')


