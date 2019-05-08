from osdsn2.analytics import patterns
import re
import argparse
import json
from munch import munchify
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import stringdist
import statistics
import os
import shutil
import csv
import nltk
from datasketch import MinHash
import datetime
import multiprocessing
import math
import sys
import random


INCLUDE_MASK = False
OPENSTACK_SERVICES_COMMON_NAMES = [
    'devstack', 'nova', 'compute', 'neutron', 'glance', 'cinder', 'keystone'
]
REMOTES = [
   '127.0.0.1',
    #'192.168.0.28'
]
TESTER_INCLUDE=True


def _removal_of_unnecessary_info(line, my_patterns):
    for i in range(0, len(my_patterns)):
        results = re.finditer(my_patterns[i], line)
        minus = 0
        for m in sorted(results, key=lambda _m: _m.start('del')):
            line = line[:m.start('del') - minus] + line[m.end('del') - minus:]
            minus += (m.end('del') - m.start('del'))
    return line


def remove_unnecessary_info(line):
    my_patterns = []
    my_patterns += patterns.DATE_PATTERNS
    my_patterns += patterns.PROC_PATTERNS + patterns.REQUEST_PATTERNS
    my_patterns += patterns.NOISE_PATTERNS
    my_patterns += patterns.ID_PATTERNS
    return _removal_of_unnecessary_info(line, my_patterns)


def _get_just_proc_name(proc):
    m = re.match(r'^(?P<name>[\w\.@-]+)(\[\d+\])?$', proc.strip())
    if not m:
        return None
    name = m.group('name')
    if [x for x in OPENSTACK_SERVICES_COMMON_NAMES if x in name]:
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
            if log.type != 'TcTraceLog':
                continue
            for line in log.log_lines:
                line = remove_unnecessary_info(line)
                processes_aux[process_name_x].append(line)
    if TESTER_INCLUDE:
        processes_aux['tester'] = []
        for log in event.tester:
            if log.type != 'TcTraceLog':
                continue
            for line in log.log_lines:
                line = remove_unnecessary_info(line)
                processes_aux['tester'].append(line)
    return processes_aux


def split_in(n, items):
    chunks = [[] for _ in range(0, n)]
    for i in range(0, len(items)):
        chunk_i = i % n
        chunks[chunk_i].append(items[i])
    assert(len(chunks) >= n)
    assert(len([x for sublist in chunks for x in sublist]) == len(items))
    return chunks


def get_lines_per_proc(data):
    processes = {}
    for event in data:
        processes_aux = _get_lines_per_proc_parallel(munchify(json.loads(json.dumps(event))))
        for process_name in processes_aux:
            if process_name not in processes:
                processes[process_name] = []
            processes[process_name] += processes_aux[process_name]
    return processes


def _generate_result_json_files_parallel(items):
    for item in items:
        item_path = item
        if os.path.isfile(item_path) and item.endswith('.json'):
            print('Generating for', item_path)
            data = FileHelper(item_path).munch
            processes = get_lines_per_proc(data)
            destination_dir = os.path.join(os.path.dirname(item_path), "results")
            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)
            destination_path = re.sub(r'\.json$', '.result.json', os.path.basename(item_path))
            with open(os.path.join(destination_dir, destination_path), mode='w', encoding='utf-8') as writer:
                json.dump(processes, writer, indent=4, sort_keys=False)


