import os
import re
import json
from pprint import pprint
import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt
import datetime


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
        self.vm_state_and_task_state = None
        self.vm_state_and_task_state_internal = None
        self.vm_state_and_task_state_after_mutation = None
        self.vm_state_and_task_state_internal_after_mutation = None
        self.vm_state_and_task_state_activity = None
        self.has_error_state = None
        self.mutation_time = None
        self.mutation_operator = None
        self.operator_fault_map = None

    def preprocess(self):
        self.number_of_tests = 0
        self.number_of_tests_that_did_not_fail = 0
        self.number_of_tests_that_fail_using_the_service_logs = 0
        self.number_of_tests_that_fail_using_the_server_logs = 0
        self.number_of_tests_that_fail_using_both_logs = 0
        self.parameters = []
        self.operator_fault_map = []
        for together_file in [os.path.join(self.together, x) for x in os.listdir(self.together)]:
            if os.path.isfile(together_file):
                name_m = re.search(r'^tester_(?P<tester>[\w]+)_{2,5}service_(?P<service>[\w]+)_{2,5}(?P<start_date>\w+_\d+_\d+_\d+_\d+_\d+)_{2,5}(?P<end_date>\w+_\d+_\d+_\d+_\d+_\d+)(\.\w+)?$', os.path.basename(together_file))
                self.tester = name_m.group('tester')
                self.service = name_m.group('service')
                self.start_date = name_m.group('start_date')
                self.end_date = name_m.group('end_date')
                with open(together_file, 'r') as together_stream:
                    self.together_object = json.load(together_stream)
                self.walk_through_processes()
                self.set_states_and_tasks_after_mutation()
                self.set_tests_statistics()
                self.set_parameters_statistics()
                self.set_operator_fault_map()

    def parse_service_name(self, service_name):
        return re.sub(r'\[\d+\]$', '', service_name)

    def parse_log_time(self, log_line):
        log_m = re.search(r'^(?P<log_date>\w+\s\d+\s\d+:\d+:\d+)\s', log_line)
        tester_m = re.search(r'^\w+\s+(?P<log_date>\d+-\d+\d+\s\d+:\d+:\d+(,\d+)?)', log_line)
        if log_m:
            return datetime.datetime.strptime(log_m.group('log_date'), '%b %d %H:%M:%S')
        elif tester_m:
            return datetime.datetime.strptime(tester_m.group('log_date'), '%Y-%m-%d %H:%M:%S')
        return None

    def walk_through_processes(self):
        self.map_messages_for_tester = []
        self.map_traces_per_process = {}
        self.vm_state_and_task_state = []
        self.vm_state_and_task_state_internal = []
        self.vm_state_and_task_state_activity = []
        self.mutation_operator = []
        for entry in self.together_object:
            for service_name, service_entry in entry['logs'].items():
                service_name_parsed = self.parse_service_name(service_name)
                if service_name_parsed not in self.map_traces_per_process:
                    self.map_traces_per_process[service_name_parsed] = 0
                self.map_traces_per_process[service_name_parsed] += service_entry['traces']
                for log_line in [item for sublist in service_entry[service_name] for item in sublist['log_lines']]:
                    log_line_time = self.parse_log_time(log_line)
                    log_line_m = re.search(r'vm_state\s{1,3}error.{1,8}task_state\s{1,3}(?P<task_state>[\w_]+)', log_line)
                    if log_line_m:
                        vm_state = 'error'
                        task_state = log_line_m.group('task_state')
                        self.vm_state_and_task_state_internal.append((vm_state, task_state))
                        self.vm_state_and_task_state_activity.append((log_line_time, vm_state, task_state, 'internal'))
                    log_line_m = re.search(r'\'vm_state\':\s(?P<vm_state>[\'\d\w_]+)[,})].*\'task_state\':\s+(?P<task_state>[\'\w\d_]+)[.})]', log_line)
                    if log_line_m:
                        vm_state = log_line_m.group('vm_state')
                        task_state = log_line_m.group('task_state')
                        vm_state = eval(vm_state)
                        task_state = eval(task_state)
                        task_state = task_state if task_state else ''
                        self.vm_state_and_task_state_internal.append((vm_state, task_state))
                        self.vm_state_and_task_state_activity.append((log_line_time, vm_state, task_state, 'internal'))
            for log in entry['tester']:
                for log_line in log['log_lines']:
                    log_line_m = re.search(r'Message\smethod=(?P<message_function_name>\S+)$', log_line)
                    log_line_time = self.parse_log_time(log_line)
                    if log_line_m:
                        time_parsed = self.parse_log_time(log_line)
                        message_function_name = log_line_m.group('message_function_name')
                        self.map_messages_for_tester.append((time_parsed, message_function_name))
                    log_line_m = re.search(r'"vm_state\\{1,6}":\s{0,3}\\{1,3}"(?P<vm_state>[\w_]+)\\.*"task_state\\{1,6}":\s{1,3}\\{1,5}"(?P<task_state>[\w_]+)\\', log_line)
                    if log_line_m:
                        vm_state = log_line_m.group('vm_state')
                        task_state = log_line_m.group('task_state')
                        self.vm_state_and_task_state.append((vm_state, task_state))
                        self.vm_state_and_task_state_activity.append((log_line_time, vm_state, task_state, 'normal'))
                    log_line_m = re.search(r'Got\smutation\s\S(?P<mutation_operator>[\w_]+)\S', log_line)
                    if log_line_m:
                        self.mutation_time = self.parse_log_time(log_line)
                        mutation_operator = log_line_m.group('mutation_operator')
                        self.mutation_operator.append(mutation_operator)

    def set_tests_statistics(self):
        self.number_of_tests += 1
        has_traces_from_services = [x for x in self.together_object if [y for y, w in x['logs'].items() if w['traces'] > 0]]
        has_traces_from_server = [x for x in self.together_object if [y for y in x['tester'] if y['type'] == 'TcTraceLog']]
        has_error_state = [x for x in self.vm_state_and_task_state_after_mutation if 'error' in " ".join(x).lower()]
        has_error_state = has_error_state if has_error_state else [x for x in self.vm_state_and_task_state_internal_after_mutation if 'error' in " ".join(x).lower()]
        self.number_of_tests_that_fail_using_both_logs += 1 if has_traces_from_server and has_traces_from_services else 0
        self.number_of_tests_that_fail_using_the_server_logs += 1 if has_traces_from_server and not has_traces_from_services else 0
        self.number_of_tests_that_fail_using_the_service_logs += 1 if has_traces_from_services and not has_traces_from_server else 0
        self.number_of_tests_that_did_not_fail += 1 if not has_traces_from_server and not has_traces_from_services else 0
        self.has_traces_from_services = True if has_traces_from_services else False
        self.has_traces_from_server = True if has_traces_from_server else False
        self.has_error_state = True if has_error_state else False

    def set_parameters_statistics(self):
        for x in self.together_object:
            for trace in x['tester']:
                for log_line in trace['log_lines']:
                    m = re.search(r'Getting\sargs\svalue\sfor.{2,50}Chain=(?P<param_array>\[.*]),\sType', log_line)
                    if m:
                        params = eval(m.group('param_array'))
                        params_line = (".".join(params), self.has_traces_from_server, self.has_traces_from_services, self.has_error_state)
                        self.parameters.append(params_line)

    def set_states_and_tasks_after_mutation(self):
        self.vm_state_and_task_state_internal_after_mutation = []
        self.vm_state_and_task_state_after_mutation = []
        if self.mutation_time:
            self.vm_state_and_task_state_after_mutation = [x for x in self.vm_state_and_task_state_activity if x[3] == 'normal' and x[0] >= self.mutation_time]
            self.vm_state_and_task_state_internal_after_mutation = [x for x in self.vm_state_and_task_state_activity if x[3] == 'internal' and x[0] >= self.mutation_time]
            self.vm_state_and_task_state_after_mutation = [(x[1], x[2]) for x in self.vm_state_and_task_state_after_mutation]
            self.vm_state_and_task_state_internal_after_mutation = [(x[1], x[2]) for x in self.vm_state_and_task_state_internal_after_mutation]

    def set_operator_fault_map(self):
        for mutation_operator in self.mutation_operator:
            self.operator_fault_map.append((mutation_operator, self.has_traces_from_server, self.has_traces_from_services, self.has_error_state))


