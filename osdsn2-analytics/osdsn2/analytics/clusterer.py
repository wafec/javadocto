import warnings
from sklearn.exceptions import ConvergenceWarning
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import sys
import bisect
import numpy as np
from osdsn2.analytics.utils import UnorderedProgress
import random


class ClustererGeneric(object):
    KMEANS = 0x010
    _WITH_CLUSTERER_MASK = 0x0F0

    @staticmethod
    def ksearch(kmin, kmax, X):
        print('Searching k...', 'Min={}, Max={}'.format(kmin, kmax))
        cn = 0
        cs = -1.0
        wc = 0
        for n_clusters in range(int(kmin), int(kmax)):
            with warnings.catch_warnings():
                warnings.filterwarnings('error')
                try:
                    clusterer = KMeans(n_clusters=n_clusters, random_state=10)
                    cluster_labels = clusterer.fit_predict(X)
                    silhouette_avg = silhouette_score(X, cluster_labels)
                    if silhouette_avg >= cs:
                        cn = n_clusters
                        cs = silhouette_avg
                    sys.stdout.write('\rn = %04d, Ss = %1.5f, Cn = %04d, Cs = %1.5f' % (
                        n_clusters, silhouette_avg, cn, cs
                    ))
                except ConvergenceWarning:
                    sys.stdout.write('\rn = %04d, Ss = %1.5f, Cn = %04d, Cs = %1.5f' % (
                        9999, 9.99999, cn, cs
                    ))
                    wc += 1

            if wc > 5:
                break
        print()
        return cn

    @staticmethod
    def remove_dups(X):
        dups_map = []
        ndups_map = []
        js = []
        mis = []
        print('Remove dups init')
        for i in range(X.shape[0]):
            index = bisect.bisect_left(js, i)
            if not(index != len(js) and js[index] == i):
                for j in range(i + 1, X.shape[0]):
                    index = bisect.bisect_left(js, j)
                    if not(index != len(js) and js[index] == j):
                        cond = False
                        for k in range(X.shape[1]):
                            cond = X[i, k] != X[j, k]
                            if cond:
                                break
                        if not cond:
                            dups_map.append((i, j))
                            if len(js):
                                index = bisect.bisect_left(js, j)
                                js = js[:index] + [j] + js[index:]
                                mis = mis[:index] + [i] + mis[index:]
                            else:
                                js = [j]
                                mis = [i]
        print('\nRemove dups end')
        array = np.arange((X.shape[0] - len(js)) * X.shape[1], dtype=np.float).reshape(X.shape[0] - len(js), X.shape[1])
        k = 0
        for i in range(X.shape[0]):
            index = bisect.bisect_left(js, i)
            if index == len(js) or js[index] != i:
                for j in range(array.shape[1]):
                    array[k, j] = X[i, j]
                ndups_map.append((k, i))
                k += 1
        return array, dups_map, ndups_map

    @staticmethod
    def predict(X, flags=0x010):
        array, dups_map, ndups_map = ClustererGeneric.remove_dups(X)
        labels = [0] * array.shape[0]
        if flags & ClustererGeneric.KMEANS:
            kvalue = ClustererGeneric.ksearch(2, array.shape[0] - 1, array)
            labels = KMeans(n_clusters=kvalue, random_state=10).fit_predict(array)
        result = [None] * X.shape[0]
        for ndup in ndups_map:
            result[ndup[1]] = labels[ndup[0]]
        for dup in dups_map:
            result[dup[1]] = result[dup[0]]
        return result