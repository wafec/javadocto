import re

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.exceptions import ConvergenceWarning

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import csv
import argparse
import warnings
import itertools
import operator

from concurrent.futures import ThreadPoolExecutor
import logging
import os
import shutil

from osdsn2.analytics.utils import TimingLogger
from osdsn2.analytics.utils import TimingLogger

from osdsn2.analytics import mining

from pyclustering.cluster.silhouette import silhouette_ksearch, silhouette_ksearch_type
from pyclustering.cluster.kmedoids import kmedoids

import random


def read_matrix(file):
    matrix = []
    with open(file, 'r') as reader:
        dict_reader = csv.DictReader(reader)
        for row in dict_reader:
            matrix_row = []
            for name in dict_reader.fieldnames:
                matrix_row.append(float(row[name].strip()))
            matrix.append(matrix_row)
    return matrix


def use_experiment_with_kmeans(file):
    TimingLogger.start('kmeans', 'kmeans')
    x = read_matrix(file)
    X = np.array(x)
    logging.info("n_clusters max is " + str(len(x)))
    warnings_counting = 0
    scores = []
    for n_clusters in range(2, len(x)):
        if warnings_counting > 20:
            break
        with warnings.catch_warnings():
            warnings.filterwarnings('error')
            try:
                kmeans = KMeans(n_clusters=n_clusters, random_state=10)
                cluster_labels = kmeans.fit_predict(X)
                silhouette_avg = silhouette_score(X, cluster_labels)
                logging.info("For n_clusters = " + str(n_clusters) +
                             " The average silhouette_score is : " + str(silhouette_avg))
                scores.append((n_clusters, silhouette_avg))
            except ConvergenceWarning:
                logging.warning("For n_clusters = " + str(n_clusters) + " no convergence")
                warnings_counting += 1
    if len(scores) > 0:
        logging.info('Better choice is ' + str(sorted(scores, key=lambda p: p[1], reverse=True)[0][0]) + ' clusters')
    TimingLogger.stop('kmeans')


def use_experiment_with_pyclustering_kmedoids(file):
    TimingLogger.start('pyclustering.kmedoids', 'kmedoids')
    x = read_matrix(file)
    X = np.array(x)
    clusters = len(x)
    search_instance = silhouette_ksearch(X, 2, clusters, algorithm=silhouette_ksearch_type.KMEDOIDS).process()
    scores = search_instance.get_scores()
    for i in range(2, len(scores)):
        logging.info('For n_clusters = ' + str(i) +
                     ' The average silhouette_score is : ' + str(scores[i - 2]))
    logging.info('Better choice is ' + str(search_instance.get_amount()) + ' clusters')
    TimingLogger.stop('pyclustering.kmedoids')


def use_kmedoids(file, n_clusters, source, destination):
    TimingLogger.start('konly.kmedoids', 'konly')
    x = read_matrix(file)
    X = np.array(x)
    initial_medoids = random.sample(range(0, len(x)), n_clusters)
    kmedoids_instance = kmedoids(X, initial_medoids)
    kmedoids_instance.process()
    clusters = kmedoids_instance.get_clusters()
    cluster_labels = [None for _ in range(0, len(x))]
    cluster_index = 0
    for cluster in clusters:
        for i in cluster:
            cluster_labels[int(i)] = cluster_index
        cluster_index += 1
    _copy_clusters(cluster_labels, source, destination)
    TimingLogger.stop('konly.kmedoids')


def use_kmeans(file, n_clusters, source, destination):
    TimingLogger.start('konly', 'konly')
    print('Entered with', file, n_clusters, source, destination)
    if not os.path.isdir(source) or not os.path.isdir(destination):
        raise ValueError('source and destination need to be dir')
    x = read_matrix(file)
    X = np.array(x)
    kmeans = KMeans(n_clusters=n_clusters, random_state=10)
    cluster_labels = kmeans.fit_predict(X)
    _copy_clusters(cluster_labels, source, destination)
    TimingLogger.stop('konly')


