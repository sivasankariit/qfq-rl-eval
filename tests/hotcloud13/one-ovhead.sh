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
for rate in 9000; do
for nclass in 16; do
for rl in htb; do
    exptid=rl-$rl-ncl-$ncl-rate-$rate-run-1
    rate_per_rl=$(($rate/$nclass))
    python udp.py --nrr 0 \
        --exptid $exptid \
        -t $time \
        --rl $rl \
        --rate $rate \
	--mtu $mtu \
	--ns 8 \
	--num-class $nclass

    mv $exptid.tar.gz $dir/

    pushd $dir;
    tar xf $exptid.tar.gz
    #python ../plot.py --rr $exptid/* -o $exptid.png --ymin 0.9
    popd;
done;
done;
done;

echo "Experiment results are in $dir"
echo "started at $start"
echo ended at `date`
