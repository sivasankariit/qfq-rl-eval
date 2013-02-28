#!/bin/bash

dir=`date +%b%d--%H-%M`
time=40
ns=0
start=`date`
dev=eth2
mtu=9000

function finish {
    killall -9 ssh
    exit
}

trap finish SIGINT
python ../utils/set-affinity.py $dev

mkdir -p $dir
for rate in 1000 3000 5000 7000 9000; do
for nrls in 1; do
for rl in none htb; do
for run in 1 2 3; do
    exptid=rl-$rl-nrls-$nrls-rate-$rate-run-$run
    rate_per_rl=$(($rate/$nrls))
    python udp.py --nrr 0 \
        --exptid $exptid \
        -t $time \
        --rl $rl \
        --rate $rate_per_rl \
        --nrls $nrls \
	--mtu $mtu \
	--ns $nrls # Same num of senders as rate limiters

    mv $exptid.tar.gz $dir/
    mv $exptid-snf.tar.gz $dir/

    pushd $dir;
    tar xf $exptid.tar.gz
    tar xf $exptid-snf.tar.gz
    #python ../plot.py --rr $exptid/* -o $exptid.png --ymin 0.9
    popd;
done;
done;
done;
done;

echo "Experiment results are in $dir"
echo "started at $start"
echo ended at `date`
