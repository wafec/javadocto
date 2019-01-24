#!/usr/bin/env bash

experiment_pid=0
stopped=0
stopping=0
pid_a=0
pid_b=0
pid_script=0
experiment_log_file=""
experiment_log_file_aux=""

echo -n "Password:"
read -s password
echo


run_stack_script() {
    if [[ $stopping -eq 0 ]] && [[ $stopped -eq 0 ]]; then
        echo $password | sudo -S -u stack -H bash -c "cd /opt/stack/devstack; source stack.sh" &
        pid_script=$!
        wait $pid_script
    fi
}


run_unstack_script() {
    if [[ $stopping -eq 0 ]] && [[ $stopped -eq 0 ]]; then
        echo $password | sudo -S -u stack -H bash -c "cd /opt/stack/devstack; source unstack.sh" &
        pid_script=$!
        wait $pid_script
    fi
    sleep 1.5
    if [[ $stopping -eq 0 ]] && [[ $stopped -eq 0 ]]; then
        echo $password | sudo -S -u stack -H bash -c "cd /opt/stack/devstack; source clean.sh" &
        pid_script=$!
        wait $pid_script
    fi
}


start_experiment() {
    kill -SIGCONT "$experiment_pid"
}


stop_experiment() {
    kill -SIGSTOP "$experiment_pid"
}


handle_pre_run_inputs() {
    stop_experiment
    stop_log
    sleep 2
    run_unstack_script
    sleep 2
    run_stack_script
    sleep 2
    start_experiment
    start_log
}


signal_usr1() {
    handle_pre_run_inputs
}

start_log() {
    pid_a=$(log_a_to_b "/var/log/syslog" "$experiment_log_file_aux")
    pid_b=$(log_a_to_b "$experiment_log_file" "$experiment_log_file_aux")
}


stop_log() {
    kill -SIGKILL "$pid_a"
    kill -SIGKILL "$pid_b"
}


handle_end() {
    stopping=1
    stop_experiment
    stop_log
    kill -SIGTERM "$pid_script"
    stopped=1
}


signal_usr2() {
    handle_end
}


signal_int() {
    handle_end
    exit 1
}


trap signal_usr1 SIGUSR1
trap signal_usr2 SIGUSR2
trap signal_int SIGINT


run_brute_force() {
    stopped=0
    stopping=0
    python osdsn2/experiment.py --log-file $4 brute-force --parent-pid $$ $1 $2 $3 &
    experiment_pid=$!

    while [[ $stopped -eq 0 ]]; do
        sleep 1
    done
}


run_error_free() {
    stopped=0
    stopping=0
    python osdsn2/experiment.py --log-file $4 error-free --parent-pid $$ $1 $2 $3 $5 &
    experiment_pid=$!

    while [[ $stopped -eq 0 ]]; do
        sleep 1
    done
}


run_with_errors() {
    stopped=0
    stopping=0
    python osdsn2/experiment.py --log-file $4 with-errors --parent-pid $$ $1 $2 $3 $5 &
    experiment_pid=$!

    while [[ $stopped -eq 0 ]]; do
        sleep 1
    done
}


log_a_to_b() {
    tail -f $1 >> $2 &
    pid=$!
    echo "$pid"
}