class StateParameterFaultRelationGeneral(object):
    def __init__(self, states):
        self.states = states
        self.statistics = None
        self.parameter_relation_server_traces = None
        self.parameter_relation_services_traces = None
        self.parameter_relation_both_traces = None
        self.parameter_relation_none_traces = None
        self.states_and_parameters_for_server_traces = None
        self.states_and_parameters_for_services_traces = None
        self.states_and_parameters_for_both_traces = None
        self.states_and_parameters_for_none_traces = None

    def collect_statistics(self):
        self.statistics = []
        for state in self.states:
            stats = StateParameterFaultRelation(state)
            stats.preprocess()
            self.statistics += [(state, stats)]
        self.build_parameter_relation()
        self.set_states_and_parameters()

    def build_parameter_relation(self):
        self.parameter_relation_both_traces = self.build_relation_between_parameters(True, True)
        self.parameter_relation_server_traces = self.build_relation_between_parameters(True, False)
        self.parameter_relation_services_traces = self.build_relation_between_parameters(False, True)
        self.parameter_relation_none_traces = self.build_relation_between_parameters(False, False)

    def build_relation_between_parameters(self, has_traces_from_server, has_traces_from_services, has_error=None):
        parameter_relation = {}
        for i in range(len(self.statistics) - 1):
            stats = self.statistics[i]
            for j in range(i, len(self.statistics)):
                other = self.statistics[j]
                for stats_param in stats[1].parameters:
                    for other_param in other[1].parameters:
                        if stats_param[0] == other_param[0] and stats_param[1] == other_param[1] and stats_param[2] == other_param[2] and\
                                (has_error is None or other_param[2] == stats_param[2]):
                            if stats_param[1] == has_traces_from_server and stats_param[2] == has_traces_from_services and\
                                    (has_error is None or has_error == stats_param[2]):
                                if stats_param[0] not in parameter_relation:
                                    parameter_relation[stats_param[0]] = []
                                parameter_relation[stats_param[0]].append(other[0])
        for key, value in parameter_relation.items():
            parameter_relation[key] = list(set(value))
        return parameter_relation

    def set_states_and_parameters(self):
        self.states_and_parameters_for_both_traces = self.set_states_and_parameters_for(self.parameter_relation_both_traces)
        self.states_and_parameters_for_server_traces = self.set_states_and_parameters_for(self.parameter_relation_server_traces)
        self.states_and_parameters_for_services_traces = self.set_states_and_parameters_for(self.parameter_relation_services_traces)
        self.states_and_parameters_for_none_traces = self.set_states_and_parameters_for(self.parameter_relation_none_traces)

    def set_states_and_parameters_for(self, parameter_relation):
        states_and_parameters = {}
        for i in range(1, len(self.states) + 1):
            states_and_parameters[i] = 0
            for param, values in parameter_relation.items():
                if len(values) == i:
                    states_and_parameters[i] += 1
        return states_and_parameters

    def set_data_set_states_parameters(self, data, states_parameters, category):
        for state_index, params in states_parameters.items():
            data['Matched States'] += [state_index]
            data['# Params'] += [params]
            data['Classification'] += [category]

    def build_label(self, server_status, services_status, error_status=False):
        services_label = 'OS' if services_status else ''
        server_label = 'TD' if server_status else ''
        error_label = 'E' if error_status else ''
        label = "+".join([services_label, server_label, error_label])
        if label:
            return label
        return 'OK'

    def build_mutation_operator_fault_map_data(self):
        data = {
            'operator': [],
            'state': [],
            'server': [],
            'service': [],
            'error': []
        }
        for state, stats in self.statistics:
            for operator, server, services, error in stats.operator_fault_map:
                data['state'].append(os.path.basename(state))
                data['operator'].append(operator)
                data['server'].append(server)
                data['service'].append(services)
                data['error'].append(error)
        return pd.DataFrame(data=data)

    def chart_mutation_operator_fault(self):
        def aggfunc(g):
            return g[g == True].count() / g.count()

        data = self.build_mutation_operator_fault_map_data()
        server_true = data.pivot_table(index='operator', columns='state', values='server', fill_value=0, aggfunc=aggfunc).unstack()
        server_true = pd.DataFrame({'count': server_true}).reset_index()
        result = server_true
        print(result)
        errors = result.pivot('operator', 'state', 'count')
        sns.heatmap(errors)
        plt.show()

    def show_states_parameters(self):
        data = {
            "Matched States": [],
            "# Params": [],
            "Classification": []
        }

        self.set_data_set_states_parameters(data, self.states_and_parameters_for_both_traces, self.build_label(True, True))
        self.set_data_set_states_parameters(data, self.states_and_parameters_for_none_traces, self.build_label(False, False))
        self.set_data_set_states_parameters(data, self.states_and_parameters_for_server_traces, self.build_label(True, False))
        self.set_data_set_states_parameters(data, self.states_and_parameters_for_services_traces, self.build_label(False, True))

        panda_data = pd.DataFrame(data=data)
        #ax = sns.barplot(x='state_index', y='number_of_parameters', hue='category', data=panda_data)
        g = sns.FacetGrid(panda_data, col='Classification', col_wrap=2, height=3)
        g = g.map(sns.barplot, 'Matched States', '# Params', palette='Blues_d')
        # plt.show()
        plt.savefig('out/charts/states_parameters.png', dpi=600)
        plt.clf()

    def show_tests_params(self):
        data = {
            'State Name': [],
            '# Tests': []
        }
        for i, stats in zip(range(len(self.statistics)), self.statistics):
            data['State Name'].append('S' + str(i + 1))
            data['# Tests'].append(stats[1].number_of_tests)
            print('S' + str(i + 1), stats[0])
        panda_data = pd.DataFrame(data=data)
        ax = sns.barplot('State Name', '# Tests', data=panda_data, palette='Blues_d')
        plt.savefig('out/charts/tests_params.png', dpi=600)
        plt.clf()


if __name__ == '__main__':
    states = []
    for x in os.listdir('out/together'):
        candidate = f'out/together/{x}'
        if os.path.isdir(candidate):
            states.append(candidate)

    general = StateParameterFaultRelationGeneral(states)
    general.collect_statistics()
    general.chart_mutation_operator_fault()