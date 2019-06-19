import os
import re
import json


class StateParameterFaultRelation(object):
    def __init__(self, together):
        self.together = together
        self.tester = None
        self.service = None
        self.start_date = None
        self.end_date = None
        self.together_object = None
        self.map_messages_for_tester = None
        self.map_traces_per_process = None
        self.number_of_tests = None
        self.number_of_tests_that_fail_using_the_server_logs = None
        self.number_of_tests_that_fail_using_the_service_logs = None
        self.number_of_tests_that_fail_using_both_logs = None
        self.number_of_tests_that_did_not_fail = None
        self.has_traces_from_services = None
        self.has_traces_from_server = None
        self.parameters = None

    def preprocess(self):
        self.number_of_tests = 0
        self.number_of_tests_that_did_not_fail = 0
        self.number_of_tests_that_fail_using_the_service_logs = 0
        self.number_of_tests_that_fail_using_the_server_logs = 0
        self.number_of_tests_that_fail_using_both_logs = 0
        self.parameters = []
        for together_file in [os.path.join(self.together, x) for x in os.listdir(self.together)]:
            if os.path.isfile(together_file):
                name_m = re.search(r'^tester_(?P<tester>[\w]+)_{2,5}service_(?P<service>[\w]+)_{2,5}(?P<start_date>\w+_\d+_\d+_\d+_\d+_\d+)_{2,5}(?P<end_date>\w\+_\d+_\d+_\d+_\d+_\d+)(\.\w+)?$', os.path.basename(together_file))
                self.tester = name_m.group('tester')
                self.service = name_m.group('service')
                self.start_date = name_m.group('start_date')
                self.end_date = name_m.group('end_date')
                with open(together_file, 'r') as together_stream:
                    self.together_object = json.load(together_stream)
                self.walk_through_processes()
                self.set_tests_statistics()
                self.set_parameters_statistics()

    def parse_service_name(self, service_name):
        return re.sub(r'\[\d+\]$', '', service_name)

    def parse_log_time(self, log_line):
        log_m = re.search(r'^(?P<log_date>\w+\s\d+\s\d+:\d+:\d+)\s', log_line)
        tester_m = re.search(r'^\w+\s+(?P<log_date>\d+-\d+\d+\s\d+:\d+:\d+(,\d+)?)', log_line)
        if log_m:
            return log_m.group('log_date')
        elif tester_m:
            return tester_m.group('log_date')
        return None

    def walk_through_processes(self):
        self.map_messages_for_tester = []
        self.map_traces_per_process = {}
        for entry in self.together_object:
            for service_name, service_entry in entry['logs'].items():
                service_name_parsed = self.parse_service_name(service_name)
                if service_name_parsed not in self.map_traces_per_process:
                    self.map_traces_per_process[service_name_parsed] = 0
                self.map_traces_per_process[service_name_parsed] += service_entry[service_name]['traces']
            for log in entry['tester']:
                for log_line in log['log_lines']:
                    log_line_m = re.search(r'Message\smethod=(?P<message_function_name>\S+)$', log_line)
                    if log_line_m:
                        time_parsed = self.parse_log_time(log_line)
                        message_function_name = log_line_m.group('message_function_name')
                        self.map_messages_for_tester.append((time_parsed, message_function_name))

    def set_tests_statistics(self):
        self.number_of_tests += 1
        has_traces_from_services = [x for x in self.together_object if [y for y, w in x['logs'].items() if w['traces']]]
        has_traces_from_server = [x for x in self.together_object if [y for y in x['tester'] if y['type'] == 'TcTraceLog']]
        self.number_of_tests_that_fail_using_both_logs += 1 if has_traces_from_server and has_traces_from_services else 0
        self.number_of_tests_that_fail_using_the_server_logs += 1 if has_traces_from_server and not has_traces_from_services else 0
        self.number_of_tests_that_fail_using_the_service_logs += 1 if has_traces_from_services and not has_traces_from_server else 0
        self.number_of_tests_that_did_not_fail += 1 if not has_traces_from_server and not has_traces_from_services else 0
        self.has_traces_from_services = has_traces_from_services
        self.has_traces_from_server = has_traces_from_server

    def set_parameters_statistics(self):
        for x in self.together_object:
            for trace in x['tester']:
                for log_line in trace['log_lines']:
                    m = re.search(r'Getting\sargs\svalue\sfor.{2,10}Chain=(?P<param_array>\[.*\]),\sType', log_line)
                    if m:
                        params = eval(m.group('param_array'))
                        params_line = (".".join(params), self.has_traces_from_server, self.has_traces_from_services)
                        self.parameters.append(params_line)


class StateParameterFaultRelationGeneral(object):
    def __init__(self, states):
        self.states = states
        self.statistics = None
        self.parameter_relation_server_traces = None
        self.parameter_relation_services_traces = None
        self.parameter_relation_both_traces = None
        self.parameter_relation_none_traces = None

    def collect_statistics(self):
        self.statistics = []
        for state in self.states:
            stats = StateParameterFaultRelation(state)
            stats.preprocess()
            self.statistics += [(state, stats)]
        self.parameter_relation_both_traces = self.build_relation_between_parameters(True, True)
        self.parameter_relation_server_traces = self.build_relation_between_parameters(True, False)
        self.parameter_relation_services_traces = self.build_relation_between_parameters(False, True)
        self.parameter_relation_none_traces = self.build_relation_between_parameters(False, False)

    def build_relation_between_parameters(self, has_traces_from_server, has_traces_from_services):
        parameter_relation = {}
        for i in range(len(self.statistics) - 1):
            stats = self.statistics[i]
            for j in range(i + 1, len(self.statistics)):
                other = self.statistics[j]
                for stats_param in stats[1].parameters:
                    if stats_param[0] not in parameter_relation:
                        for other_param in other[1].parameters:
                            if stats_param[0] == other_param[0] and stats_param[1] == other_param[1] and stats_param[2] == other_param[2]:
                                if stats_param[1] == has_traces_from_server and stats_param[2] == has_traces_from_services:
                                    if stats_param[0] not in parameter_relation:
                                        parameter_relation[stats_param[0]] = []
                                    parameter_relation[stats_param[0]].append(other[0])
        for key, value in parameter_relation.items():
            parameter_relation[key] = list(set(value))
        return parameter_relation
