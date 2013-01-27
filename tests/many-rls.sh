#!/bin/bash

dir=`date +%b%d-%H:%M`
time=40
ns=0

function finish {
    killall -9 ssh
    exit
}

trap finish SIGINT

mkdir -p $dir
for rl in qfq; do
for rate in 1000 3000 5000 7000 9000; do
for nrls in 1 10 100 1000; do
    exptid=rl-$rl-nrls-$nrls-rate-$rate
    rate_per_rl=$(($rate/$nrls))
    python netperf.py --nrr 0 \
        --exptid $exptid \
        -t $time \
        --rl $rl \
        --rate $rate_per_rl \
        --nrls $nrls \
	--ns $nrls # Same num of senders as rate limiters

    mv $exptid.tar.gz $dir/

    pushd $dir;
    tar xf $exptid.tar.gz
    #python ../plot.py --rr $exptid/* -o $exptid.png --ymin 0.9
    popd;
done;
done;
done;

echo Experiment results are in $dir
