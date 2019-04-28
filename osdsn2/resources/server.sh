#!/usr/bin/env bash

source "./resources/openstack.sh"

sys_logs_destination=$1
port=$2
sys_logs_monitor_pid=0

start_monitor_sys_logs() {
    if [[ ${sys_logs_monitor_pid} -eq 0 ]]; then
        tail -f "/var/log/syslog" >> "$sys_logs_destination" &
        sys_logs_monitor_pid=$!
    fi
}

stop_monitor_sys_logs() {
    if [[ ${sys_logs_monitor_pid} -ne 0 ]]; then
        kill -SIGSTOP ${sys_logs_monitor_pid}
    fi
}

rm ${sys_logs_destination}

coproc netcat -l localhost ${port}

while read -r cmd; do
    case "$cmd" in
        s) stack ;;
        u) unstack ;;
        q) kill "$COPROC_PID"
           exit ;;
        a) start_monitor_sys_logs ;;
        b) stop_monitor_sys_logs ;;
        *) echo "What?" ;;
    esac
    echo "SERVER_COMPLETED"
done <&${COPROC[0]} >&${COPROC[1]}