#!/usr/bin/env bash

source "resources/tenv_functions.sh"

dest_dir=$1
log_dir=$2

for transition_target_dir in $(ls "$dest_dir"); do
    transition_target_path="${dest_dir}/${transition_target_dir}"
    if [[ -d "$transition_target_path" ]]; then
        dirs=$(find "$transition_target_path" -maxdepth 1 -type d | wc -l)
        dirs=$(($dirs - 1))
        selected_dir_index=$(( ( RANDOM % $dirs ) + 1 ))
        selected_dir=$(ls "$transition_target_path" | sed -n ${selected_dir_index}p)
        experiment_path="${transition_target_path}/${selected_dir}"
        test_summary=$(ls "$experiment_path" | grep "test-summary" | sed -n 1p)
        test_case=$(ls "$experiment_path" | grep "test-case" | sed -n 1p)
        test_summary_path="${experiment_path}/${test_summary}"
        test_case_path="${experiment_path}/${test_case}"

        experiment_log_dir="${log_dir}/${transition_target_dir}"
        log_file_name="$(date +"%Y_%m_%d_%H%M%S.log")"
        experiment_log_file="${experiment_log_dir}/EF_${log_file_name}.1"
        experiment_log_file_aux="${experiment_log_dir}/EF_${log_file_name}.2"
        data_file="${experiment_log_dir}/data.yaml"
        data_file2="${experiment_log_dir}/data.txt"
        mkdir -p "$experiment_log_dir"
        touch "$experiment_log_file"
        touch "$experiment_log_file_aux"
        echo "${test_case_path}" > $data_file2
        echo "${test_summary_path}" >> $data_file2

        start_log
        run_error_free "$test_case_path" "$test_summary_path" "$transition_target_dir" "$experiment_log_file" "$data_file"
        stop_log
    fi
done