import os
from osdsn2.analytics.feature_extraction import StackTraceVectorizer, StackTraceGraphHelper
from osdsn2.analytics.feature_extraction import TraceFileGraph
from osdsn2.analytics.feature_extraction import AbstractHelper
from osdsn2.analytics.clusterer import ClustererGeneric

import argparse


def stack_extraction_with_k_clusterer(raw, destination, process_name, flags):
    if os.path.exists(raw):
        raw_files = [os.path.join(raw, file_path) for file_path in os.listdir(raw)]
        raw_files = [file_path for file_path in raw_files if os.path.isfile(file_path)]
        graphs_map = []
        for file_path in raw_files:
            graphs_map += StackTraceGraphHelper.get_graphs_map(file_path, process_name)
        vectorizer = StackTraceVectorizer(StackTraceGraphHelper.get_graphs_from_map(graphs_map))
        X, documents = vectorizer.transform(int(flags, 16))
        labels = ClustererGeneric.predict(X)
        clusters_destination = os.path.join(destination, 'clusters')
        if not os.path.exists(clusters_destination):
            os.makedirs(clusters_destination)
        StackTraceGraphHelper.copy_files_based_on_labels(graphs_map, labels, clusters_destination)
        documents_destination = os.path.join(destination, 'documents')
        if not os.path.exists(documents_destination):
            os.makedirs(documents_destination)
        StackTraceGraphHelper.copy_documents_based_on_labels(graphs_map, documents, labels, documents_destination)
        charts_destination = os.path.join(destination, 'charts')
        if not os.path.exists(charts_destination):
            os.makedirs(charts_destination)
        for label in labels:
            zero = [x[1] for x in zip(labels, graphs_map) if x[0] == label]
            trace_graph = TraceFileGraph()
            for z in zero:
                trace_graph.add_nodesequence(z[1].trace_files)
            trace_graph.plot(os.path.join(charts_destination, "%04d-network.html" % (label)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()

    stack_k = sub.add_parser('stack-k')
    stack_k.add_argument('raw')
    stack_k.add_argument('destination')
    stack_k.add_argument('process_name')
    stack_k.add_argument('flags')
    stack_k.set_defaults(callback=lambda _a: stack_extraction_with_k_clusterer(_a.raw, _a.destination, _a.process_name, _a.flags))

    print_p = sub.add_parser('print-p')
    print_p.add_argument('raw')
    print_p.set_defaults(callback=lambda _a: AbstractHelper.print_processes_names(_a.raw))

    print_t = sub.add_parser('print-t')
    print_t.add_argument('raw')
    print_t.set_defaults(callback=lambda _a: AbstractHelper.print_processes_names_t(_a.raw))

    opts = parser.parse_args()
    opts.callback(opts)
