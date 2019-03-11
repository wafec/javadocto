#!/usr/bin/env bash

src=$1
csv_file=$2
log_index=2

files=""
trans=""

echo "Checking files."

for tran in $(ls ${src}); do
    tran_path="${src}/${tran}"
    echo "Working on ${tran_path}"
    merged="${tran_path}/we_merged"
    echo "Confirming ${merged}"
    if [[ ! -f $merged ]]; then
        echo "File not found."
        exit
    fi
    files="$files $merged"
    trans="$trans $tran"
done

echo "Generating CSV for R."
python osdsn2/stats.py we_csv "$csv_file" --files $files --trans $trans
echo "Finished."