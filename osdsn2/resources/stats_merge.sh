#!/usr/bin/env bash

src=$1
log_index=$2

echo "Collecting data."

for tran in $(ls ${src}); do
    tran_path="${src}/${tran}"
    echo "Working on ${tran_path}"
    merged="${tran_path}/we_merged"
    echo "" > "${merged}"
    for we in $(ls -1 "${tran_path}" | grep "WE.*log\.$log_index"); do
        wepath="${tran_path}/${we}"
        echo "Merging ${we} to ${merged}."
        cat "${wepath}" >> "${merged}"
    done
done

echo "Finished"