def _copy_clusters(cluster_labels, source, destination):
    results = [x for x in zip(range(0, len(cluster_labels)), cluster_labels)]
    it = itertools.groupby(sorted(results, key=lambda r: r[1]), operator.itemgetter(1))
    source_files = [os.path.join(source, x) for x in os.listdir(source) if os.path.isfile(os.path.join(source, x))
                    and x.endswith('.result.json')]
    for key, subiter in it:
        for item in subiter:
            source_file = source_files[item[0]]
            if not os.path.exists(os.path.join(destination, str(key))):
                os.makedirs(os.path.join(destination, str(key)))
            shutil.copyfile(source_file,
                            os.path.join(os.path.join(destination, str(key)), os.path.basename(source_file)))
            print('%03d' % key, item[0], 'copied successfully')


def get_better_choice(filename):
    if not filename:
        print('Better choice filename is None')
        return None
    with open(filename, 'r', encoding='iso-8859-1') as reader:
        line = reader.readline()
        while line:
            m = re.match(r'^.*Better choice is (?P<choice>\d+) clusters.*$', line)
            if m:
                return int(m.group('choice'))
            line = reader.readline()
    raise ValueError('Better choice not found.')


def _value_or_default(value, default):
    if value:
        return value
    return default


def check_groups(destination, grouped):
    hashes = [x for x in os.listdir(grouped) if os.path.isdir(os.path.join(grouped, x))]
    path_resolution = mining.PathResolution([])
    for k in [os.path.join(destination, x) for x in os.listdir(destination) if
              os.path.isdir(os.path.join(destination, x))]:
        for file in [os.path.join(k, x) for x in os.listdir(k) if os.path.isfile(os.path.join(k, x))]:
            path_resolution.add_file(file)
            if path_resolution.get_hash(file) in hashes:
                grouped_folder = os.path.join(grouped, path_resolution.get_hash(file))
                grouped_files = [os.path.join(grouped_folder, x) for x in os.listdir(grouped_folder)]
                for grouped_file in grouped_files:
                    shutil.copyfile(grouped_file, os.path.join(k, os.path.basename(grouped_file)))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('kmeans.log', 'a'), logging.StreamHandler()],
                        format='%(asctime)s %(message)s')

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()

    k = sub.add_parser('gk')
    k.add_argument('file')

    k_sub = k.add_subparsers()

    k_kmeans = k_sub.add_parser('kmeans')
    k_kmeans.set_defaults(callback=lambda _a: use_experiment_with_kmeans(_a.file))

    k_kmedoids = k_sub.add_parser('kmedoids')
    k_kmedoids.set_defaults(callback=lambda _a: use_experiment_with_pyclustering_kmedoids(_a.file))

    konly = sub.add_parser('process')
    konly.add_argument('file')
    konly.add_argument('n_clusters', type=int)
    konly.add_argument('source', type=str)
    konly.add_argument('destination', type=str)
    konly.add_argument('--better-choice', type=str)

    konly_sub = konly.add_subparsers()

    konly_kmeans = konly_sub.add_parser('kmeans')
    konly.set_defaults(callback=lambda _a: use_kmeans(_a.file, _value_or_default(get_better_choice(_a.better_choice),
                                                                                 _a.n_clusters), _a.source,
                                                      _a.destination))

    konly_kmedoids = konly_sub.add_parser('kmedoids')
    konly_kmedoids.set_defaults(callback=lambda _a: use_kmedoids(_a.file, _value_or_default(get_better_choice(_a.better_choice),
                                                                                   _a.n_clusters), _a.source,
                                                        _a.destination))

    check = sub.add_parser('check')
    check.add_argument('destination', type=str)
    check.add_argument('grouped', type=str)
    check.set_defaults(callback=lambda _a: check_groups(_a.destination, _a.grouped))

    a = parser.parse_args()
    a.callback(a)
