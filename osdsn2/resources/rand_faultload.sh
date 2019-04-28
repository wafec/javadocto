#!/usr/bin/env bash

opts_dir=$1
workload_dir=$2
control=$3
max=$4
log=$5
port=$6

for opts_file in $(ls ${opts_dir} | grep ".opts"); do
    opts_path="${opts_dir}/${opts_file}"
    opts_file_len=${#opts_file}
    workload_file=${opts_file:0:opts_file_len-5}
    wld_path="${workload_dir}/${workload_file}"
    python osdsn2/orandom.py --log-to "${log}" faultload "${wld_path}" "${opts_path}" "${control}" "${max}" --port "${port}"
done