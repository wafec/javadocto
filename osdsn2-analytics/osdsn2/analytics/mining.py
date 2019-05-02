from osdsn2.analytics import patterns
import re
import argparse
import json
from munch import munchify
from concurrent.futures import ProcessPoolExecutor
import threading
import stringdist
import statistics
import os
import shutil
import csv


INCLUDE_MASK = False
OPENSTACK_SERVICES_COMMON_NAMES = [
    'devstack', 'nova', 'compute', 'neutron', 'glance', 'cinder', 'keystone'
]


def _removal_of_unnecessary_info(line, my_patterns):
    for i in range(0, len(my_patterns)):
        results = re.finditer(my_patterns[i], line)
        for m in results:
            mask = ""
            if INCLUDE_MASK:
                mask = ("X" * (m.end('del') - m.start('del')))
            line = line[:m.start('del')] + mask + line[m.end('del'):]
    return line


def remove_unnecessary_info(line):
    my_patterns = []
    my_patterns += patterns.DATE_PATTERNS + patterns.PROC_PATTERNS + patterns.REQUEST_PATTERNS
    my_patterns += patterns.NOISE_PATTERNS
    my_patterns += patterns.ID_PATTERNS
    return _removal_of_unnecessary_info(line, my_patterns)


def _get_just_proc_name(proc):
    m = re.match(r'^(?P<name>[\w\.@-]+)(\[\d+\])?$', proc.strip())
    if not m:
        return None
    name = m.group('name')
    if [x for x in OPENSTACK_SERVICES_COMMON_NAMES if x in name]:
        print("%-20s %s" % (threading.current_thread().getName(), name))
        return name
    return None


def _get_lines_per_proc_parallel(event):
    processes_aux = {}
    for process_name in event.logs:
        process_name_x = _get_just_proc_name(process_name)
        if not process_name:
            continue
        if process_name not in processes_aux:
            processes_aux[process_name_x] = []
        for log in event.logs[process_name][process_name]:
            for line in log.log_lines:
                line = remove_unnecessary_info(line)
                processes_aux[process_name_x].append(line)
    return processes_aux


def get_lines_per_proc(data):
    processes = {}
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = []
        for event in data:
            futures.append(executor.submit(_get_lines_per_proc_parallel, munchify(json.loads(json.dumps(event)))))
        for future in futures:
            processes_aux = future.result()
            for process_name in processes_aux:
                if process_name not in processes:
                    processes[process_name] = []
                processes[process_name] += processes_aux[process_name]
    return processes


def generate_result_json_files(source_dir):
    if os.path.isdir(source_dir):
        for item in os.listdir(source_dir):
            item_path = os.path.join(source_dir, item)
            if os.path.isfile(item_path) and item.endswith('.json'):
                data = FileHelper(item_path).munch
                print('Generating for', item_path)
                processes = get_lines_per_proc(data)
                destination_dir = os.path.join(os.path.dirname(item_path), "results")
                if not os.path.exists(destination_dir):
                    os.makedirs(destination_dir)
                destination_path = re.sub(r'\.json$', '.result.json', os.path.basename(item_path))
                with open(os.path.join(destination_dir, destination_path), mode='w', encoding='utf-8') as writer:
                    json.dump(processes, writer, indent=4, sort_keys=False)


def print_lines_for_manual_examination(data, out):
    processes = get_lines_per_proc(data)
    with open(out, 'w') as writer:
        for proc in processes:
            for line in processes[proc]:
                writer.write("%-35s %s" % (proc, line))
                writer.write('\n')


def compare_processes(processes_a, processes_b, compare_function):
    all_processes_names = list(set(list(processes_a.keys()) + list(processes_b.keys())))
    result = {}
    for process_name in all_processes_names:
        value_a = processes_a[process_name] if process_name in processes_a else ""
        value_b = processes_b[process_name] if process_name in processes_b else ""
        result[process_name] = compare_function(value_a, value_b)
    return result


def _to_str_for_levenshtein_distance(value):
    if value is None:
        return ''
    if not isinstance(value, str):
        if isinstance(value, list):
            return "".join(value)
        return str(value)
    return value


def compare_with_levenshtein_distance(value_a, value_b):
    str_a = _to_str_for_levenshtein_distance(value_a)
    str_b = _to_str_for_levenshtein_distance(value_b)
    try:
        value = stringdist.levenshtein_norm(str_a, str_b)
        return value
    except Exception as exc:
        print(str_a, str_b)
        raise exc


