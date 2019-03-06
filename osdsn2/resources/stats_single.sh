#!/usr/bin/env bash

src=$1

single_file_name="we_merged_all.dat"
rm ${single_file_name}
touch ${single_file_name}

log_index=2
ignore_states="error"

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

    cat "${merged}" >> "${single_file_name}"
    rm "${merged}"
done

python osdsn2/stats.py we_faults_stats "${single_file_name}" --ignore-states ${ignore_states} --show-buffer | tee "we_stats_all.txt"