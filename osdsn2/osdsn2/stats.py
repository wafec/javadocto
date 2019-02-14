import re
import ast
import argparse


EF_LOG_PREFIX_PATTERN = r"(\w+\s*[\d-]+\s[\d:,]+\s.*\s.*\s\d+:\s)(.*$)"


def foreach_message_in(file, consumer):
    with open(file, 'r') as reader:
        for line in reader:
            m = re.match(EF_LOG_PREFIX_PATTERN, line)
            if m:
                consumer(m.group(2))


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


def print_we_faults_stats(file, ignore_states):
    counter = 0
    fault_map = {}
    fault_parameter_map = {}
    last_fault = ''
    last_state = ''
    last_parameter = ''
    flag_last_state = False
    flag_timeout = False

    def consumer(message):
        nonlocal counter
        nonlocal last_fault
        nonlocal fault_map
        nonlocal last_state
        nonlocal flag_last_state
        nonlocal flag_timeout
        nonlocal last_parameter

        if message.startswith('Running inputs'):
            print('')
            counter += 1
            last_state = ''
            flag_last_state = False
            flag_timeout = False
        elif message.startswith('Getting args value'):
            m = re.match(r"[\w\s]+Method=([\w_\d]+),\s\w+=(.*),\sType=_(.*)$", message)
            op = m.group(1)
            chain = m.group(2)
            dt = m.group(3)

            chain = ast.literal_eval(chain)
            chain = [x for x in chain if '.' not in x]
            chain = '.'.join(chain)

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


print_ef_log_by_sample_stats("logs/penv/t_build/EF_2019_01_24_114055.log.1")
# print_we_faults_stats("logs/penv/t_build/we.merged.log.1", ['error'])

if __name__ == '__main__':
    def func_print_we_faults_stats(args):
        print_we_faults_stats(args.file, args.ignore_states)

    def func_print_ef_log_by_sample_stats(args):
        print_ef_log_by_sample_stats(args.file, include_params_details=args.include_details)

    def func_print_ef_log_by_faults_states(args):
        print_ef_log_by_states(args.file)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_we_faults_stats = subparsers.add_parser("we_faults_stats")
    parser_we_faults_stats.add_argument("file", type=str)
    parser_we_faults_stats.add_argument("--ignore-states", nargs="*", type=str)
    parser_we_faults_stats.set_defaults(func=func_print_we_faults_stats)

    parser_ef_log_by_sample = subparsers.add_parser("ef_by_sample")
    parser_ef_log_by_sample.add_argument("file", type=str)
    parser_ef_log_by_sample.add_argument("--include-details", action="store_true")
    parser_ef_log_by_sample.set_defaults(func=func_print_ef_log_by_sample_stats)

    parser_ef_by_faults = subparsers.add_parser("ef_by_faults")
    parser_ef_by_faults.add_argument("file")
    parser_ef_by_faults.set_defaults(func=func_print_ef_log_by_faults_states)

    args = parser.parse_args()
    args.func(args)
