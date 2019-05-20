import os
from osdsn2.analytics.feature_extraction import StackTraceVectorizer, StackTraceGraphHelper
from osdsn2.analytics.feature_extraction import AbstractHelper
from osdsn2.analytics.clusterer import KMeansClusterer

import argparse


def stack_extraction_with_k_clusterer(raw, destination, process_name):
    if os.path.exists(raw):
        raw_files = [os.path.join(raw, file_path) for file_path in os.listdir(raw)]
        raw_files = [file_path for file_path in raw_files if os.path.isfile(file_path)]
        graphs_map = []
        for file_path in raw_files:
            graphs_map += StackTraceGraphHelper.get_graphs_map(file_path, process_name)
        vectorizer = StackTraceVectorizer(StackTraceGraphHelper.get_graphs_from_map(graphs_map))
        X = vectorizer.transform()
        labels = KMeansClusterer.predict(X)
        if not os.path.exists(destination):
            os.makedirs(destination)
        StackTraceGraphHelper.copy_files_based_on_labels(graphs_map, labels, destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()

    stack_k = sub.add_parser('stack-k')
    stack_k.add_argument('raw')
    stack_k.add_argument('destination')
    stack_k.add_argument('process_name')
    stack_k.set_defaults(callback=lambda _a: stack_extraction_with_k_clusterer(_a.raw, _a.destination, _a.process_name))

    print_p = sub.add_parser('print-p')
    print_p.add_argument('raw')
    print_p.set_defaults(callback=lambda _a: AbstractHelper.print_processes_names(_a.raw))

    print_t = sub.add_parser('print-t')
    print_t.add_argument('raw')
    print_t.set_defaults(callback=lambda _a: AbstractHelper.print_processes_names_t(_a.raw))

    opts = parser.parse_args()
    opts.callback(opts)
