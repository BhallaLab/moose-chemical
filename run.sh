#!/usr/bin/env bash
if [ $# -lt 1 ]; then
    echo "USAGE: $0 model_path "
    exit
fi
model_path="$1"
python ./chem2moose.py -st 20 -f $model_path --solver moose -p -o ${model_path}.png
