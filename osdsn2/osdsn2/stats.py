import re
import ast
import argparse
import collections
import inspect
import sys
from datetime import datetime
from ruamel.yaml import YAML
from pathlib import Path
import csv


EF_LOG_PREFIX_PATTERN = r"(\w+\s*[\d-]+\s[\d:,]+\s.*\s.*\s\d+:\s)(.*$)"


def foreach_message_in(file, consumer, buffer_len=1000, stop_on_fail=True):
    buffer = collections.deque(maxlen=buffer_len)
    with open(file, 'r', errors="replace") as reader:
        for line in reader:
            try:
                buffer.append(line)
                m = re.match(EF_LOG_PREFIX_PATTERN, line)
                if m:
                    consumer_number_of_params = len(inspect.signature(consumer).parameters)
                    if consumer_number_of_params == 1:
                        consumer(m.group(2))
                    elif consumer_number_of_params == 2:
                        consumer(m.group(2), buffer)
                    elif consumer_number_of_params == 3:
                        consumer(m.group(2), buffer, m.group(1))
            except Exception as exception:
                print("ERROR:", line)
                if stop_on_fail:
                    raise exception


def print_ef_log_by_states(file):
    def consumer(message):
        if message.startswith('Run Name'):
            m = re.match(r"\w+\s\w+=(\w+),\s\w+=\w+\((.*)\).*", message)
            cmd = m.group(1)
            args = m.group(2)
            print("Command:", cmd + ",", "Parameters:", args)
        elif message.startswith('Wait update'):
            m = re.match(r"\w+\s\w+\s.\s\w+\s(.*$)", message)
            st = m.group(1)
            print("    ", "[sub]State:", st)
        elif message.startswith('Received message'):
            m = re.match(r".*method...:\s...([\w_\d]+).*", message)
            if m:
                op = m.group(1)
                print("    ", "Operation:", op)

    foreach_message_in(file, consumer)


def print_ef_log_by_sample_stats(file, include_params_details=True):
    flag_first_op = False
    op_mapping_params = {}

    def consumer(message):
        nonlocal flag_first_op
        nonlocal op_mapping_params

        if message.startswith('Method='):
            if not flag_first_op:
                print("Operation Chain:")
                flag_first_op = True
            m = re.match(r"\w+=([\w_\d]+),\s\w+\s\w+=(\d+)\s", message)
            op = m.group(1)
            n = m.group(2)
            print("    ", "#:", n + ',', "Operation:", op)
        elif message.startswith('There were filtered'):
            m = re.match(r".*\s(\d+)\s.*\w+\s(\d+)$", message)
            total_out = m.group(1)
            total = m.group(2)
            total_in = int(total) - int(total_out)
            print("Parameters Stats:")
            print("    ", "// Out filter ignores parameters with '.' character within")
            print("    ", "Total:", total + ",", "Out:", total_out + ",", "In: ", total_in)
        elif message.startswith('I=Name'):
            m = re.match(r".*M=(\d+),\sP=\w+=([\w_\d]+),\s\w+=(\[['\w_.,\s]+\]),\sType=_(\w+)$", message)
            n = m.group(1)
            op = m.group(2)
            chain = m.group(3)
            dt = m.group(4)
            if dt.lower() == 'dict':
                dt = 'object'
            chain = ast.literal_eval(chain)
            chain = [x for x in chain if '.' not in x]

            if n not in op_mapping_params:
                op_mapping_params[n] = []

            op_mapping_params[n].append((chain, dt, op))
        elif message.startswith('Calculator'):
            m = re.match(r"\w+\s(.*)$", message)
            stats = m.group(1)
            print(("Sample Stats from "
                   "'https://select-statistics.co.uk/calculators/sample-size-calculator-population-proportion/':"))
            print("    ", stats)

    foreach_message_in(file, consumer)

    if include_params_details:
        print("Parameter Details:")
        values = sorted(op_mapping_params.keys())
        for v in values:
            l = op_mapping_params[v]
            if len(l) == 0:
                continue
            i = l[0]
            print("    ", "#:", v + ",", "Operation:", i[2] + ",", "Total:", len(l))
            for item in sorted(l, key=lambda x: ".".join(x[0])):
                print("        ", "Parameter:", ".".join(item[0]) + ",", "Type:", item[1])


