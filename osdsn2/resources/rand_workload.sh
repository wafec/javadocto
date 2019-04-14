#!/usr/bin/env bash

source "resources/tenv_functions.sh"

workload_size=$1
workload_count_from=$2
workload_count_to=$3
destination_folder=$4

function execute_workload_generation {
    python osdsn2/orandom.py --log-to $1 workload ${workload_size} $2
}

experiment_pid=-1
stopping=0
stopped=0

for i in $(seq ${workload_count_from} ${workload_count_to}); do
    file_index=$(printf %04d $i)
    destination_file="${destination_folder}/wl.bin${file_index}.wld"

    experiment_log_file_aux="${destination_folder}/wl.sys${file_index}.log"
    experiment_log_file="${destination_folder}/wl.app${file_index}.log"

    touch ${experiment_log_file}
    touch ${experiment_log_file_aux}

    run_unstack_script
    run_stack_script
    start_log
    execute_workload_generation ${experiment_log_file} ${destination_file}
    stop_log
done

run_unstack_script