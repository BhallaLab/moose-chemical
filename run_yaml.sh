#!/usr/bin/env bash
if [ $# -lt 1 ]; then
    echo "USAGE: $0 model_path "
    exit
fi
model_path="$1"
python ./yacml.py -st 20 -f $model_path --outfile $model_path.dat
~/Scripts/plot_csv.py -i $model_path.dat -y 1,10 -o $model_path.png -s
