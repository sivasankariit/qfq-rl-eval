#!/bin/bash

dir=`date +%b%d-%H:%M`
time=30
ns=0

mkdir -p $dir
for nrr in 8 128; do
for rrsize in 1; do
for rl in htb qfq; do
    exptid=rl-$rl-rrsize-$rrsize-nrr-$nrr
    python netperf.py --nrr $nrr \
        --exptid $exptid \
        -t $time \
        --ns $ns \
        --rl $rl \
        --rrsize $rrsize

    mv $exptid.tar.gz $dir/
    pushd $dir; tar xf $exptid.tar.gz; popd $dir;
done;
done
done

echo Experiment results are in $dir
