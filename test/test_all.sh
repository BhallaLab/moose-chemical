#!/usr/bin/env bash
set -e
set -x
models=`find . -type f -name "*.yacml"`
for m in $models; do
    echo "Executing $m"
    python ../yacml.py -st 20 -f $m  --outfile $m.dat
done
