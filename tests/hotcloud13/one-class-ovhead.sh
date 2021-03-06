#!/bin/bash

dir=`date +%b%d--%H-%M`
time=40
ns=0
start=`date`
dev=eth2
mtu=9000
cpus=8

function finish {
    killall -9 ssh
    exit
}

trap finish SIGINT
python ../utils/set-affinity.py $dev

mkdir -p $dir
for rate in 1000; do
for nrls in 1; do
for rl in htb; do
for num_class in 512; do
    exptid=rl-$rl-nrls-$nrls-rate-$rate-ncl-$num_class
    rate_per_rl=$(($rate/$nrls))
    python udp.py --nrr 0 \
        --exptid $exptid \
        -t $time \
        --rl $rl \
        --rate $rate_per_rl \
        --nrls $nrls \
	--mtu $mtu \
	--num-class $num_class \
	--ns $cpus

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
