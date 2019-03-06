#!/usr/bin/env bash

src=$1
dst=$2

log_index="2"
ignore_states="error"
buffer_words="error warning ERROR WARNING"


for t_something in $(ls ${src}); do
    echo "sh: Generating Stats for ${t_something}"
    parent="${src}/${t_something}"
    merged="${parent}/we_merged"
    rm "${merged}"
    touch "${merged}"
    for we in $(ls -1 "${parent}" | grep "WE.*log\.$log_index"); do
        wepath="${parent}/${we}"
        cat "${wepath}" >> "${merged}"
    done
    efpath="$(ls -1 "${parent}" | grep "EF.*log.$log_index" | sed -n 1p)"
    efpath="${parent}/${efpath}"
    dstparent="${dst}/${t_something}"
    mkdir -p "${dstparent}"
    python osdsn2/stats.py ef_by_sample "${efpath}" --include-details | tee "${dstparent}/ef_sample.txt"
    python osdsn2/stats.py ef_by_faults "${efpath}" | tee "${dstparent}/ef_faults.txt"
    expected_state=$(grep "State" "${dstparent}/ef_faults.txt" | tail -1 | cut -d ' ' -f 7)
    python osdsn2/stats.py we_faults_stats "${merged}" --ignore-states ${ignore_states} --show-buffer --expected-state ${expected_state} --buffer-words ${buffer_words} | tee "${dstparent}/we_stats.txt"
    rm "${merged}"
done