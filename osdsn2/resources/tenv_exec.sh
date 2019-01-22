#!/usr/bin/env bash

experiment_pid=0
stopped=0
stack_pid=0
unstack_pid=0

echo -n "Password:"
read -s password
echo


run_stack_script() {
    echo $password | sudo -S -u stack -H bash -c "cd /opt/stack/devstack; source stack.sh" &
    stack_pid=$!
    wait $stack_pid
}


run_unstack_script() {
    echo $password | sudo -S -u stack -H bash -c "cd /opt/stack/devstack; source unstack.sh" &
    unstack_pid=$!
    wait $unstack_pid
    echo $password | sudo -S -u stack -H bash -c "cd /opt/stack/devstack; source clean.sh" &
    unstack_pid=$!
    wait $unstack_pid
}


handle_pre_run_inputs() {
    kill -SIGSTOP $experiment_pid
    run_unstack_script
    run_stack_script
    kill -SIGCONT $experiment_pid
}


signal_usr1() {
    handle_pre_run_inputs
}


handle_end() {
    kill -SIGHUP $experiment_pid
    kill -SIGHUP $stack_pid
    kill -SIGHUP $unstack_pid
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
    python osdsn2/experiment.py experiment_transition --parent-pid $$ $1 $2 $3 &
    experiment_pid=$!

    while [[ $stopped -eq 0 ]]; do
        sleep 1
    done
}

run_experiment_transition "tenv/t_build/test-case-Bailey.yaml" "tenv/t_build/test-summary-Amiya.yaml" "t_build"