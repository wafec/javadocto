#!/usr/bin/env bash

echo "Clearing data."

for tran in $(ls ${src}); do
    tran_path="${src}/${tran}"
    echo "Working on ${tran_path}"
    merged="${tran_path}/we_merged"
    echo "Removing ${merged}"
    if [[ -f $merged ]]; then
        rm $merged
    fi
done

echo "Finished"