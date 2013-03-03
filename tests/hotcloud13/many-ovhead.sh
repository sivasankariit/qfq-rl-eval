#!/bin/bash

dir=`date +%b%d--%H-%M`
time=40
ns=0
start=`date`
mtu=9000

function finish {
    killall -9 ssh
    exit
}

trap finish SIGINT

EXPT_RATES=`python site_config.py --var EXPT_RATES`
EXPT_NCLASSES=`python site_config.py --var EXPT_NCLASSES`
EXPT_RL=`python site_config.py --var EXPT_RL`
EXPT_RUN=`python site_config.py --var EXPT_RUN`
DEV=`python site_config.py --var DEFAULT_DEV`
NUM_CPUS=`python site_config.py --var NUM_CPUS`

sudo python ../utils/set-affinity.py $DEV

mkdir -p $dir
for rate in $EXPT_RATES; do
for rl in $EXPT_RL; do
for nclasses in $EXPT_NCLASSES; do
for run in $EXPT_RUN; do
    exptid=rl-$rl-rate-$rate-ncl-$nclasses-run-$run
    python udp.py --nrr 0 \
        --exptid $exptid \
        -t $time \
        --rl $rl \
        --rate $rate \
        --mtu $mtu \
        --num-class $nclasses \
        --ns $NUM_CPUS # Same num of sender progs as CPUs

    mv $exptid.tar.gz $dir/
    mv $exptid-snf.tar.gz $dir/

    pushd $dir;
    tar xf $exptid.tar.gz
    #tar xf $exptid-snf.tar.gz
    #python ../hotcloud13/plot-sniffer.py -f $exptid/pkt_snf.txt \
    #    -r `echo $[$rate / 1000]` \
    #    -o $exptid/pkt_arr.pdf > $exptid/plot-sniffer-output.txt
    #rm -f $exptid/pkt_snf.txt
    #python ../plot.py --rr $exptid/* -o $exptid.png --ymin 0.9
    popd;
done;
done;
done;
done;

echo "Experiment results are in $dir"
echo "started at $start"
echo ended at `date`
