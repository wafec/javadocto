

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
                    except ConvergenceWarning:
                        logging.warning("For n_clusters = " + str(n_clusters) + " no convergence")
                        warnings_counting += 1
            executor.submit(_use_kmeans_per_cluster, n_clusters)


def use_kmeans(file, n_clusters):
    x = read_matrix(file)
    X = np.array(x)
    kmeans = KMeans(n_clusters=n_clusters, random_state=10)
    cluster_labels = kmeans.fit_predict(X)
    results = [x for x in zip(range(0, len(cluster_labels)), cluster_labels)]
    it = itertools.groupby(sorted(results, key=lambda r: r[1]), operator.itemgetter(1))
    for key, subiter in it:
        for item in subiter:
            print('%03d' % key, item[0])


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
    konly.set_defaults(callback=lambda _a: use_kmeans(_a.file, _a.n_clusters))

    a = parser.parse_args()
    a.callback(a)
