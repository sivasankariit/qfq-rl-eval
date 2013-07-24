#!/bin/bash

dir=`date +%b%d--%H-%M`
time=300
start=`date`
mtu=1500

function finish {
    killall -9 ssh
    exit
}

trap finish SIGINT

NUM_CPUS=`python site_config.py --var NUM_CPUS`
EXCLUDE_CPUS=`python site_config.py --var EXCLUDE_CPUS`

mkdir -p $dir
touch $dir/expt_config.txt
echo "NUM_CPUS = ${NUM_CPUS}" >> $dir/expt_config.txt
echo "EXCLUDE_CPUS = ${EXCLUDE_CPUS}" >> $dir/expt_config.txt
pair_rate=1000
for mcrate in 5000 7000 9000 11000; do
for rl in none htb qfq; do
for run in 1; do
    exptid=memcached-rl-$rl-mcrate-$mcrate-run-$run
    mkdir -p $dir/$exptid
    chmod a+w $dir/$exptid

    # Write the expsift_tags file
    pushd $dir/$exptid
    touch expsift_tags
    chmod a+w expsift_tags
    echo "link_speed_mbps=10000" >> expsift_tags
    echo "nic_vendor=intel" >> expsift_tags
    echo "workload=memcached_set" >> expsift_tags
    echo "mtu=$mtu" >> expsift_tags
    echo "tso=off" >> expsift_tags
    echo "gso=off" >> expsift_tags
    echo "lro=on" >> expsift_tags
    echo "gro=off" >> expsift_tags
    echo "rl=$rl" >> expsift_tags
    echo "pair_rate=$pair_rate" >> expsift_tags
    echo "mcrate=$mcrate" >> expsift_tags
    echo "tenants=8" >> expsift_tags
    echo "run=$run" >> expsift_tags
    popd

    # Run the experiment
    python mcperf.py --exptid $exptid \
        -t $time \
        --rl $rl \
        --pair_rate $pair_rate \
        --mcrate $mcrate \
        --mcworkload "set" \
        --mtu $mtu \
        --htb-mtu $mtu \
        --num_tenants 8 \
        --outdir $dir/$exptid

    chmod a+w $dir/$exptid
done;
done;
done;

echo "Experiment results are in $dir"
echo "started at $start"
echo ended at `date`
