from sklearn.cluster import KMeans
import numpy as np


class Data(object):
    def __init__(self, mean, stdev):
        self.mean = mean
        self.stdev = stdev


X = np.array([[Data(1, 2), Data(2, 3)], [Data(3, 4), Data(5, 6)]])
kmeans = KMeans(n_clusters=2, random_state=0).fit(X)
print(kmeans.cluster_centers_)