def parse_getting_args_line(message):
    m = re.match(r"[\w\s]+Method=([\w_\d]+),\s\w+=(.*),\sType=_(.*)$", message)
    op = m.group(1)
    chain = m.group(2)
    dt = m.group(3)

    chain = ast.literal_eval(chain)
    chain = [x for x in chain if '.' not in x]
    chain = '.'.join(chain)

    return op, chain, dt


def print_we_faults_stats(file, ignore_states, show_buffer=True, buffer_words=[], expected_state=None):
    counter = 0
    fault_map = {}
    fault_parameter_map = {}
    last_fault = ''
    last_state = ''
    last_parameter = ''
    flag_last_state = False
    flag_timeout = False
    last_message = ''
    temp_buffer = []
    flag_buffer = False
    fault_mem = None

    def consumer(message, buffer):
        nonlocal counter
        nonlocal last_fault
        nonlocal fault_map
        nonlocal last_state
        nonlocal flag_last_state
        nonlocal flag_timeout
        nonlocal last_parameter
        nonlocal last_message
        nonlocal temp_buffer
        nonlocal flag_buffer
        nonlocal fault_mem

        if message.startswith('Running inputs'):
            print('')
            if fault_mem:
                print('        ', "Code: %s, Message: %s, Details: %s" % (fault_mem[0], fault_mem[1], fault_mem[2]))

            if flag_buffer:
                buffer.reverse()
                for buffer_item in buffer:
                    if buffer_item == last_message:
                        break
                    temp_buffer.append(buffer_item)
                buffer.reverse()

            if len(temp_buffer) > 0:
                temp_buffer.reverse()

                buffer_pattern = r"^\w{3}\s+\d+.*$"

                if show_buffer:
                    print("        ", "-- BEGIN OF SYSTEM LOGS --")
                    for buffer_item in temp_buffer:
                        if re.match(buffer_pattern, buffer_item):
                            print("        ", buffer_item, end='')
                    print("        ", "-- END OF SYSTEM LOGS --")
                if len(buffer_words) > 0:
                    print("        ", "-- BEGIN OF SYSTEM BUFFER WORDS LOGS --")
                    for buffer_item in temp_buffer:
                        if re.match(buffer_pattern, buffer_item):
                            if any(log_level in buffer_item for log_level in buffer_words):
                                print("        ", buffer_item, end='')
                    print("        ", "-- END OF SYSTEM BUFFER WORDS LOGS --")
            else:
                print("        ", "-- BUFFER WAS EMPTY --")

            temp_buffer = []
            flag_buffer = False
            counter += 1
            last_state = ''
            flag_last_state = False
            flag_timeout = False
            last_message = message
            fault_mem = None
        elif message.startswith('Getting args value'):
            op, chain, dt = parse_getting_args_line(message)

            print("    ", counter, op, chain, dt.upper(), '', end='')

            last_parameter = op + ' ' + chain
        elif message.startswith('Got mutation'):
            m = re.match(r"\w+\s\w+\s.([\w_]+).$", message)
            ft = m.group(1)
            print(ft, '', end='')
            last_fault = ft
        elif message.startswith('Wait timeout'):
            m = re.match(r"\w+\s\w+.*elapsed\s(\d+)s.*timeout\s(\d+)s", message)
            elapsed = m.group(1)
            timeout = m.group(2)
            print("TIMEOUT(%s,%s) " % (elapsed, timeout), end='')
            flag_timeout = True
            flag_buffer = True
        elif message.startswith('Wait update'):
            m = re.match(r"\w+\s\w+.*status\s(.*)$", message)
            last_state = m.group(1)
        elif message.startswith('Created resources deleted'):
            if not flag_last_state:
                print(last_state, end='')
                flag_last_state = True
                if last_state.lower() not in ignore_states and flag_timeout:
                    key = "%s %s" % (last_state, last_fault)
                    if key not in fault_map:
                        fault_map[key] = 0
                    fault_map[key] += 1
                    if last_parameter not in fault_parameter_map:
                        fault_parameter_map[last_parameter] = 0
                    fault_parameter_map[last_parameter] += 1
                # Expected State?
                if expected_state and last_state != expected_state:
                    flag_buffer = True
        elif message.startswith("{'message': "):
            fault_obj = ast.literal_eval(message)
            fault_msg = fault_obj['message']
            fault_code = fault_obj['code']
            fault_details = fault_obj['details']
            fault_mem = (fault_code, fault_msg, fault_details)

    print('Stats of Injections:', end='')
    foreach_message_in(file, consumer)

    print('')
    print('Just Successful Injections by Fault (Total=%d):' % sum([fault_map[x] for x in fault_map]))
    for key in sorted(fault_map.keys()):
        print("    ", key, fault_map[key])
    print('Just Successful Injections by Parameter (Total=%d):'
          % len(fault_parameter_map.keys()))
    for key in sorted(fault_parameter_map.keys()):
        print("    ", key, fault_parameter_map[key])