def build_distance_matrix(files):
    matrix = [[None for _ in range(len(files))] for _ in range(len(files))]
    i = 0
    progress = 0
    total = sum([len([i for i in range(j, len(files))]) for j in range(len(files))])
    counter = 0.0
    while i < len(files):
        j = i
        file_helper_of_i = FileHelper(files[i])
        content_of_file_i = file_helper_of_i.munch
        while j < len(files):
            file_helper_of_j = FileHelper(files[j])
            content_of_file_j = file_helper_of_j.munch
            result = compare_processes(content_of_file_i, content_of_file_j, compare_with_levenshtein_distance)
            counter += 1
            _progress = counter / total * 100
            print(_progress, progress, total, counter)
            if _progress > progress:
                progress = _progress
                print('Progress in ', ("%-3d" % progress) + '%', end='\r')
            matrix[j][i] = result
            matrix[i][j] = result
            j += 1
            del file_helper_of_j
        del file_helper_of_i
        i += 1
    return matrix


def prepare_distance_matrix_results(distance_matrix):
    for i in range(len(distance_matrix)):
        names = []
        for j in range(len(distance_matrix)):
            result = distance_matrix[j][i]
            names += result.keys()
        names = list(set(names))
        for j in range(len(distance_matrix)):
            values = []
            result = distance_matrix[j][i]
            for name in names:
                if name in result:
                    values.append(result[name])
                else:
                    values.append(1)
            distance_matrix[j][i] = values
    return distance_matrix


def _save_matrix_as_csv(matrix, output_file):
    with open(output_file, 'w', newline='') as csvwriter:
        writer = csv.writer(csvwriter)
        for row in matrix:
            writer.writerow(row)


def build_matrix_flow(source_dir, output_file):
    if os.path.isdir(source_dir):
        files = [os.path.join(source_dir, x) for x in os.listdir(source_dir) if x.endswith('.result.json')]
        files = [x for x in files if os.path.isfile(x)]
        distance_matrix = build_distance_matrix(files)
        distance_matrix = prepare_distance_matrix_results(distance_matrix)
        distance_matrix = prepare_2_dimensional_distance_matrix(distance_matrix)
        _save_matrix_as_csv(distance_matrix, output_file)


def prepare_2_dimensional_distance_matrix(distance_matrix):
    matrix = []
    for i in range(len(distance_matrix)):
        matrix[i] = []
        for j in range(len(distance_matrix)):
            for k in range(len(distance_matrix[i][j])):
                matrix[i].append(distance_matrix[i][j][k])
    return matrix


class FileHelper(object):
    def __init__(self, file_name, mode='r', encoding='utf-8'):
        self._file_ref = open(file_name, mode=mode, encoding=encoding)

    def __del__(self):
        self._file_ref.close()

    @property
    def file(self):
        return self._file_ref

    @property
    def json(self):
        return json.load(self.file)

    @property
    def munch(self):
        return munchify(self.json)


def our_files_together(source_dir, destination_dir):
    source_path = os.path.join(*source_dir)
    if os.path.isdir(source_path):
        for dir_item in os.listdir(source_path):
            dir_item_path = os.path.join(*(source_dir + [dir_item]))
            if os.path.isfile(dir_item_path) and dir_item.endswith('.json'):
                print("Copying", dir_item_path)
                shutil.copyfile(dir_item_path, os.path.join(destination_dir, "___".join(source_dir[1:] + [dir_item])))
            elif os.path.isdir(dir_item_path):
                our_files_together(source_dir + [dir_item], destination_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()

    exam = sub.add_parser('exam')
    exam.add_argument('file', type=str)
    exam.add_argument('out', type=str)
    exam.set_defaults(callback=lambda _a: print_lines_for_manual_examination(FileHelper(_a.file).munch, _a.out))

    together = sub.add_parser('together')
    together.add_argument('source_dir', type=str)
    together.add_argument('destination_dir', type=str)
    together.set_defaults(callback=lambda _a: our_files_together([_a.source_dir], _a.destination_dir))

    results = sub.add_parser('results')
    results.add_argument('source_dir', type=str)
    results.set_defaults(callback=lambda _a: generate_result_json_files(_a.source_dir))

    matrix = sub.add_parser('matrix')
    matrix.add_argument('source_dir', type=str)
    matrix.add_argument('output_file', type=str)
    matrix.set_defaults(callback=lambda _a: build_matrix_flow(_a.source_dir, _a.output_file))

    a = parser.parse_args()
    a.callback(a)