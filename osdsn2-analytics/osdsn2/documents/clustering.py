from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.exceptions import ConvergenceWarning

import re
import string
import json
from munch import munchify
import os
import shutil
import sys
import warnings

from osdsn2.analytics.mining import put_processes_on_one_value


def file_to_text(file):
    with open(file, 'r', encoding='iso-8859-1') as reader:
        obj = munchify(json.load(reader))
        return put_processes_on_one_value(obj)['__one__']


def preprocessor(text):
    text = re.sub(r"[{}]".format(string.punctuation), " ", text.lower())
    return text


def remove_empties_from_document(files, document):
    new_files = []
    new_document = []
    for file, text in zip(files, document):
        if text:
            new_files.append(file)
            new_document.append(text)
    return new_files, new_document


def ksearch(kmin, kmax, X):
    print('Searching k...')
    cn = 0
    cs = -1.0
    wc = 0
    for n_clusters in range(kmin, kmax):
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


def results_to_document(files, save_in, kvalue=None):
    document = [file_to_text(file) for file in files]
    files, document = remove_empties_from_document(files, document)

    tfidf_vectorizer = TfidfVectorizer(preprocessor=preprocessor)
    tfidf = tfidf_vectorizer.fit_transform(document)

    kvalue = kvalue if kvalue else ksearch(2, len(files) - 1, tfidf)
    kmeans = KMeans(n_clusters=kvalue).fit(tfidf)

    for cluster, file in zip(kmeans.predict(tfidf_vectorizer.transform(document)), files):
        dest_dir = os.path.join(save_in, str(cluster))
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        shutil.copy(file, os.path.join(dest_dir, os.path.basename(file)))


files = [os.path.join('out/tests/raw', file) for file in os.listdir("out/tests/raw")]
results_to_document(files, "out/tests/save")
