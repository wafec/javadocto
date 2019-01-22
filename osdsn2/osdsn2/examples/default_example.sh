#!/usr/bin/env bash

function f()
{
    tail -f "/var/log/syslog" >> log.log &
    pid=$!
    echo "$pid"
}

pid=$(f)

echo $pid
sleep 5
kill -SIGTERM $pid

sleep 5