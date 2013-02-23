#!/usr/bin/python
import sys
import argparse
import termcolor as T
import re
from collections import defaultdict
import matplotlib as mp
import matplotlib.pyplot as plt
import glob
import os
import numpy
import math
import plot_defaults
import sys
import itertools
from helper import *
from parser import EthstatsParser

IFACE="eth2"
ZERO="0.00"
parser = argparse.ArgumentParser(description="Plot ethstats experiment outputs.")
parser.add_argument('--dir',
                    help="expt output dir")

parser.add_argument('--out', '-o',
                    help="save plot to file")

args = parser.parse_args()
rspaces = re.compile(r'\s+')

plot_defaults.rcParams['figure.figsize'] = 4, 3.5

nrls = [1, 10, 100, 1000]
rates = [1000, 3000, 5000, 7000, 9000]

def DIR(nrl, rate):
    return "rl-qfq-nrls-%s-rate-%s" % (nrl, rate)

for nrl, rate in itertools.product(nrls, rates):
    dir = DIR(nrl, rate)
    fname = os.path.join(args.dir, dir, "net.txt")
    net = ESParser(fname)

    rates = net.parse()
    summ = net.summary()
    m, std = summ["mean"], summ["stdev"]
    print nrl, rate, summ

sys.exit(0)

if args.rr:
    colours = ["green", "red"]
    lss = ["--", "-"]
    labels = args.labels
    for dir,col, label, ls in zip(args.rr, colours, labels, lss):
        plot_rr(dir, lw=2, color=col, label=label, ls=ls)
    plt.legend(loc="lower right")
    if args.out is None:
        plt.show()
        pass
    else:
        print 'saved to %s' % args.out
        plt.savefig(args.out)
else:
    colours = dict(none="white", htb="#e9f2f9", newrl="#3c8dc5")
    labels = dict(newrl="EyeQ")
    rls = ["newrl"]#, "none"]
    L = len(rls)
    ssizes = [64, 1440, 32000]
    normalise = args.normalise
    nrls = 1000
    for start,rl in enumerate(rls):
        ys = []
        for rootdir in args.ss_dir:
            tmpys = []
            for ssize in ssizes:
                dir = "rl-%s-ssize-%s-nrls-%d" % (rl, ssize, nrls)
                path = os.path.join(rootdir, dir)
                if not os.path.exists(path):
                    print 'cannot find %s' % path
                    continue
                _, mbps, cpu = parse_st(path)
                print _, mbps, cpu
                if normalise:
                    tmpys.append(mbps/cpu)
                else:
                    tmpys.append(cpu)
            ys.append(tmpys)
        # Calculate errs
        ys, yerrs = process_series(ys)
        print yerrs
        plot_vbar(ys, start, skip=L+1, color=colours[rl],
                  label=labels.get(rl,rl),
                  yerr=yerrs, ecolor='black', alpha=1)
    xticks = L/2.0 + (L+1) * numpy.arange(0, len(ssizes))
    xticklabels = map(lambda e: str(e), ssizes)
    plt.xticks(xticks, xticklabels)
    plt.yticks(range(0, args.ymax+1, 10))
    plt.xlabel("Packet sizes")
    if normalise:
        plt.ylabel("Mb/s per CPU%")
        plt.title("Normalized CPU usage per Mb/s")
    else:
        plt.ylabel("CPU %")
        plt.title("CPU usage")
    plt.grid(True)
    plt.legend(loc="upper right")
    plt.ylim((0, args.ymax))
    if args.out:
        plt.savefig(args.out)
    else:
        plt.show()
