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
EXPT_NRL=`python site_config.py --var EXPT_NRL`
EXPT_RL=`python site_config.py --var EXPT_RL`
EXPT_RUN=`python site_config.py --var EXPT_RUN`
dev=`python site_config.py --var DEFAULT_DEV`

sudo python ../utils/set-affinity.py $dev

mkdir -p $dir
for rate in $EXPT_RATES; do
for nrls in $EXPT_NRL; do
for rl in $EXPT_RL; do
for run in $EXPT_RUN; do
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