def parse_test_logger_time(control):
    sdate = re.match(r"^\w+\s+(\d{2,4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}).*", control).group(1)
    return datetime.strptime(sdate, '%Y-%m-%d %H:%M:%S')


class CsvForRline(object):
    def __init__(self):
        self.transition_ID = None
        self.fault_ID = None
        self.message_ID = None
        self.param_ID = None
        self.test_time = None
        self.mutation_time = None
        self.number_of_error_logs = None
        self.number_of_warning_logs = None
        self.number_of_exercised_status_before_fault = None
        self.number_of_input_events_before_fault = None
        self.number_of_messages_for_test = None
        self.user_message_status = None
        self.last_status_before_termination = None
        self.test_status = None
        self.param_type = None
        self.statuses_before_termination = []

    @staticmethod
    def get_headers():
        headers = [
            "transition_ID",
            "message_ID",
            "param_ID",
            "param_type",
            "fault_ID",
            "test_time",
            "mutation_time",
            "NEL",
            "NWL",
            "NESF",
            "NIEF",
            "NMT",
            "user_status",
            "LST",
            "test_status",
            "statuses"
        ]

        return ",".join([str(x) for x in headers])

    def __repr__(self):
        items = [
            self.transition_ID,
            self.message_ID,
            self.param_ID,
            self.param_type,
            self.fault_ID,
            int(self.test_time) if self.test_time else 0,
            int(self.mutation_time) if self.mutation_time else 0,
            self.number_of_error_logs if self.number_of_error_logs else 0,
            self.number_of_warning_logs if self.number_of_warning_logs else 0,
            self.number_of_exercised_status_before_fault if self.number_of_exercised_status_before_fault else 0,
            self.number_of_input_events_before_fault if self.number_of_input_events_before_fault else 0,
            self.number_of_messages_for_test if self.number_of_messages_for_test else 0,
            self.user_message_status,
            self.last_status_before_termination,
            self.test_status,
            " ".join(self.statuses_before_termination)
        ]

        return ",".join([str(x) for x in items])


