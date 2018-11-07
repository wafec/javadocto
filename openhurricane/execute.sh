#!/usr/bin/env bash

THE_SUMMARY=$1
THE_TEST=$2
THE_SETUP=$3
THE_MAPPING=$4

stack()
{
    sudo -u stack -H bash -c "cd /opt/stack/queens/devstack; source stack.sh"
}

unstack()
{
    sudo -u stack -H bash -c "cd /opt/stack/queens/devstack; source unstack.sh"
}

execute_one_parameter()
{
    THE_PARAM=$1
    python openhurricane/experiments.py --logger "/var/log/syslog" --debug compute injection "$THE_SUMMARY" "$THE_TEST" "$THE_SETUP" "$THE_PARAM" --type number
}

unstack
while read p; do
    stack
    echo "--------------------------- START_SHELL----"
    echo "---------------- $p ---"
    execute_one_parameter $p
    echo "--------------------------- END_SHELL----"
    unstack
done <$THE_MAPPING