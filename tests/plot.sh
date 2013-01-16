#!/bin/bash

dir="$1"

if [ -z "$dir" ]; then
    echo "usage: $(basename $0) expt-dir"
    exit 1;
fi

pushd $dir;
rrsize=1

for nrr in 8 128; do
    out=rr-$rrsize-nrr-$nrr.png
    python ../plot.py --rr rl-htb-rrsize-$rrsize-nrr-$nrr \
    	rl-qfq-rrsize-$rrsize-nrr-$nrr \
	-o $out --ymin 0.1 --labels htb qfq
done
popd;
