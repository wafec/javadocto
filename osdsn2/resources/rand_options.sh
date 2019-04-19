#!/usr/bin/env bash

source_dir=$1
destination_dir=$2

for bin_candidate in $(ls ${source_dir}); do
    bin_candidate_path="${source_dir}/${bin_candidate}"
    if [[ -f ${bin_candidate_path} ]] && [[ ${bin_candidate} == *"wl.bin"* ]]; then
        opts_path="${destination_dir}/${bin_candidate}.opts"
        echo "Creating options for ${bin_candidate_path} as ${opts_path}"
        python osdsn2/orandom.py options ${bin_candidate_path} ${opts_path}
    fi
done