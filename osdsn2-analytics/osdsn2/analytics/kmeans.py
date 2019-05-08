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
    x = read_matrix(file)
    X = np.array(x)
    logging.info("n_clusters max is " + str((int(len(x) / 2.0))))
    warnings_counting = 0
    scores = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        for n_clusters in range(2, int(len(x) / 2.0)):
            if warnings_counting > 20:
                break

            def _use_kmeans_per_cluster(n_clusters):
                nonlocal warnings_counting
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
            executor.submit(_use_kmeans_per_cluster, n_clusters)
    if len(scores) > 0:
        logging.info('Better choice is ' + str(sorted(scores, key=lambda p: p[1], reverse=True)[0][0]) + ' clusters')


def use_kmeans(file, n_clusters, source, destination):
    if not os.path.isdir(source) or not os.path.isdir(destination):
        raise ValueError('source and destination need to be dir')
    x = read_matrix(file)
    X = np.array(x)
    kmeans = KMeans(n_clusters=n_clusters, random_state=10)
    cluster_labels = kmeans.fit_predict(X)
    results = [x for x in zip(range(0, len(cluster_labels)), cluster_labels)]
    it = itertools.groupby(sorted(results, key=lambda r: r[1]), operator.itemgetter(1))
    source_files = [os.path.join(source, x) for x in os.listdir(source) if os.path.isfile(os.path.join(source, x))
                    and x.endswith('.result.json')]
    for key, subiter in it:
        for item in subiter:
            source_file = source_files[item[0]]
            if not os.path.exists(os.path.join(destination, key)):
                os.makedirs(os.path.join(destination, key))
            shutil.copyfile(source_file, os.path.join(os.path.join(destination, key), os.path.basename(source_file)))
            print('%03d' % key, item[0], 'copied successfully')


def get_better_choice(filename):
    with open(filename, 'w', encoding='iso-8859-1') as reader:
        line = reader.readline()
        while line:
            m = re.match(r'^.*Better choice is (?P<choice>\d+) cluster.*$')
            if m:
                return int(m.group('choice'))
            line = reader.readline()
    return None


def _value_or_default(value, default):
    if value:
        return value
    return default


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('kmeans.log', 'a'), logging.StreamHandler()],
                        format='%(asctime)s %(message)s')

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()

    k = sub.add_parser('kmeans')
    k.add_argument('file')
    k.set_defaults(callback=lambda _a: use_experiment_with_kmeans(_a.file))

    konly = sub.add_parser('konly')
    konly.add_argument('file')
    konly.add_argument('n_clusters', type=int)
    konly.add_argument('source', type=str)
    konly.add_argument('destination', type=str)
    konly.add_argument('--better-choice', type=str)
    konly.set_defaults(callback=lambda _a: use_kmeans(_a.file, _value_or_default(get_better_choice(_a.better_choice),
                                                                                 _a.n_clusters), _a.source,
                                                      _a.destination))

    a = parser.parse_args()
    a.callback(a)