def print_csv_for_r_program(files, transition_ids, csv_file):
    start_time = None
    mutation_start_time = None
    csv_line_object = None
    csv_lines = []

    for file, transition_id in zip(files, transition_ids):
        print("Working with", file)

        def consumer(message, buffer, control):
            nonlocal start_time
            nonlocal csv_line_object
            nonlocal mutation_start_time

            def calculate_mutation_time(control):
                mutation_end_time = parse_test_logger_time(control)
                return (mutation_end_time - mutation_start_time).total_seconds()

            if message.startswith("Running inputs"):
                # this is the first message for a test
                # - restart the buffer
                buffer.clear()
                start_time = parse_test_logger_time(control)
                # creation of CSV line
                csv_line_object = CsvForRline()
                csv_line_object.transition_ID = transition_id
                csv_line_object.number_of_input_events_before_fault = 0
                csv_line_object.number_of_exercised_status_before_fault = 0
                csv_line_object.number_of_messages_for_test = 0
                csv_line_object.last_status_before_termination = "unknown"
                csv_line_object.user_message_status = "NORMAL"
                csv_line_object.test_status = "PASS"
                csv_lines.append(csv_line_object)
                mutation_start_time = None
            if csv_line_object:
                if message.startswith("Run Name="):
                    # this message carries the event name
                    # NIEF
                    csv_line_object.number_of_input_events_before_fault += 1
                    if mutation_start_time:
                        csv_line_object.mutation_time = calculate_mutation_time(control)
                        mutation_start_time = None
                if message.startswith("Wait update"):
                    # this updates the status of the request
                    # examples: scheduling, deleting
                    # LSBT=last status before termination (in the doc)
                    # TODO: it needs to have a way of getting the last source and destination state for the fault
                    csv_line_object.last_status_before_termination = re.match(r".*status\s+(.*$)", message).group(1)
                    csv_line_object.statuses_before_termination.append(csv_line_object.last_status_before_termination)
                    # NESF
                    csv_line_object.number_of_exercised_status_before_fault += 1
                if message.startswith("CPU="):
                    pass
                if message.startswith("Got mutation"):
                    mutation = re.match(r"Got mutation (.*$)", message).group(1)
                    mutation = mutation[1:len(mutation)-1]
                    csv_line_object.fault_ID = mutation
                    mutation_start_time = parse_test_logger_time(control)
                if message.startswith("Getting args value for"):
                    op, chain, dt = parse_getting_args_line(message)
                    csv_line_object.message_ID = op
                    csv_line_object.param_ID = chain
                    csv_line_object.param_type = dt
                if message.startswith("Param Method"):
                    # we can count for the number of messages in the test here
                    # pattern: Param Method=<expected_method>, Message method=<observed_method>
                    # NMT=number of messages for test (in the doc)
                    csv_line_object.number_of_messages_for_test += 1
                if message.startswith("{'message': "):
                    csv_line_object.user_message_status = "FAULT"
                if message.startswith("Wait timeout"):
                    csv_line_object.test_status = "FAIL"
                    if mutation_start_time:
                        csv_line_object.mutation_time = calculate_mutation_time(control)
                        mutation_start_time = None
                if message.startswith("Created resources deleted"):
                    # the end of the test
                    end_time = parse_test_logger_time(control)
                    csv_line_object.test_time = (end_time - start_time).total_seconds()
                    csv_line_object.number_of_error_logs = len([x for x in buffer if "error" in x.lower()])
                    csv_line_object.number_of_warning_logs = len([x for x in buffer if "warning" in x.lower()])
                    print(repr(csv_line_object))

                    csv_line_object = None

        foreach_message_in(file, consumer, buffer_len=25000, stop_on_fail=False)

    print("Writing CSV file in", csv_file)
    with open(csv_file, 'w') as csv_stream:
        csv_stream.write(CsvForRline.get_headers())
        csv_stream.write("\n")
        for csv_line in csv_lines:
            csv_stream.write(repr(csv_line))
            csv_stream.write("\n")


