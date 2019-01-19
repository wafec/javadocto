#!/usr/bin/env bash

THE_SUMMARY=$1
THE_TEST=$2
THE_SETUP=$3
THE_MAPPING=$4
THE_SQL=$5

THE_SUDO='8130501'

stack()
{
    echo $THE_SUDO | sudo -S -u stack -H bash -c "cd /opt/stack/queens/devstack; source stack.sh"
}

unstack()
{
    echo $THE_SUDO | sudo -S -u stack -H bash -c "cd /opt/stack/queens/devstack; source unstack.sh"
    echo $THE_SUDO | sudo -S -u stack -H bash -c "cd /opt/stack/queens/devstack; source clean.sh"
}

create_test_database()
{
    SQL_MODEL=$1

    mysql -uroot -psupersecret < $SQL_MODEL
}

execute_one_parameter()
{
    THE_PARAM=$1
    # --logger "/var/log/syslog"
    python openhurricane/experiments.py --debug compute injection "$THE_SUMMARY" "$THE_TEST" "$THE_SETUP" "$THE_PARAM" --type number
}

unstack
while read p; do
    stack
    create_test_database $THE_SQL
    echo "--------------------------- START_SHELL----"
    echo "---------------- $p ---"
    execute_one_parameter $p
    echo "--------------------------- END_SHELL----"
    unstack
done <$THE_MAPPING

echo "END_OF_THIS_SCRIPT"