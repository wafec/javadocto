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

    def preprocess(self):
        self.number_of_tests = 0
        self.number_of_tests_that_did_not_fail = 0
        self.number_of_tests_that_fail_using_the_service_logs = 0
        self.number_of_tests_that_fail_using_the_server_logs = 0
        self.number_of_tests_that_fail_using_both_logs = 0
        self.parameters = []
        self.parameters_types = []
        self.operator_fault_map = []
        self.faults_general = []
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
        log_m = re.search(r'^(?P<log_date>\w+\s+\d+\s\d+:\d+:\d+)\s', log_line)
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
        log_line_time = None
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
                    m = re.search(r'Getting\sargs\svalue\sfor.{2,50}Chain=(?P<param_array>\[.*]),\sType=(?P<param_type>[\w\d_]+)', log_line)
                    if m:
                        params = eval(m.group('param_array'))
                        params_line = (".".join(params), self.has_traces_from_server, self.has_traces_from_services, self.has_error_state)
                        self.parameters.append(params_line)
                        self.parameters_types.append(m.group('param_type'))

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
        f, ax = plt.subplots(figsize=(7.8, 7))
        mask = np.zeros_like(abort)
        mask[abort == -.0001] = True
        with sns.axes_style('white'):
            g = sns.heatmap(abort, center=0.5, annot=True, mask=mask, cmap='YlOrRd')
        # ax.legend(ncol=4, loc=2, frameon=False, bbox_to_anchor=(0, 1.1), borderaxespad=0.)
        ax.set(ylabel='', xlabel='Operator effectivity ratio among different states')
        states = sorted(list(set(data['state'])))
        ax.set_xticklabels(self.state_map(states))
        sns.despine(left=True, bottom=True)
        plt.tight_layout()
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
        sns.set_style('whitegrid')
        f, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(x='Pass', y='State', data=data4pd, label='Pass', color='#28b463')
        sns.barplot(x='Silent', y='State', data=data4pd, label='Silent', color='#8e44ad')
        sns.barplot(x='Hindering', y='State', data=data4pd, label='Hindering', color='#f1c40f')
        sns.barplot(x='Abort', y='State', data=data4pd, label='Abort', color='#e74c3c')

        ax.legend(ncol=4, loc=2, frameon=False, bbox_to_anchor=(0, 1.1), borderaxespad=0.)
        ax.set(ylabel='', xlabel='Number of test cases assigned to a specific failure mode in a state')
        ax.set_yticklabels(self.state_map(states))
        sns.despine(left=True, bottom=True)
        plt.tight_layout()
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

    def state_map(self, states):
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
        return [d[state] for state in states]

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
        pdata = pd.DataFrame(data=data)
        print(pdata)

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
    general.chart_mutation_operator_fault() # heatmap
    # general.chart_faults_general() # crash
    # general.chart_parameters()
    # general.show_states_parameters() # params
    # general.printfchart_parameters_per_state()