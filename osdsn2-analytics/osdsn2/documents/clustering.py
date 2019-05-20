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

import argparse
import logging


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
    removed_files = []
    for file, text in zip(files, document):
        if text:
            new_files.append(file)
            new_document.append(text)
        else:
            removed_files.append(file)
    return new_files, new_document, removed_files


def ksearch(kmin, kmax, X):
    print('Searching k...')
    logging.info('Start searching k')
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
                message = 'n = %04d, Ss = %1.5f, Cn = %04d, Cs = %1.5f' % (
                    n_clusters, silhouette_avg, cn, cs
                )
                sys.stdout.write('\r' + message)
                logging.info(message)
            except ConvergenceWarning:
                message = 'n = %04d, Ss = %1.5f, Cn = %04d, Cs = %1.5f' % (
                    9999, 9.99999, cn, cs
                )
                sys.stdout.write('\r' + message)
                logging.info(message)
                wc += 1

        if wc > 5:
            break
    print()
    return cn


def results_to_document(files, save_in, kvalue=None):
    document = [file_to_text(file) for file in files]
    files, document, removed_files = remove_empties_from_document(files, document)

    tfidf_vectorizer = TfidfVectorizer(preprocessor=preprocessor)
    tfidf = tfidf_vectorizer.fit_transform(document)

    kvalue = kvalue if kvalue else ksearch(2, len(files) - 1, tfidf)
    kmeans = KMeans(n_clusters=kvalue).fit(tfidf)

    for cluster, file in zip(kmeans.predict(tfidf_vectorizer.transform(document)), files):
        dest_dir = os.path.join(save_in, str(cluster))
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        shutil.copy(file, os.path.join(dest_dir, os.path.basename(file)))
        logging.info('File ' + os.path.basename(file) + ' to n = ' + str(cluster))
    dest_dir = os.path.join(save_in, 'empty')
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    for file in removed_files:
        shutil.copy(file, os.path.join(dest_dir, os.path.basename(file)))
        logging.info('File ' + file + ' to empty folder')


def _get_files_from_dir(d):
    return [os.path.join(d, file) for file in os.listdir(d)]


if __name__ == '__main__':
    handlers = []
    parser = argparse.ArgumentParser()
    parser.add_argument('raw', type=str)
    parser.add_argument('save', type=str)
    parser.add_argument('--extra', type=str, default=None)

    opts = parser.parse_args()

    if opts.extra:
        handlers.append(logging.FileHandler(opts.extra, 'a'))

    logging.basicConfig(format='%(asctime)s %(message)s', handlers=handlers, level=logging.INFO)
    results_to_document(_get_files_from_dir(opts.raw), opts.save)
