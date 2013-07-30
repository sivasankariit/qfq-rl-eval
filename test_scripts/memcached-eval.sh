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
mc_total_rate_server=3000
mc_total_rate_client=3000
trafgen_total_rate=3000
trafgenproto="udp"
mcsize=4096
mcnconn=8
echo "mc_total_rate_server = ${mc_total_rate_server}" >> $dir/expt_config.txt
echo "mc_total_rate_client = ${mc_total_rate_client}" >> $dir/expt_config.txt
echo "trafgen_total_rate = ${trafgen_total_rate}" >> $dir/expt_config.txt
echo "trafgenproto= ${trafgenproto}" >> $dir/expt_config.txt
echo "mcsize = ${mcsize}" >> $dir/expt_config.txt
echo "mcnconn = ${mcnconn}" >> $dir/expt_config.txt

OLDIFS=$IFS;
IFS=','
for mcrate in 2500; do
for rl in none htb qfq; do
for tenants in 10,4; do
    set $tenants;
    mctenants=$1
    trafgentenants=$2
for run in 1; do
    exptid=memcached-rl-$rl-mcrate-$mcrate-mctenants-$mctenants-trafgentenants-$trafgentenants-run-$run
    mkdir -p $dir/$exptid
    chmod a+w $dir/$exptid

    # Write the expsift_tags file
    pushd $dir/$exptid
    touch expsift_tags
    chmod a+w expsift_tags
    echo "link_speed_mbps=10000" >> expsift_tags
    echo "nic_vendor=intel" >> expsift_tags
    echo "workload=memcached_get+trafgen_udp" >> expsift_tags
    echo "mtu=$mtu" >> expsift_tags
    echo "tso=off" >> expsift_tags
    echo "gso=off" >> expsift_tags
    echo "lro=on" >> expsift_tags
    echo "gro=off" >> expsift_tags
    echo "rl=$rl" >> expsift_tags
    echo "mcsize=$mcsize" >> expsift_tags
    echo "mc_total_rate_server=$mc_total_rate_server" >> expsift_tags
    echo "mc_total_rate_client=$mc_total_rate_client" >> expsift_tags
    echo "mcrate=$mcrate" >> expsift_tags
    echo "mcncon=$mcnconn" >> expsift_tags
    echo "mctenants=$mctenants" >> expsift_tags
    echo "trafgentenants=$trafgentenants" >> expsift_tags
    echo "trafgenproto=$trafgenproto" >> expsift_tags
    echo "trafgen_total_rate=$trafgen_total_rate" >> expsift_tags
    echo "run=$run" >> expsift_tags
    popd

    # Run the experiment
    python mcperf.py --exptid $exptid \
        --time $time \
        --rl $rl \
        --mtu $mtu \
        --htb-mtu $mtu \
        --mcsize $mcsize \
        --mcrate $mcrate \
        --mcnconn $mcnconn \
        --mcworkload "get" \
        --mctenants $mctenants \
        --mc_total_rate_server $mc_total_rate_server \
        --mc_total_rate_client $mc_total_rate_client \
        --trafgentenants $trafgentenants \
        --trafgenproto $trafgenproto \
        --trafgen_total_rate $trafgen_total_rate \
        --outdir $dir/$exptid

    chmod a+w $dir/$exptid
done;
done;
done;
done;
IFS=$OLDIFS

echo "Experiment results are in $dir"
echo "started at $start"
echo ended at `date`
