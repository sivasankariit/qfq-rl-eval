#!/bin/bash

dir=`date +%b%d-%H:%M`
time=40
ns=0
start=`date`
dev=eth2

function finish {
    killall -9 ssh
    exit
}

trap finish SIGINT
python ../utils/set-affinity.py $dev

mkdir -p $dir
for rl in qfq; do
for rate in 9000; do
for divisor in 3; do
for nrls in 1 2 3; do
    exptid=qfq-nrls-$nrls-d-$divisor-rate-$rate
    python oversub.py \
        --exptid $exptid \
        -t $time \
        --rate $rate \
	--divisor $divisor \
	--nc $nrls

    mv $exptid.tar.gz $dir/

    pushd $dir;
    tar xf $exptid.tar.gz
    #python ../plot.py --rr $exptid/* -o $exptid.png --ymin 0.9
    popd;
done;
done;
done;
done;

echo "Experiment results are in $dir"
echo "started at $start"
echo ended at `date`
