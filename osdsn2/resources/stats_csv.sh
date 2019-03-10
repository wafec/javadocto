#!/usr/bin/env bash

src=$1
csv_file=$2
log_index=2

files=""
trans=""

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
    files="$files $merged"
    trans="$trans $tran"
done

echo "Generating CSV for R."
python osdsn2/stats.py we_csv "$csv_file" --files "$files" --trans "$trans"
echo "Finished."