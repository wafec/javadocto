#!/usr/bin/env bash

echo -n "Password:"
read -s password
echo

call_stack() {
    echo "$password" | sudo -S -u stack -H bash -c "cd /opt/stack/devstack; source stack.sh"
}

call_unstack() {
    echo "$password" | sudo -S -u stack -H bash -c "cd /opt/stack/devstack; source unstack.sh"
}

call_clean() {
    echo "$password" | sudo -S -u stack -H bash -c "cd /opt/stack/devstack; source clean.sh"
}

stack() {
    call_stack
}

unstack() {
    call_unstack
    call_clean
}