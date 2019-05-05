from osdsn2.analytics import patterns
import re
import argparse
import json
from munch import munchify
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import threading
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
import threading
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy


INCLUDE_MASK = False
OPENSTACK_SERVICES_COMMON_NAMES = [
    'devstack', 'nova', 'compute', 'neutron', 'glance', 'cinder', 'keystone'
]
REMOTES = [
    '192.168.0.28'
]


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
                pass
            for line in log.log_lines:
                line = remove_unnecessary_info(line)
                processes_aux[process_name_x].append(line)
    return processes_aux


def split_in(n, items):
    content = []
    chunck_size = int(math.ceil(len(items) / n))
    chunck = None
    for i in range(0, len(items)):
        if i % chunck_size == 0:
            chunck = []
            content.append(chunck)
        chunck.append(items[i])
    assert(len(content) >= n)
    return content


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
        print('...', end='')
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
    str_a = _to_str_for_distance_calculation(value_a)
    str_b = _to_str_for_distance_calculation(value_b)
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


def _build_distance_matrix_parallel_by_chunk(chunk, files, alg_exec):
    total = sum([len([i for i in range(j, len(files))]) for j in range(len(files))])
    counter = 0
    space = len(str(total))
    mask = f'%{space}d/%{space}d'
    date_start = datetime.datetime.now()
    print('Progress in ', mask % (counter, total), end='')
    matrix_list = []
    for i, j in chunk:
        file_helper_of_i = FileHelper(files[i])
        content_of_file_i = file_helper_of_i.munch
        file_helper_of_j = FileHelper(files[j])
        content_of_file_j = file_helper_of_j.munch
        result = _build_distance_matrix_parallel(i, j, content_of_file_i,
                                                 content_of_file_j, alg_exec)
        _build_distance_matrix_consume(result, matrix_list)
        counter += 1
        _calc_estimated_time_arrival(date_start, total, counter, mask, result[4], result[3])
    print('\nProgress in ', mask % (total, total), datetime.datetime.now().strftime('%b %d %H:%M:%S'))
    return matrix_list


def build_distance_matrix_parallel_by_chunk(chunk, files, alg_exec_name):
    alg_exec = locals()[alg_exec_name]
    print('Remote working now')
    return _build_distance_matrix_parallel_by_chunk(chunk, files, alg_exec)


def _build_distance_matrix_parallel_by_chunk_in_remote(cix, chunk, files, alg_exec_name):
    with ServerProxy(f'http://{REMOTES[cix]}:8000') as proxy:
        return proxy.build_distance_matrix_parallel_by_chunck(chunk, files, alg_exec_name)


def _build_distance_matrix_consume(result, matrix_list):
    ix, jx, result, size_mean, time_delta = result
    matrix_list.append((ix, jx, result))


def _calc_estimated_time_arrival(date_start, total, counter, mask, time_delta, size_mean):
    spent = (datetime.datetime.now() - date_start).total_seconds()
    x = (total * spent) / counter
    estimated = date_start + datetime.timedelta(0, x)
    print('\rProgress in ', mask % (counter, total), estimated.strftime('%b %d %H:%M:%S'),
          'Size(u)=%6d Time(s)=%s' % (size_mean, time_delta), end='')


def how_many_cpus():
    return multiprocessing.cpu_count()


def start_rpc_server():
    server = SimpleXMLRPCServer('localhost', 8000)
    print('Listening on port 8000...')
    server.register_function(how_many_cpus, 'how_many_cpus')
    server.register_function(build_distance_matrix_parallel_by_chunk, 'build_distance_matrix_parallel_by_chunk')
    server.serve_forever()


def _ask_remote_for_cpu_counting():
    cpus = 0
    for remote in REMOTES:
        with ServerProxy(f'http://{remote}:8000') as proxy:
            cpus += proxy.how_many_cpus()
    return cpus


def build_distance_matrix(files, alg):
    alg_exec = compare_with_levenshtein_distance if alg not in DISTANCE_FUNCTIONS else DISTANCE_FUNCTIONS[alg]
    matrix = [[None for _ in range(len(files))] for _ in range(len(files))]
    print('Matrix ', f'{len(files)}x{len(files)}')
    print('We have', multiprocessing.cpu_count(), 'cpus')
    cpus = int(0.95 * multiprocessing.cpu_count())
    remote_cpus = _ask_remote_for_cpu_counting()
    print('Working with', cpus, 'cpus')
    processing_list = []
    for i in range(0, len(files)):
        for j in range(i + 1, len(files)):
            processing_list.append((i, j))
    chunks = split_in(cpus + remote_cpus, processing_list)
    local_chunks = chunks[:cpus]
    remote_chunks = chunks[cpus:]
    with ProcessPoolExecutor(max_workers=cpus + remote_cpus) as executor:
        futures = []
        for chunk in local_chunks:
            future = executor.submit(_build_distance_matrix_parallel_by_chunk, chunk, files, alg_exec)
            futures.append(future)
        for cix, chunk in zip(range(0, remote_cpus), remote_chunks):
            future = executor.submit(_build_distance_matrix_parallel_by_chunk_in_remote, cix, chunk, files,
                                     alg_exec.__name__)
            futures.append(future)
        for future in futures:
            ix, jx, result = future.result()
            matrix[ix][jx] = result
            matrix[jx][ix] = result
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


def build_matrix_flow(source_dir, output_file, algorithm):
    if os.path.isdir(source_dir):
        files = [os.path.join(source_dir, x) for x in os.listdir(source_dir) if x.endswith('.result.json')]
        files = [x for x in files if os.path.isfile(x)]
        distance_matrix = build_distance_matrix(files, algorithm)
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
    matrix.add_argument('--algorithm', type=str, default='minhash')
    matrix.set_defaults(callback=lambda _a: build_matrix_flow(_a.source_dir, _a.output_file, _a.algorithm))

    server = sub.add_parser('server')
    server.set_defaults(callback=lambda _: start_rpc_server())

    a = parser.parse_args()
    a.callback(a)