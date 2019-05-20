import warnings
from sklearn.exceptions import ConvergenceWarning
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import sys


class KMeansClusterer(object):
    @staticmethod
    def ksearch(kmin, kmax, X):
        print('Searching k...')
        cn = 0
        cs = -1.0
        wc = 0
        for n_clusters in range(int(kmin), int(kmax)):
            with warnings.catch_warnings():
                warnings.filterwarnings('error')
                try:
                    clusterer = KMeans(n_clusters=n_clusters)
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
    def predict(X):
        kvalue = KMeansClusterer.ksearch(2, X.shape[0], X)
        labels = KMeans(n_clusters=kvalue).fit_predict(X)
        return labels