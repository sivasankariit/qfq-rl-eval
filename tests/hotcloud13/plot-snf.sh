#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <result_dir>"
    exit 1
fi

dir=$1

EXPT_RATES=`python site_config.py --var EXPT_RATES`
EXPT_NCLASSES=`python site_config.py --var EXPT_NCLASSES`
EXPT_RL=`python site_config.py --var EXPT_RL`
EXPT_RUN=`python site_config.py --var EXPT_RUN`
PLOT_TMPDIR=`python site_config.py --var PLOT_TMPDIR`

mkdir -p $PLOT_TMPDIR
TMPDIR=`mktemp -d --tmpdir=$PLOT_TMPDIR`
echo TMPDIR=$TMPDIR
for rate in $EXPT_RATES; do
for rl in $EXPT_RL; do
for nclasses in $EXPT_NCLASSES; do
for run in $EXPT_RUN; do
    exptid=rl-$rl-rate-$rate-ncl-$nclasses-run-$run
    echo "Processing $dir/$exptid"
    echo "    Extracting tar files"
    tar xf $dir/$exptid.tar.gz -C $TMPDIR
    tar xf $dir/$exptid-snf.tar.gz -C $TMPDIR
    echo "    Plotting"
    python hotcloud13/plot-sniffer.py -f $TMPDIR/$exptid/pkt_snf.txt \
        -r `echo $[$rate / 1000]` \
        -o $dir/$exptid/pkt_arr.pdf > $dir/$exptid/plot-sniffer-output.txt
    echo "    Removing untar'd sniffer file"
    rm $TMPDIR/$exptid/pkt_snf.txt
done;
done;
done;
done;

echo "Plotted graphs"
