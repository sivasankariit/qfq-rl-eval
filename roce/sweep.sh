#!/bin/bash

dir=`date +%b%d--%H-%M`
start=`date`
time=20

server=triton01
client=triton02
sshopts="-t -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"

#set -e

function finish {
    echo -----------------------------------------
    echo started at $start
    echo finished at $(date)
    echo -----------------------------------------
}

mkdir -p $dir

for n in 10000 100000 1000000; do
for msize in 1 32 64; do
for p in 1 8 16 32; do
for q in 1 32 64; do
    edir=n$n-msize$msize-p$p-q$q
    mkdir -p $dir/$edir

    if [ ! -d $dir/$edir ]; then
	exit
    fi

    # Start montor at the client, only the +ve rates -- i.e. don't log 0Gb/s
    ssh $sshopts $client python rocestats.py -i 0.1 > $dir/$edir/rate.txt &

    # Start the server
    echo starting server at $server
    ssh $sshopts $server sudo python roce_40g_expt.py \
	-s -n $n --msize $msize -p $p -q $q > $dir/$edir/server.txt 2>&1 &
    sleep 3

    # Start the client
    ssh $client $sshopts sudo python roce_40g_expt.py \
	-c $server -n $n --msize $msize -p $p -q $q > $dir/$edir/client.txt 2>&1 &

    echo -----------------------------------------
    echo params $edir
    echo -----------------------------------------
    echo Running experiment...

    # Run the experiment
    count=$time
    while [ "$count" -ne "0" ]; do
	sleep 1
	echo $count seconds remaining
	count=$(($count-1))
    done

    # Kill all
    jobs -p | xargs sudo kill -9
done
done
done
done

finish