def beautify_csv_for_r(original, modified, legend_path):
    yaml = YAML()
    legend = yaml.load(Path(legend_path))

    original_counter = 0
    modified_counter = 0
    with open(original, mode='r') as original_csv, open(modified, mode='w') as modified_csv:
        original_reader = csv.DictReader(original_csv)
        modified_writer = csv.writer(modified_csv, delimiter=',')
        for row in original_reader:
            if original_counter > 0:
                modified_row = []
                modified_header = []
                for key, value in row.items():
                    if key == "transition_ID":
                        if any(value == x['name'] for x in legend['transitions']):
                            sel = [x for x in legend['transitions'] if x['name'] == value][0]
                            modified_row.append(sel['source'])
                            modified_row.append(sel['command'])
                            modified_row.append(sel['destination'])
                            modified_header.append("Ss")
                            modified_header.append("CMD")
                            modified_header.append("Sd")
                        else:
                            raise ValueError('transition_ID not found for %s.' % value)
                    elif key == "statuses":
                        valid = [[z for z in legend['states'] if z['original'] == x][0]['modeled'] for x in value.split(' ') if any(y['original'] == x for y in legend['states'])]
                        modified_header.append('LSF')
                        modified_row.append(valid[len(valid) - 1])
                    elif key == "LST":
                        pass
                    elif key == "user_status":
                        if value == "NORMAL":
                            modified_row.append("200")
                        elif value == "FAULT":
                            modified_row.append("500")
                        modified_header.append("http_code")
                    else:
                        modified_row.append(value)
                        modified_header.append(key)
                if modified_counter == 1:
                    modified_writer.writerow(modified_header)
                modified_writer.writerow(modified_row)
            original_counter += 1
            modified_counter += 1


if __name__ == '__main__':
    def func_print_we_faults_stats(args):
        print_we_faults_stats(args.file, args.ignore_states,
                              args.show_buffer or len(args.buffer_words) > 0,
                              args.buffer_words, expected_state=args.expected_state)

    def func_print_ef_log_by_sample_stats(args):
        print_ef_log_by_sample_stats(args.file, include_params_details=args.include_details)

    def func_print_ef_log_by_states(args):
        print_ef_log_by_states(args.file)

    def func_print_csv_for_r_program(args):
        print_csv_for_r_program(args.files, args.trans, args.csv_file)

    def func_beautify_csv(args):
        beautify_csv_for_r(args.original, args.modified, args.legend)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_we_faults_stats = subparsers.add_parser("we_faults_stats")
    parser_we_faults_stats.add_argument("file", type=str)
    parser_we_faults_stats.add_argument("--ignore-states", nargs="*", type=str, default=[])
    parser_we_faults_stats.add_argument("--buffer-words", nargs="*", type=str, default=[])
    parser_we_faults_stats.add_argument("--show-buffer", action="store_true")
    parser_we_faults_stats.add_argument("--expected-state", type=str, default=None)
    parser_we_faults_stats.set_defaults(func=func_print_we_faults_stats)

    parser_ef_log_by_sample = subparsers.add_parser("ef_by_sample")
    parser_ef_log_by_sample.add_argument("file", type=str)
    parser_ef_log_by_sample.add_argument("--include-details", action="store_true")
    parser_ef_log_by_sample.set_defaults(func=func_print_ef_log_by_sample_stats)

    parser_ef_by_faults = subparsers.add_parser("ef_by_faults")
    parser_ef_by_faults.add_argument("file")
    parser_ef_by_faults.set_defaults(func=func_print_ef_log_by_states)

    parser_we_csv = subparsers.add_parser("we_csv")
    parser_we_csv.add_argument("csv_file", type=str)
    parser_we_csv.add_argument("--files", type=str, nargs="*")
    parser_we_csv.add_argument("--trans", type=str, nargs="*")
    parser_we_csv.set_defaults(func=func_print_csv_for_r_program)

    parser_cute_csv = subparsers.add_parser("cute_csv")
    parser_cute_csv.add_argument("original", type=str)
    parser_cute_csv.add_argument("modified", type=str)
    parser_cute_csv.add_argument("legend", type=str)
    parser_cute_csv.set_defaults(func=func_beautify_csv)

    args = parser.parse_args()
    print('CMD: ', sys.argv)
    args.func(args)
