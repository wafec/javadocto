#!/usr/bin/env bash

experiment_pid=0
stopped=0
stopping=0

echo -n "Password:"
read -s password
echo


run_stack_script() {
    if [[ $stopping -eq 0 ]] && [[ $stopped -eq 0 ]]; then
        echo $password | sudo -S -u stack -H bash -c "cd /opt/stack/devstack; source stack.sh"
     fi
}


run_unstack_script() {
    if [[ $stopping -eq 0 ]] && [[ $stopped -eq 0 ]]; then
        echo $password | sudo -S -u stack -H bash -c "cd /opt/stack/devstack; source unstack.sh"
    fi
    sleep 1.5
    if [[ $stopping -eq 0 ]] && [[ $stopped -eq 0 ]]; then
        echo $password | sudo -S -u stack -H bash -c "cd /opt/stack/devstack; source clean.sh"
    fi
}


handle_pre_run_inputs() {
    kill -SIGSTOP $experiment_pid
    sleep 2
    run_unstack_script
    sleep 2
    run_stack_script
    sleep 2
    kill -SIGCONT $experiment_pid
}


signal_usr1() {
    handle_pre_run_inputs
}


handle_end() {
    stopping=1
    kill -SIGINT $experiment_pid
    stopped=1
}


signal_usr2() {
    handle_end
}


signal_int() {
    handle_end
}


trap signal_usr1 SIGUSR1
trap signal_usr2 SIGUSR2
trap signal_int SIGINT


run_experiment_transition() {
    stopped=0
    stopping=0
    python osdsn2/experiment.py experiment_transition --parent-pid $$ $1 $2 $3 &
    experiment_pid=$!

    while [[ $stopped -eq 0 ]]; do
        sleep 1
    done
}


run_experiment_transition "tenv/t_build/test-case-Bailey.yaml" "tenv/t_build/test-summary-Amiya.yaml" "t_build"