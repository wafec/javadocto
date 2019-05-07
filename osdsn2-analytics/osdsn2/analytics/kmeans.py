

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
    print("n_clusters max is", int(len(x) / 2.0))
    for n_clusters in range(2, int(len(x) / 2.0)):
        with warnings.catch_warnings():
            try:
                kmeans = KMeans(n_clusters=n_clusters, random_state=10)
                cluster_labels = kmeans.fit_predict(X)
                silhouette_avg = silhouette_score(X, cluster_labels)
                print("For n_clusters =", n_clusters,
                      "The average silhouette_score is :", silhouette_avg)
            except ConvergenceWarning:
                print("For n_clusters =", n_clusters, "no convergence")


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
