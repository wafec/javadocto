#!/usr/bin/env bash

source "resources/tenv_functions.sh"

transition_target_path=$1
transition_target_dir_name=$2
index_from=$3

if [[ -d "$transition_target_path" ]]; then
    data_file="${transition_target_path}/data.yaml"
    data_file2="${transition_target_path}/data.txt"
    if [[ -f "$data_file" ]] && [[ -f "$data_file2" ]]; then
        test_case_path="$(cat $data_file2 | sed -n 1p)"
        test_summary_path="$(cat $data_file2 | sed -n 2p)"

        experiment_log_dir="${transition_target_path}"
        log_file_name="$(date +"%Y_%m_%d_%H%M%S.log")"
        experiment_log_file="${experiment_log_dir}/WE_${log_file_name}.1"
        experiment_log_file_aux="${experiment_log_dir}/WE_${log_file_name}.2"

        touch "$experiment_log_file"
        touch "$experiment_log_file_aux"
        start_log
        run_with_errors2 "$test_case_path" "$test_summary_path" "$transition_target_dir_name" "$experiment_log_file" "$data_file" "$index_from"
        stop_log
    fi
fi
