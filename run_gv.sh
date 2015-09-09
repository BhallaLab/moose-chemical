#!/usr/bin/env bash
if [ $# -lt 1 ]; then
    echo "USAGE: $0 model_path "
    exit
fi
model_path="$1"
python ./gv.py -st 20 -f $model_path --solver moose  --outfile $model_path.dat
neato -Tpng ${model_path}_out.dot > ${model_path}.png
