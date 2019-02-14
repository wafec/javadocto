#!/usr/bin/env bash

src=$1
dst=$2

for t_something in $(ls ${src}); do
    echo "sh: Generating Stats for ${t_something}"
    parent="${src}/${t_something}"
    merged="${parent}/we_merged"
    rm "${merged}"
    touch "${merged}"
    for we in $(ls -1 "${parent}" | grep "WE.*log\.1"); do
        wepath="${parent}/${we}"
        cat "${wepath}" >> "${merged}"
    done
    efpath="$(ls -1 "${parent}" | grep "EF.*log.1" | sed -n 1p)"
    efpath="${parent}/${efpath}"
    dstparent="${dst}/${t_something}"
    mkdir -p "${dstparent}"
    python osdsn2/stats.py ef_by_sample "${efpath}" --include-details | tee "${dstparent}/ef_sample"
    python osdsn2/stats.py ef_by_faults "${efpath}" | tee "${dstparent}/ef_faults"
    python osdsn2/stats.py we_faults_stats "${merged}" --ignore-states "error" | tee "${dstparent}/we_stats"
    rm "${merged}"
done