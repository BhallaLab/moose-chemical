#!/usr/bin/env bash
set -e
models=`find . -type f -name "*.chem"`
for m in $models; do
    echo "Executing $m"
    python ../chemgv.py run -st 20 -f $m --solver moose  --outfile $m.dat
done
