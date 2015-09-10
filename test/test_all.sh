#!/usr/bin/env bash
models=`find . -type f -name "*.dot"`
for m in $models; do
    python ../chemgv.py run -st 20 -f $m --solver moose  --outfile $model_path.dat
done
