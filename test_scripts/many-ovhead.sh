#!/bin/bash

dir=`date +%b%d--%H-%M`
time=40
start=`date`
mtu=1500

function finish {
    killall -9 ssh
    exit
}

trap finish SIGINT

EXPT_RATES=`python site_config.py --var EXPT_RATES`
EXPT_NCLASSES=`python site_config.py --var EXPT_NCLASSES`
EXPT_RL=`python site_config.py --var EXPT_RL`
EXPT_RUN=`python site_config.py --var EXPT_RUN`
NUM_CPUS=`python site_config.py --var NUM_CPUS`

mkdir -p $dir
touch $dir/expt_config.txt
echo "EXPT_RATES = ${EXPT_RATES}" >> $dir/expt_config.txt
echo "EXPT_NCLASSES = ${EXPT_NCLASSES}" >> $dir/expt_config.txt
echo "EXPT_RL = ${EXPT_RL}" >> $dir/expt_config.txt
echo "EXPT_RUN = ${EXPT_RUN}" >> $dir/expt_config.txt
echo "NUM_CPUS = ${NUM_CPUS}" >> $dir/expt_config.txt
for rate in $EXPT_RATES; do
for rl in $EXPT_RL; do
for nclasses in $EXPT_NCLASSES; do
for run in $EXPT_RUN; do
    exptid=rl-$rl-rate-$rate-ncl-$nclasses-run-$run
    mkdir -p $dir/$exptid
    chmod a+w $dir/$exptid

    # Write the expsift_tags file
    pushd $dir/$exptid
    touch expsift_tags
    chmod a+w expsift_tags
    echo "link_speed_mbps=10000" >> expsift_tags
    echo "nic_vendor=intel" >> expsift_tags
    echo "workload=trafgen_tcp" >> expsift_tags
    echo "mtu=$mtu" >> expsift_tags
    echo "tso=on" >> expsift_tags
    echo "gso=off" >> expsift_tags
    echo "lro=on" >> expsift_tags
    echo "gro=off" >> expsift_tags
    echo "gso_max_size=65536" >> expsift_tags
    echo "rl=$rl" >> expsift_tags
    echo "rate_mbps=$rate" >> expsift_tags
    echo "nclasses=$nclasses" >> expsift_tags
    echo "run=$run" >> expsift_tags
    echo "num_senders=$NUM_CPUS" >> expsift_tags
    popd

    # Run the experiment
    python trafgen.py --proto tcp \
        --exptid $exptid \
        -t $time \
        --rl $rl \
        --rate $rate \
        --mtu $mtu \
        --htb-mtu $mtu \
        --num-class $nclasses \
        --ns $NUM_CPUS # Same num of sender progs as CPUs

    mv $exptid.tar.gz $dir/
    mv $exptid-snf.tar.gz $dir/

    pushd $dir;
    tar xf $exptid.tar.gz
    tar xf $exptid-snf.tar.gz
    chmod a+w $exptid
    popd;
done;
done;
done;
done;

echo "Experiment results are in $dir"
echo "started at $start"
echo ended at `date`