def generate_result_json_files(source_dir):
    if os.path.isdir(source_dir):
        workers = multiprocessing.cpu_count()
        with ProcessPoolExecutor(max_workers=workers) as executor:
            file_list = [os.path.join(source_dir, f) for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
            chuncks = split_in(workers, file_list)
            for chunck in chuncks:
                executor.submit(_generate_result_json_files_parallel, chunck)


def print_lines_for_manual_examination(data, out):
    processes = get_lines_per_proc(data)
    with open(out, 'w') as writer:
        for proc in processes:
            for line in processes[proc]:
                writer.write("%-35s %s" % (proc, line))
                writer.write('\n')


def compare_processes(processes_a, processes_b, compare_function):
    date_start = datetime.datetime.now()
    all_processes_names = list(set(list(processes_a.keys()) + list(processes_b.keys())))
    result = {}
    sizes = []
    for process_name in all_processes_names:
        value_a = processes_a[process_name] if process_name in processes_a else ""
        value_b = processes_b[process_name] if process_name in processes_b else ""
        value_a = _to_str_for_distance_calculation(value_a)
        value_b = _to_str_for_distance_calculation(value_b)
        sizes.append(len(value_a))
        sizes.append(len(value_b))
        result[process_name] = compare_function(value_a, value_b)
    if not sizes:
        sizes.append(0)
    return result, statistics.mean(sizes), datetime.datetime.now() - date_start


def _to_str_for_distance_calculation(value):
    if value is None:
        return ''
    if not isinstance(value, str):
        if isinstance(value, list):
            return " ".join(value)
        return str(value)
    return value


def compare_with_levenshtein_distance(value_a, value_b):
    str_a = 'a' + _to_str_for_distance_calculation(value_a)
    str_b = 'a' + _to_str_for_distance_calculation(value_b)
    try:
        value = stringdist.levenshtein_norm(str_a, str_b)
        return value
    except Exception as exc:
        print(str_a, str_b)
        raise exc


def compare_with_minhash(value_a, value_b):
    str_a = _to_str_for_distance_calculation(value_a)
    str_b = _to_str_for_distance_calculation(value_b)
    try:
        tokens_a = nltk.word_tokenize(str_a)
        tokens_b = nltk.word_tokenize(str_b)
        m1, m2 = MinHash(), MinHash()
        for d in tokens_a:
            m1.update(d.encode('utf8'))
        for d in tokens_b:
            m2.update(d.encode('utf8'))
        value = m1.jaccard(m2)
        return value
    except Exception as exc:
        print(str_a, str_b)
        raise exc


DISTANCE_FUNCTIONS = {
    'levenshtein': compare_with_levenshtein_distance,
    'minhash': compare_with_minhash
}


def _build_distance_matrix_parallel(i, j, content_of_file_i, content_of_file_j, alg_exec):
    result, size_mean, time_delta = compare_processes(content_of_file_i, content_of_file_j, alg_exec)
    return i, j, result, size_mean, time_delta


class RecordsProxy(object):
    def __init__(self, records):
        self._records = records

    def __getattr__(self, item):
        if item == 'counter':
            return self._records[1]
        if item == 'total':
            return self._records[0]
        if item == 'date_start':
            return self._records[2]
        return super(RecordsProxy, self).__getattribute__(item)

    def __setattr__(self, key, value):
        if key == 'counter':
            self._records[1] = value
        elif key == 'total':
            self._records[0] = value
        elif key == 'date_start':
            self._records[2] = value
        super(RecordsProxy, self).__setattr__(key, value)


def _build_distance_matrix_parallel_by_chunk(chunk, files, alg_exec, records, results, counter):
    records_proxy = RecordsProxy(records)
    matrix_list = []
    for i, j in random.sample(chunk, len(chunk)):
        file_helper_of_i = FileHelper(files[i])
        content_of_file_i = file_helper_of_i.munch
        file_helper_of_j = FileHelper(files[j])
        content_of_file_j = file_helper_of_j.munch
        result = _build_distance_matrix_parallel(i, j, content_of_file_i,
                                                 content_of_file_j, alg_exec)
        _build_distance_matrix_consume(result, matrix_list)
        with counter.get_lock():
            counter.value += 1
            _calc_estimated_time_arrival(records_proxy.date_start, records_proxy.total, counter.value,
                                         result[4], result[3])
    results.append(matrix_list)


def _build_distance_matrix_consume(result, matrix_list):
    ix, jx, result, size_mean, time_delta = result
    matrix_list.append((ix, jx, result))


def _calc_estimated_time_arrival(date_start, total, counter, time_delta, size_mean):
    spent = (datetime.datetime.now() - date_start).total_seconds()
    x = (total * spent) / counter
    estimated = date_start + datetime.timedelta(0, x)
    sys.stdout.write('\rProgress in ' + '%06d/%06d ' % (counter, total) + estimated.strftime('%b %d %H:%M:%S') +
                     ' Size(u)=%06d Time(s)=%s' % (size_mean, time_delta))


def build_distance_matrix(files, alg):
    alg_exec = compare_with_levenshtein_distance if alg not in DISTANCE_FUNCTIONS else DISTANCE_FUNCTIONS[alg]
    matrix = [[None for _ in range(len(files))] for _ in range(len(files))]
    print('Matrix ', f'{len(files)}x{len(files)}')
    print('We have', multiprocessing.cpu_count(), 'cpus')
    cpus = int(1 * multiprocessing.cpu_count())
    print('Working with', cpus, 'local cpus')

    processing_list = []
    for i in range(0, len(files)):
        for j in range(i + 1, len(files)):
            processing_list.append((i, j))
    chunks = split_in(cpus, processing_list)
    local_chunks = chunks

    total = sum([len([i for i in range(j, len(files))]) for j in range(len(files))])
    counter = 0
    date_start = datetime.datetime.now()
    print('Begin at', date_start.strftime('%b %d %H:%M:%S'))

    with multiprocessing.Manager() as manager:
        records = manager.list([total, counter, date_start])
        results = manager.list([])
        counter = multiprocessing.Value('i', 0)
        processes = []
        for chunk in local_chunks:
            p = multiprocessing.Process(target=_build_distance_matrix_parallel_by_chunk, args=(chunk, files, alg_exec,
                                                                                               records, results,
                                                                                               counter))
            processes.append(p)
            p.start()
        for p in processes:
            p.join()
        for result_c in results:
            for ix, jx, result in result_c:
                matrix[ix][jx] = result
                matrix[jx][ix] = result
    print()
    print('End at', datetime.datetime.now().strftime('%b %d %H:%M:%S'))
    return matrix


def prepare_distance_matrix_results(distance_matrix, reverse=False):
    columns_names = []
    for i in range(len(distance_matrix)):
        names = []
        for j in range(len(distance_matrix)):
            result = distance_matrix[j][i]
            names += result.keys() if result is not None else []
        names = list(set(names))
        columns_names.append(['%03d_%s' % (len(columns_names), name) for name in names])
        for j in range(len(distance_matrix)):
            values = []
            result = distance_matrix[j][i]
            for name in names:
                if result is not None and name in result:
                    values.append(result[name] if reverse is False else 1.0 - result[name])
                else:
                    values.append(1.0)
            distance_matrix[j][i] = values
    return distance_matrix, [item for sublist in columns_names for item in sublist]


class CsvItemWrapper(object):
    def __init__(self, value, indentation):
        self._indentation = indentation
        self._value = value

    def __str__(self):
        return f'%{self._indentation}.04f' % self._value


def _save_matrix_as_csv(matrix, columns_names, output_file):
    with open(output_file, 'w', newline='') as csvwriter:
        writer = csv.DictWriter(csvwriter, fieldnames=columns_names)
        writer.writeheader()
        for row in matrix:
            row_dict = {}
            for i in range(0, len(columns_names)):
                row_dict[columns_names[i]] = CsvItemWrapper(row[i], len(columns_names[i]))
            writer.writerow(row_dict)


def _isReverseAlg(algorithm):
    if algorithm == 'levenshtein':
        return True
    return False


def build_matrix_flow(source_dir, output_file, algorithm):
    if os.path.isdir(source_dir):
        files = [os.path.join(source_dir, x) for x in os.listdir(source_dir) if x.endswith('.result.json')]
        files = [x for x in files if os.path.isfile(x)]
        print('Building distance matrix...')
        distance_matrix = build_distance_matrix(files, algorithm)
        print('Preparing distance matrix results...')
        distance_matrix, columns_names = prepare_distance_matrix_results(distance_matrix,
                                                                         reverse=_isReverseAlg(algorithm))
        print('Preparing 2-dimensional distance matrix...')
        distance_matrix, columns_statuses = prepare_2_dimensional_distance_matrix(distance_matrix)
        columns_names_aux = []
        for i, column_status in zip(range(0, len(columns_statuses)), columns_statuses):
            if not columns_statuses[i]:
                columns_names_aux.append(columns_names[i])
        print('Saving as CSV...')
        _save_matrix_as_csv(distance_matrix, columns_names_aux, output_file)


def prepare_2_dimensional_distance_matrix(distance_matrix):
    matrix = [[] for _ in range(0, len(distance_matrix))]
    for i in range(len(distance_matrix)):
        for j in range(len(distance_matrix)):
            for k in range(len(distance_matrix[i][j])):
                matrix[i].append(distance_matrix[i][j][k])
    columns_statuses = [False for _ in range(len(matrix[0]))]
    for i in range(len(matrix[0])):
        distinct_values = []
        for j in range(len(matrix)):
            distinct_values.append(matrix[j][i])
        distinct_values = list(set(distinct_values))
        columns_statuses[i] = len(distinct_values) == 1 and distinct_values[0] == 1.0
    for i in range(len(matrix)):
        dels = 0
        for j in range(len(matrix[i])):
            if columns_statuses[j]:
                del matrix[i][j - dels]
                dels += 1
    return matrix, columns_statuses


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
    matrix.add_argument('--algorithm', type=str, default='minhash', choices=[
        'minhash', 'levenshtein'
    ])
    matrix.set_defaults(callback=lambda _a: build_matrix_flow(_a.source_dir, _a.output_file, _a.algorithm))

    a = parser.parse_args()
    a.callback(a)