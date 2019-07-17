import os
import re
import json
from pprint import pprint
import seaborn as sns
import pandas as pd
from matplotlib import pyplot as plt
import datetime
import pickle
import numpy as np
import statistics
import math
from upsetplot import plot as uplot


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
        self.faults_general = None
        self.lib_virt_states = None
        self.parameters_types = None
        self.traces = []
        self.params_operators_verdicts = None
        self.struct_parameters = None
        self.message_iteration = None
        self.wait_updates_list = []
        self.together_filename = None

    def preprocess(self):
        self.number_of_tests = 0
        self.number_of_tests_that_did_not_fail = 0
        self.number_of_tests_that_fail_using_the_service_logs = 0
        self.number_of_tests_that_fail_using_the_server_logs = 0
        self.number_of_tests_that_fail_using_both_logs = 0
        self.parameters = []
        self.struct_parameters = []
        self.parameters_types = []
        self.operator_fault_map = []
        self.faults_general = []
        self.traces = []
        self.params_operators_verdicts = []
        for together_file in [os.path.join(self.together, x) for x in os.listdir(self.together)]:
            if os.path.isfile(together_file):
                name_m = re.search(r'^tester_(?P<tester>[\w]+)_{2,5}service_(?P<service>[\w]+)_{2,5}(?P<start_date>\w+_\d+_\d+_\d+_\d+_\d+)_{2,5}(?P<end_date>\w+_\d+_\d+_\d+_\d+_\d+)(\.\w+)?$', os.path.basename(together_file))
                self.tester = name_m.group('tester')
                self.service = name_m.group('service')
                self.start_date = name_m.group('start_date')
                self.end_date = name_m.group('end_date')
                with open(together_file, 'r') as together_stream:
                    self.together_filename = together_file
                    self.together_object = json.load(together_stream)
                self.walk_through_processes()
                if self.mutation_time:
                    self.set_states_and_tasks_after_mutation()
                    self.set_tests_statistics()
                    self.set_parameters_statistics()
                    self.set_operator_fault_map()
                    self.set_faults()
                else:
                    print('Problems with the file', together_file)

    def parse_service_name(self, service_name):
        return re.sub(r'\[\d+\]$', '', service_name)

    def parse_log_time(self, log_line):
        log_m = re.search(r'^(?P<log_date>\w+\s+\d+\s\d+:\d+:\d+)(,\d+)?\s?', log_line)
        tester_m = re.search(r'^\w+\s+(?P<log_date>\d+-\d+-\d+\s\d+:\d+:\d+(,\d+)?)', log_line)
        date = None
        if log_m:
            date = datetime.datetime.strptime(log_m.group('log_date'), '%b %d %H:%M:%S')
        elif tester_m:
            date = datetime.datetime.strptime(tester_m.group('log_date'), '%Y-%m-%d %H:%M:%S,%f')
        if date:
            return datetime.datetime(2000, date.month, date.day, date.hour, date.minute, date.second, date.microsecond)
        else:
            return None

    def walk_through_processes(self):
        self.map_messages_for_tester = []
        self.map_traces_per_process = {}
        self.vm_state_and_task_state = []
        self.vm_state_and_task_state_internal = []
        self.vm_state_and_task_state_activity = []
        self.mutation_operator = []
        self.lib_virt_states = []
        self.wait_updates = []
        self.failures = []
        log_line_time = None
        self.message_iteration = 0
        got_mutation = False
        mutation_operator = None
        structure = None
        misbehavior = False
        for entry in self.together_object:
            for service_name, service_entry in entry['logs'].items():
                service_name_parsed = self.parse_service_name(service_name)
                if service_name_parsed not in self.map_traces_per_process:
                    self.map_traces_per_process[service_name_parsed] = 0
                self.map_traces_per_process[service_name_parsed] += service_entry['traces']
                for log_line in [item for sublist in service_entry[service_name] for item in sublist['log_lines']]:
                    log_line_time_null = self.parse_log_time(log_line)
                    log_line_time = log_line_time_null if log_line_time_null else log_line_time
                    log_line_m = re.search(r'vm_state\s{1,3}error.{1,8}task_state\s{1,3}(?P<task_state>[\w_]+)', log_line)
                    if log_line_m:
                        vm_state = 'error'
                        task_state = log_line_m.group('task_state')
                        self.vm_state_and_task_state_internal.append((vm_state, task_state))
                        self.vm_state_and_task_state_activity.append((log_line_time, vm_state, task_state, 'internal'))
                    log_line_m = re.search(r'\'vm_state\':\s(?P<vm_state>[\'\d\w_]+)[,})].*\'task_state\':\s+(?P<task_state>[\'\w\d_]+)[.})]', log_line)
                    if not log_line_m:
                        log_line_m = re.search(r'vm_state:\s+(?P<vm_state>[\w\d_]+),\s+.*task_state:\s+(?P<task_state>[\w\d_]+),', log_line)
                    if not log_line_m:
                        log_line_m = re.search(
                            r'task_state=\'(?P<task_state>[\w\d_]+)\'.*vm_state=\'(?P<vm_state>[\w\d_]+)\'', log_line)
                    if log_line_m:
                        vm_state = log_line_m.group('vm_state')
                        task_state = log_line_m.group('task_state')
                        vm_state = vm_state
                        task_state = task_state
                        task_state = task_state if task_state else ''
                        self.vm_state_and_task_state_internal.append((vm_state, task_state))
                        self.vm_state_and_task_state_activity.append((log_line_time, vm_state, task_state, 'internal'))
                for service_list in service_entry[service_name]:
                    if service_list['type'] == 'TcTraceLog':
                        log_lines = [re.search(r"(?P<bug>\S*(exception|error|fault|failure)\S*:\s*[\w\d\s'_().""`-]*)", log_line, flags=re.IGNORECASE) for log_line in service_list['log_lines']]
                        log_lines = [x for x in log_lines if x]
                        log_lines = [x.group('bug') for x in log_lines]
                        if log_lines:
                            self.traces += log_lines
                            self.failures.append(self.parse_log_time(service_list['date']))
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
                        got_mutation = True
                    log_line_m = re.search(r'Msg\sITL=(?P<message_iteration>\d+),', log_line)
                    if log_line_m:
                        self.message_iteration = int(log_line_m.group('message_iteration'))
                    m = re.search(
                        r'Getting\sargs\svalue\sfor.{1,50}Method=(?P<method>[\w\d_]+),\sChain=(?P<param_array>\[.*]),\sType=(?P<param_type>[\w\d_]+)',
                        log_line)
                    if m:
                        params = eval(m.group('param_array'))
                        method = m.group('method')
                        param_type = m.group('param_type')
                        params = ".".join(params)
                        structure = {'message': method, 'field': params, 'fieldType': param_type}
                    log_line_m = re.search(r'Wait update # status (?P<state>.*)', log_line)
                    if log_line_m:
                        state = log_line_m.group('state')
                        self.wait_updates.append({'file': self.together_filename, 'state': state, 'corrupted': got_mutation, 'event': entry['name'], 'time': log_line_time, 'mutation': mutation_operator, 'structure': structure})
                    log_line_m = re.search(r'Wait timeout # elapsed', log_line)
                    if log_line_m:
                        self.wait_updates.append({'file': self.together_filename, 'state': 'timeout', 'corrupted': got_mutation, 'event': entry['name'], 'time': log_line_time, 'mutation': mutation_operator, 'structure': structure})
                        misbehavior = True
        if not misbehavior:
            self.wait_updates.append({'file': self.together_filename, 'state': 'final', 'corrupted': got_mutation, 'event': '', 'time': '', 'mutation': mutation_operator, 'structure': structure})
        for wait_update in self.wait_updates:
            wait_update['failures'] = len([x for x in self.failures if wait_update['time'] and x < wait_update['time']])
        self.wait_updates_list.append(self.wait_updates)

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
                    m = re.search(r'Getting\sargs\svalue\sfor.{1,50}Method=(?P<method>[\w\d_]+),\sChain=(?P<param_array>\[.*]),\sType=(?P<param_type>[\w\d_]+)', log_line)
                    if m:
                        params = eval(m.group('param_array'))
                        method = m.group('method')
                        params_line = (".".join(params), self.has_traces_from_server, self.has_traces_from_services, self.has_error_state)
                        self.parameters.append(params_line)
                        struct_param = {'method': method, 'param': params_line[0], 'server': params_line[1], 'service': params_line[2], 'error': params_line[3], 'iteration': self.message_iteration}
                        self.struct_parameters.append(struct_param)
                        self.parameters_types.append(m.group('param_type'))

                        if self.mutation_operator:
                            for operator in self.mutation_operator:
                                instance = struct_param.copy()
                                instance['operator'] = operator
                                self.params_operators_verdicts.append(instance)

    def set_states_and_tasks_after_mutation(self):
        self.vm_state_and_task_state_internal_after_mutation = []
        self.vm_state_and_task_state_after_mutation = []
        if self.mutation_time:
            self.vm_state_and_task_state_after_mutation = [x for x in self.vm_state_and_task_state_activity if x[3] == 'normal' and x[0] and x[0] >= self.mutation_time]
            self.vm_state_and_task_state_internal_after_mutation = [x for x in self.vm_state_and_task_state_activity if x[3] == 'internal' and x[0] and x[0] >= self.mutation_time]
            self.vm_state_and_task_state_after_mutation = [(x[1], x[2]) for x in self.vm_state_and_task_state_after_mutation]
            self.vm_state_and_task_state_internal_after_mutation = [(x[1], x[2]) for x in self.vm_state_and_task_state_internal_after_mutation]
        else:
            print("Problems with mutation time")

    def set_operator_fault_map(self):
        for mutation_operator in self.mutation_operator:
            self.operator_fault_map.append((mutation_operator, self.has_traces_from_server, self.has_traces_from_services, self.has_error_state))

    def set_faults(self):
        self.faults_general.append((self.has_traces_from_server, self.has_traces_from_services, self.has_error_state))


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
        self.parameter_relation_both_traces = self.build_relation_between_parameters(True, True, None)
        self.parameter_relation_server_traces = self.build_relation_between_parameters(True, False, None)
        self.parameter_relation_services_traces = self.build_relation_between_parameters(False, True, None)
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

    def chart_parameters_get_data(self, o, prev=None):
        data = {
            'States': [],
            'Value': []
        }
        for i, value in o.items():
            data['States'].append(f'{i} States')
            data['Value'].append(value + (prev['Value'][len(data['Value'])] if prev else 0))
        print(data)
        return data

    def chart_parameters(self):
        sns.set()
        sns.set_context('paper')
        sns.set_style('whitegrid')
        f, ax = plt.subplots(figsize=(6, 4))
        abort = self.chart_parameters_get_data(self.states_and_parameters_for_both_traces)
        hindering = self.chart_parameters_get_data(self.states_and_parameters_for_server_traces, abort)
        silent = self.chart_parameters_get_data(self.states_and_parameters_for_services_traces, hindering)
        pa = self.chart_parameters_get_data(self.states_and_parameters_for_none_traces, hindering)
        sns.barplot(x='Value', y='States', data=pd.DataFrame(data=pa), label='Pass', color='#28b463')
        sns.barplot(x='Value', y='States', data=pd.DataFrame(data=silent), label='Silent', color='#8e44ad')
        sns.barplot(x='Value', y='States', data=pd.DataFrame(data=hindering), label='Hindering', color='#f1c40f')
        sns.barplot(x='Value', y='States', data=pd.DataFrame(data=abort), label='Abort', color='#e74c3c')

        ax.legend(ncol=4, loc=2, frameon=False, bbox_to_anchor=(0, 1.1), borderaxespad=0.)
        ax.set(ylabel='', xlabel='')
        #ax.set_yticklabels(self.state_map(states))
        sns.despine(left=True, bottom=True)
        plt.tight_layout()
        plt.show()

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
        if server_status and services_status and not error_status:
            return 'Abort'
        if server_status and not services_status and not error_status:
            return 'Hindering'
        if not server_status and services_status and not error_status:
            return 'Silent'
        return 'Pass'

    def build_mutation_operator_fault_map_data(self, agg):
        data = {
            'operator': [],
            'state': [],
            'value': []
        }
        operators = []
        for state, stats in self.statistics:
            for operator, server, services, error in stats.operator_fault_map:
                data['state'].append(os.path.basename(state))
                data['operator'].append(operator.replace('_', '-'))
                data['value'].append(agg(server, services, error))
                operators.append(data['operator'][-1])
        operators = list(set(operators))
        table = {
            'Operator': [],
            'Mean': [],
            'Stdev': [],
            'Min': [],
            'Max': [],
            'Effectivity': [],
            'Sum': []
        }
        for operator in operators:
            states = {}
            for state, d_operator, value in zip(data['state'], data['operator'], data['value']):
                if d_operator == operator:
                    if state not in states:
                        states[state] = []
                    states[state].append(value)
            table['Operator'].append(operator)
            statdata = [len([x for x in values if x]) for state, values in states.items()]
            statdata2 = [len(values) for state, values in states.items()]
            table['Mean'].append(statistics.mean(statdata))
            table['Stdev'].append(statistics.stdev(statdata))
            table['Effectivity'].append(sum(statdata) / float(sum(statdata2)))
            table['Sum'].append(sum(statdata2))
            table['Min'].append(min(statdata))
            table['Max'].append(max(statdata))

        print(pd.DataFrame(data=table).sort_values(by=['Effectivity'], ascending=False))

        return pd.DataFrame(data=data)

    def chart_mutation_operator_fault(self):
        data = self.build_mutation_operator_fault_map_data(lambda server, service, error: error is False and (server is True or service is True))

        abort = data.pivot_table(index='operator', columns='state', values='value', fill_value=-.0001,
                                       aggfunc=lambda g: g[g == True].count() / g.count()).unstack()
        abort = pd.DataFrame({'count': abort}).reset_index()
        abort = abort.pivot('operator', 'state', 'count')
        sns.set()
        sns.set_context('paper')
        sns.set_style('whitegrid')
        sns.set(font_scale=0.7)
        f, ax = plt.subplots(figsize=(5, 6))
        mask = np.zeros_like(abort)
        mask[abort == -.0001] = True
        with sns.axes_style('white'):
            g = sns.heatmap(abort, center=0.5, annot=True, annot_kws={'fontsize': 7}, mask=mask, cmap='YlOrRd', cbar=False)
        # ax.legend(ncol=4, loc=2, frameon=False, bbox_to_anchor=(0, 1.1), borderaxespad=0.)
        ax.set(ylabel='', xlabel='')
        states = sorted(list(set(data['state'])))
        ax.set_xticklabels(self.state_map(states))
        sns.despine(left=True, bottom=True)
        plt.tight_layout()
        plt.savefig('out/paper_figure2.png', dpi=600)
        plt.show()

    def count(self, data, states, eval):
        c = {}
        for state in states:
            c[state] = 0
        for i in range(0, len(data['state'])):
            if eval(data, i):
                c[data['state'][i]] += 1
        return [c[state] for state in states]

    def build_faults_general_map_data(self):
        data = {
            'state': [],
            'server': [],
            'service': [],
            'error': []
        }

        for state, stats in self.statistics:
            for server, services, error in stats.faults_general:
                data['state'].append(os.path.basename(state))
                data['server'].append(server)
                data['service'].append(services)
                data['error'].append(error)

        return data

    def a_beautiful_state_name(self, state_name):
        return re.sub(r'^t_', '', state_name).capitalize()

    def printfchart_faults_general(self, data4):
        modes_names = ['Abort', 'Silent', 'Hindering', 'Pass']
        modes = {}
        total = sum([sum(data4[mode]) for mode in modes_names])
        for mode in modes_names:
            modes[mode] = (statistics.mean(data4[mode]), statistics.stdev(data4[mode]), sum(data4[mode]), sum(data4[mode]) / float(total))
        data = {
            'Failure Mode': [],
            'Mean': [],
            'Stdev': [],
            'Sum': [],
            'Ratio': []
        }
        for mode in modes_names:
            data['Failure Mode'].append(mode)
            data['Mean'].append(modes[mode][0])
            data['Stdev'].append(modes[mode][1])
            data['Sum'].append(modes[mode][2])
            data['Ratio'].append(modes[mode][3])
        pandas_d = pd.DataFrame(data=data)
        print(pandas_d)

    def printf_states_symptoms(self):
        data = {
            'Scenario': [],
            'Method': [],
            'Parameter': [],
            'Operator': [],
            'OnServerFault': [],
            'OnClientFault': [],
            'VmErrorFound': [],
            'Iteration': []
        }
        for state, stats in self.statistics:
            for method, parameter, operator, server, service, error, iteration in [(x['method'], x['param'], x['operator'], x['server'], x['service'], x['error'], x['iteration']) for x in stats.params_operators_verdicts]:
                scenario = os.path.basename(state)
                data['Method'].append(method)
                data['Scenario'].append(scenario)
                data['Parameter'].append(parameter)
                data['Operator'].append(operator)
                data['OnServerFault'].append(service)
                data['OnClientFault'].append(server)
                data['VmErrorFound'].append(error)
                data['Iteration'].append(iteration)
        frame = pd.DataFrame(data=data)
        result = frame[(frame['VmErrorFound'] == False)]
        result = result.assign(Faulty=(result['OnServerFault'] == True) | (result['OnClientFault'] == True))
        result.drop(['OnServerFault', 'OnClientFault', 'VmErrorFound'], inplace=True, axis=1)
        def effectivity(v):
            return len(v[v == True]) / float(len(v))
        def faulty(v):
            return len(v[v == True])
        def nonfaulty(v):
            return len(v[v == False])
        def total(v):
            return len(v)
        result = result.groupby(['Parameter', 'Operator'])['Faulty'].agg([effectivity, total, faulty, nonfaulty])
        print(result.corr(method='pearson'))
        def size(v):
            return len(v)
        newresult = result.groupby(['total', 'faulty']).size().to_frame('size').reset_index()
        print(newresult)
        sns.set()
        sns.set_context('paper')
        sns.set_style('darkgrid')
        f, ax = plt.subplots(figsize=(5, 6))
        ax = sns.regplot(x='total', y='faulty', data=newresult, ax=ax)
        ax.set(ylabel='# of failures', xlabel='# of test instances')
        sns.despine(left=True, bottom=True)
        plt.tight_layout()
        plt.show()
        result.to_csv('out/panda.csv')
        result = result.groupby(['faulty', 'total'])
        # print(result.size())

    def chart_faults_general(self):
        data = self.build_faults_general_map_data()
        # service + server = Abort
        # server = Hindering
        # service = Silent
        # pass = Pass
        data2 = {
            # 'class': ['server+service', 'server', 'service', 'pass']
            'class': ['Abort', 'Hindering', 'Silent', 'Pass']
        }

        states = list(set([os.path.basename(state) for state, stats in self.statistics]))

        for state, server_service, server, service, p in zip(
                states,
                self.count(data, states,
                      lambda df, i: df['server'][i] == True and df['service'][i] == True and df['error'][i] == False),
                self.count(data, states,
                      lambda df, i: df['server'][i] == True and df['service'][i] == False and df['error'][i] == False),
                self.count(data, states,
                      lambda df, i: df['server'][i] == False and df['service'][i] == True and df['error'][i] == False),
                self.count(data, states, lambda df, i: (df['server'][i] == False and df['service'][i] == False) or df['error'][i] == True)
        ):
            data2[state] = [server_service, server, service, p]
        data4 = {
            'State': [],
            'Abort': [],
            'Silent': [],
            'Hindering': [],
            'Pass': []
        }
        for state in states:
            data4['State'].append(state)
            acc = data2[state][0]
            data4['Abort'].append(acc)
            acc += data2[state][1]
            data4['Hindering'].append(acc)
            acc += data2[state][2]
            data4['Silent'].append(acc)
            acc += data2[state][3]
            data4['Pass'].append(acc)

        self.printfchart_faults_general(data4)
        data4pd = pd.DataFrame(data=data4)
        sns.set()
        sns.set_context('paper')
        sns.set_style('darkgrid')
        f, ax = plt.subplots(figsize=(3.5, 3.5))
        sns.barplot(x='Pass', y='State', data=data4pd, label='Pass', color='#28b463')
        sns.barplot(x='Silent', y='State', data=data4pd, label='Silent', color='#8e44ad')
        sns.barplot(x='Hindering', y='State', data=data4pd, label='Hindering', color='#f1c40f')
        sns.barplot(x='Abort', y='State', data=data4pd, label='Abort', color='#e74c3c')

        ax.legend(ncol=2, loc=2, frameon=False, bbox_to_anchor=(0, 1.15), borderaxespad=0., fontsize=8)
        ax.set(ylabel='', xlabel='')
        ax.set_yticklabels(self.state_map(states))
        ax.tick_params(labelsize=8)
        sns.despine(left=True, bottom=True)
        plt.tight_layout()
        plt.savefig('out/paper_figure1.png', dpi=600)
        plt.show()
        return

        data3 = {
            'Class': [],
            'State': [],
            'Count': []
        }
        for i, clazz in zip(range(4), data2['class']):
            for state in list(data2.keys())[1:]:
                data3['Class'].append(clazz)
                data3['State'].append(state)
                data3['Count'].append(data2[state][i])

        data = pd.DataFrame(data=data3)
        sns.set()
        sns.set_context('paper')
        sns.set_style('whitegrid')

        g = sns.catplot(x='State', y='Count', col='Class', data=data, saturation=0.5, kind='bar', ci=None, aspect=0.8, col_wrap=4, height=5, palette=sns.color_palette('Blues_r'))
        (g.set_axis_labels('', 'Count')
            .set_xticklabels(self.state_map(states), fontsize=9, rotation=90)
            .set_titles('{col_name} Mode')
            .despine(left=True))
        plt.show()

    def state_path_to_nominal_state(self, state):
        d = {
            't_build': 'Building',
            't_confirm': 'Resizing/Starting',
            't_confirm_from_resized': 'Resizing/Stopping',
            't_delete': 'Deleting',
            't_delete_from_error': 'Deleting Error',
            't_pause': 'Pausing',
            't_rebuild': 'Rebuilding',
            't_resize': 'Do Resizing',
            't_resize_from_stopped': 'Do Stopped Resizing',
            't_resume': 'Resuming'
        }
        return d[state]

    def state_map(self, states):
        return [self.state_path_to_nominal_state(state) for state in states]

    def get_scenarios_and_parameters(self):
        params_map = self.parameter_relation_both_traces
        venn_map = {}
        scenarios = []
        for param, values in params_map.items():
            new_scenarios = self.state_map(sorted([os.path.basename(x) for x in values]))
            scenarios += new_scenarios
            scenarios = list(set(scenarios))
            venn_key = ":".join(sorted(new_scenarios))
            if venn_key not in venn_map:
                venn_map[venn_key] = []
            venn_map[venn_key].append(param)
            venn_map[venn_key] = list(set(venn_map[venn_key]))
        for venn_key, size, values in sorted([(venn_key, len(venn_key.split(':')), values) for venn_key, values in venn_map.items()], key=lambda v: v[1]):
            print(venn_key, size, len(values))
        dict_data = {}
        for scenario in scenarios:
            dict_data[scenario] = []
        for venn_key, size, values in sorted(
            [(venn_key, len(venn_key.split(':')), values) for venn_key, values in venn_map.items()],
            key=lambda v: v[1]):
            for i in range(len(values)):
                scenarios_names = venn_key.split(':')
                for key in dict_data.keys():
                    dict_data[key].append(key in scenarios_names)
        dict_data = pd.DataFrame(data=dict_data)
        result = dict_data.groupby(scenarios).size()
        uplot(result, sort_by='degree', orientation='horizontal')
        plt.show()

    def printf_structures_and_failures(self):
        data = {'Scenario': [], 'Operation': [], 'Parameter': [], 'Mutation': [], 'Service': [], 'Server': [], 'Error': []}
        for scenario, stats in self.statistics:
            for instance in stats.params_operators_verdicts:
                data['Scenario'].append(os.path.basename(scenario))
                data['Operation'].append(instance['method'])
                data['Parameter'].append(instance['param'])
                data['Mutation'].append(instance['operator'])
                data['Server'].append(instance['server'])
                data['Service'].append(instance['service'])
                data['Error'].append(instance['error'])
        data = pd.DataFrame(data=data)
        data['Structure'] = data['Parameter'].apply(lambda x: x.strip().split('.')[0])
        data['Abort'] = (data['Server'] == True) & (data['Service'] == True) & (data['Error'] == False)
        data['Silent'] = (data['Server'] == True) & (data['Service'] == False) & (data['Error'] == False)
        data['Hindering'] = (data['Server'] == False) & (data['Service'] == True) & (data['Error'] == False)
        def Field(v):
            return len(list(set(v)))
        def Tests(v):
            return len(v)
        def Sum(v):
            return len(v[v == True])
        group = data.groupby(['Scenario', 'Structure'])
        group_param = group['Parameter'].agg([Field, Tests]).reset_index()
        group_abort = group['Abort'].agg(Sum).reset_index()
        group_silent = group['Silent'].agg(Sum).reset_index()
        group_hindering = group['Hindering'].agg(Sum).reset_index()
        m = pd.merge(group_param, group_abort, on=['Scenario', 'Structure'])
        m = pd.merge(m, group_silent, on=['Scenario', 'Structure'])
        m = pd.merge(m, group_hindering, on=['Scenario', 'Structure'])
        m['Failures'] = m['Silent'] + m['Abort'] + m['Hindering']
        m['Scenario'] = m['Scenario'].apply(lambda x: self.state_path_to_nominal_state(x))
        n = m.copy()
        n = n.groupby(['Scenario']).agg({'Structure': 'count', 'Field': 'sum', 'Tests': 'sum', 'Failures': 'sum', 'Abort': 'sum', 'Hindering': 'sum', 'Silent': 'sum'})
        n = n.reset_index()
        n.loc['sum'] = n.sum(numeric_only=True)
        n['%'] = n['Failures'] / n['Tests'] * 100
        n['Structure'] = n['Structure'].astype(int)
        n['Field'] = n['Field'].astype(int)
        n['Tests'] = n['Tests'].astype(int)
        n['Failures'] = n['Failures'].astype(int)
        n['Abort'] = n['Abort'].astype(int)
        n['Hindering'] = n['Hindering'].astype(int)
        n['Silent'] = n['Silent'].astype(int)
        print(n)
        n.to_csv('out/structures2.csv')
        m.to_csv('out/structures.csv')
        print(m['Structure'].unique())
        print(len(m['Structure'].unique()))

        m['Ratio'] = m['Failures'] / m['Tests']
        chart = m.pivot('Structure', 'Scenario', 'Ratio')
        sns.set()
        sns.set_context('paper')
        sns.set_style('whitegrid')
        sns.set(font_scale=0.7)
        f, ax = plt.subplots(figsize=(4, 5.5))
        mask = np.zeros_like(chart)
        mask[chart == -.0001] = True
        with sns.axes_style('white'):
            g = sns.heatmap(chart, center=0.5, annot=True, annot_kws={'size': 7}, mask=mask, cmap='YlOrRd', cbar=False)
        # ax.legend(ncol=4, loc=2, frameon=False, bbox_to_anchor=(0, 1.1), borderaxespad=0.)
        ax.set(ylabel='', xlabel='')
        #states = sorted(list(set(data['state'])))
        #ax.set_xticklabels(self.state_map(states))
        sns.despine(left=True, bottom=True)
        plt.tight_layout()
        plt.savefig('out/paper_figure3.png', dpi=600)
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

        sns.set()
        sns.set_context('paper')
        sns.set_style('whitegrid')
        f, ax = plt.subplots(figsize=(6, 4))
        palette = ['#e74c3c', '#28b463', '#f1c40f', '#8e44ad']
        sns.barplot(y='# Params', x='Matched States', hue='Classification', data=panda_data, palette=palette)
        ax.legend(ncol=4, loc=2, frameon=False, bbox_to_anchor=(0, 1.1), borderaxespad=0.)
        ax.set(ylabel='Parameters in failure mode', xlabel='Number of states where the parameter has classified into a same failure mode')
        #ax.set_yticklabels(self.state_map(states))
        sns.despine(left=True, bottom=True)
        plt.tight_layout()
        plt.show()
        return
        #ax = sns.barplot(x='state_index', y='number_of_parameters', hue='category', data=panda_data)
        g = sns.FacetGrid(panda_data, col='Classification', col_wrap=2, height=3)
        g = g.map(sns.barplot, 'Matched States', '# Params', palette='Blues_d')
        plt.show()
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

    def type_to_b(self, name):
        return name[1:].capitalize()

    def printfchart_parameters_per_state(self):
        types = []
        for state, stats in self.statistics:
            for t in stats.parameters_types:
                types.append(t)
        types = list(set(types))
        data = {
            'State': [],
            'Params': [],
            'Tests': []
        }
        types = [self.type_to_b(x) for x in types]
        for t in types:
            data[t] = []
        for state, stats in self.statistics:
            data['State'].append(os.path.basename(state))
            data['Tests'].append(len(stats.parameters))
            result = zip(stats.parameters, stats.parameters_types)
            aux_p = []
            aux_pt = []
            for p, pt in result:
                if p not in aux_p:
                    aux_p.append(p)
                    aux_pt.append(pt)
            data['Params'].append(len(aux_p))
            for t in types:
                data[t].append(len([x for x in aux_pt if self.type_to_b(x) == t]))
        data['State'] = self.state_map(data['State'])
        pdata = pd.DataFrame(data=data).sort_values(by=['Params'], ascending=False)
        print(pdata)

    # THE LAST STATE IS THE ERROR STATE
    def matrix_ended_with_error(self, wait_updates):
        return wait_updates and (((len(wait_updates) > 1 and wait_updates[-1]['state'] == 'timeout' and wait_updates[-2]['state'] == 'error')
                                  or (wait_updates[-1]['state'] == 'error') or
                                 (len(wait_updates) > 1 and wait_updates[-1]['state'] == 'final' and wait_updates[-2]['state'] == 'error')))

    # THE LAST STATE BEFORE THE EVENT WHEN THE FAULT WAS INJECTED IS THE SAME AFTER THE INJECTION
    # THE LAST STATE MUST BE THE TIMEOUT OTHERWISE THE STATE IS EXPECTED
    def matrix_ended_with_source(self, wait_updates):
        if self.matrix_ended_with_no_fault_actication(wait_updates):
            return False
        i = 0
        while i < len(wait_updates) and wait_updates[i]['corrupted'] is False:
            i += 1
        while i > 1 and wait_updates[i - 1]['event'] == wait_updates[i]['event']:
            i -= 1
        i -= 1 # IMPORTANT!
        if i > 0:
            state = wait_updates[i]['state']
        else:
            state = 'initial'
        return wait_updates and (wait_updates[-1]['state'] == 'timeout' and (wait_updates[-2]['state'] == state)) and\
            not self.matrix_ended_with_error(wait_updates)

    # THE SCENARIO CANNOT CONTINUE WHEN AN INTERMEDIATE STATE GETS STUCK THE VM
    # IT STOPS JUST AFTER THE INJECTION OF THE FAULT USING THE TARGET EVENT
    def matrix_ended_with_intermediate(self, wait_updates):
        if self.matrix_ended_with_no_fault_actication(wait_updates):
            return False
        i = 0
        while i < len(wait_updates) and wait_updates[i]['corrupted'] is False:
            i += 1
        while i < len(wait_updates) - 1 and wait_updates[i]['event'] == wait_updates[i + 1]['event']:
            i += 1
        return wait_updates and wait_updates[-1]['state'] == 'timeout' and wait_updates[-2]['event'] == wait_updates[i]['event'] and\
                not self.matrix_ended_with_source(wait_updates) and not self.matrix_ended_with_error(wait_updates)

    # IF AFTER THE MUTATION THE STATE IS NOT TIMEOUT AND THE EVENT IS OTHER THAN THE INJECTED
    # THUS, OTHER EVENTS WERE USED AFTER, THEN THE DESTINATION STATE OF THE TARGET TRANSITION WAS REACHED
    def matrix_ended_with_destination_post(self, wait_updates):
        if self.matrix_ended_with_no_fault_actication(wait_updates):
            return False
        i = 0
        while i < len(wait_updates) and wait_updates[i]['corrupted'] is False:
            i += 1
        while i < len(wait_updates) - 1 and wait_updates[i]['event'] == wait_updates[i + 1]['event']:
            i += 1
        return wait_updates and wait_updates[-1]['state'] == 'timeout' and wait_updates[i]['state'] != 'timeout' and\
            not self.matrix_ended_with_error(wait_updates)

    # CASE WHEN THE SCENARIO IS COMPLETELY EXECUTED
    def matrix_ended_destination_complete(self, wait_updates):
        return wait_updates and wait_updates[-1]['state'] != 'timeout' and wait_updates[-1]['state'] != 'error'

    def matrix_ended_with_no_fault_actication(self, wait_updates):
        return wait_updates and not [x for x in wait_updates if x['corrupted']]

    def matrix_check(self):
        cases = 0
        got = 0
        no_activation = 0
        os.remove('out/failures.txt')
        for state, stats in self.statistics:
            with open('out/failures.txt', 'a') as writer:
                writer.write('Scenario: ' + state + '\n')
                for wait_updates in stats.wait_updates_list:
                    cases += 1
                    verdicts = {
                        'complete': self.matrix_ended_destination_complete(wait_updates),
                        'post': self.matrix_ended_with_destination_post(wait_updates),
                        'inter': self.matrix_ended_with_intermediate(wait_updates),
                        'source': self.matrix_ended_with_source(wait_updates),
                        'error': self.matrix_ended_with_error(wait_updates),
                        'noact': self.matrix_ended_with_no_fault_actication(wait_updates)
                    }
                    c = verdicts.copy()
                    del c['noact']
                    if len([x for x in c.values() if x]) == 0:
                        writer.write(repr(verdicts) + '\n')
                        writer.write(repr([(x['state'], x['event'], 1 if x['corrupted'] else 0) for x in wait_updates]))
                        writer.write('\n\n')
                    if wait_updates[-1]['file'].endswith('tester_common__service_traceback___Feb_09_10_18_57_096000__Feb_09_10_19_06_487000.json'):
                        print(repr([(x['state'], x['event'], 1 if x['corrupted'] else 0) for x in wait_updates]))

    def matrix_pd_create_instance(self, labels):
        pd_data = {}
        for label in labels:
            pd_data[label] = []
        return pd_data

    def matrix_pd(self):
        pd_data = self.matrix_pd_create_instance(['file', 'scenario', 'message', 'structure', 'field', 'type', 'mutation', 'complete', 'post', 'inter', 'source', 'error', 'act', 'failures'])
        for state, stats in self.statistics:
            for wait_updates in stats.wait_updates_list:
                if not wait_updates:
                    continue
                pd_data['file'].append(wait_updates[0]['file'].split('/')[-1].split('\\')[-2] + '/' + wait_updates[0]['file'].split('\\')[-1])
                pd_data['scenario'].append(state.split('/')[-1].replace('t_', ''))
                if wait_updates[-1]['structure']:
                    pd_data['message'].append(wait_updates[-1]['structure']['message'])
                    pd_data['structure'].append(wait_updates[-1]['structure']['field'].split('.')[0])
                    pd_data['field'].append(wait_updates[-1]['structure']['field'].replace('nova_object.data.', ''))
                    pd_data['type'].append(wait_updates[-1]['structure']['fieldType'])
                else:
                    pd_data['message'].append('-')
                    pd_data['structure'].append('-')
                    pd_data['field'].append('-')
                    pd_data['type'].append('-')
                pd_data['mutation'].append(wait_updates[-1]['mutation'])
                pd_data['complete'].append(1 if self.matrix_ended_destination_complete(wait_updates) else 0)
                pd_data['post'].append(1 if self.matrix_ended_with_destination_post(wait_updates) else 0)
                pd_data['inter'].append(1 if self.matrix_ended_with_intermediate(wait_updates) else 0)
                pd_data['source'].append(1 if self.matrix_ended_with_source(wait_updates) else 0)
                pd_data['error'].append(1 if self.matrix_ended_with_error(wait_updates) else 0)
                pd_data['act'].append(0 if self.matrix_ended_with_no_fault_actication(wait_updates) else 1)
                pd_data['failures'].append(max([0] + [x['failures'] for x in wait_updates if x['corrupted']]))
        return pd.DataFrame(data=pd_data)

    def matrix_pd_check(self):
        frame = self.matrix_pd()
        frame.to_csv('out/failures.csv', sep=';')

    def matrix_pd_scenario_name_capitalize(self, value):
        if str(value).lower() == 'resize_from_stopped':
            value = 'resize #2'
        if str(value).lower() == 'resize':
            value = 'resize #1'
        if str(value).lower() == 'delete':
            value = 'delete #1'
        if str(value).lower() == 'delete_from_error':
            value = 'delete #2'
        if str(value).lower() == 'confirm':
            value = 'confirm #1'
        if str(value).lower() == 'confirm_from_resized':
            value = 'confirm #2'
        return value.replace('_', ' ').title()

    def matrix_pd_chart_by_scenario_1(self):
        frame = self.matrix_pd()
        frame = frame[frame['act'] == 1]
        frame['scenario'] = frame['scenario'].apply(self.matrix_pd_scenario_name_capitalize)
        frame['completeAndError'] = (frame['complete'] == 1) | (frame['error'] == 1)
        frame['complete'] = (frame['complete'] == 1) & (frame['error'] == 0)
        frame['failures'] = frame['failures'].apply(lambda x: 1 if x else 0)
        pass1 = frame.groupby(['scenario', 'complete']).size().to_frame('size').reset_index()
        pass2 = frame.groupby(['scenario', 'completeAndError']).size().to_frame('size').reset_index()
        total = frame.groupby(['scenario']).size().to_frame('size').reset_index()
        sns.set(style='whitegrid', context='paper')
        f, ax = plt.subplots(figsize=(3.5,4))
        sns.barplot(x='size', y='scenario', data=total, label='Others', color='#ffffff', linewidth=1, hatch='**', edgecolor='black')

        sns.barplot(x='size', y='scenario', data=(pass2[pass2['completeAndError'] == 1]), label='Pass #1', color='#ffffff', linewidth=1, hatch="xxx", edgecolor='black')

        sns.barplot(x='size', y='scenario', data=(pass1[pass1['complete'] == 1]), label='Pass #2', color='#ffffff', linewidth=1, hatch='..', edgecolor='black')

        ax.legend(ncol=1, loc='center right', frameon=True)
        ax.set(ylabel='', xlabel='')
        plt.tight_layout()
        sns.despine(left=True, bottom=True)
        plt.show()

    def matrix_pd_handle_observation(self, value):
        if value == 'post':
            return 'Other Destination'
        if value == 'inter':
            return 'Stuck in Intermediate'
        if value == 'source':
            return 'Back to Source'
        return value

    def matrix_pd_chart_by_scenario_2(self):
        frame = self.matrix_pd()
        frame = frame[frame['act'] == 1]
        frame['scenario'] = frame['scenario'].apply(self.matrix_pd_scenario_name_capitalize)
        frame = frame[(frame['error'] == 0) & (frame['complete'] == 0)]
        result = frame.groupby(['scenario', 'post', 'inter', 'source']).size().to_frame('size').reset_index()
        result['post'] = result.apply(lambda row: row['size'] if row['post'] == 1 else 0, axis=1)
        result['inter'] = result.apply(lambda row: row['size'] if row['inter'] == 1 else 0, axis=1)
        result['source'] = result.apply(lambda row: row['size'] if row['source'] == 1 else 0, axis=1)
        del result['size']
        result = pd.melt(result, id_vars="scenario", var_name="case", value_name="sum")
        result = result[result['sum'] > 0]
        result = result.rename(index=str, columns={'case': 'Observation'})
        result['Observation'] = result['Observation'].apply(self.matrix_pd_handle_observation)
        print(result)
        sns.set(style='whitegrid', context='paper')
        f, ax = plt.subplots(figsize=(3.5, 6))
        palette = ['white']
        bar = sns.barplot(x='sum', y='scenario', hue='Observation', data=result, palette=palette, edgecolor='black', linewidth=1)
        hatches = ['xxxx', '|||', '....']
        for i, thebar in enumerate(bar.patches):
            thebar.set_hatch(hatches[i % 3])
        ax.set(ylabel='', xlabel='')
        ax.legend(bbox_to_anchor=(0.05, 1), loc='center center', ncol=1, title='User Observation')
        plt.tight_layout()
        sns.despine(left=True, bottom=True)
        plt.show()


if __name__ == '__main__':
    need_processing = False
    if need_processing:
        states = []
        for x in os.listdir('out/together'):
            candidate = f'out/together/{x}'
            if os.path.isdir(candidate):
                states.append(candidate)

        general = StateParameterFaultRelationGeneral(states)
        general.collect_statistics()
        pickle.dump(general, open('general.pkl', 'wb'))
    else:
        general = pickle.load(open('general.pkl', 'rb'))
    # general.chart_mutation_operator_fault() # heatmap
    # general.chart_faults_general() # crash
    # general.chart_parameters()
    # general.show_states_parameters() # params
    # general.printfchart_parameters_per_state()
    # general.get_scenarios_and_parameters()
    # general.printf_states_symptoms()
    # general.printf_structures_and_failures()
    #general.matrix_check()
    general.matrix_pd_chart_by_scenario_2()
    print('End')