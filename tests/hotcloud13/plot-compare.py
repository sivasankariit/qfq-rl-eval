#!/usr/bin/python
import sys
import os

sys.path.append(os.getcwd())

import argparse
import termcolor as T
import re
from collections import defaultdict
import matplotlib as mp
import matplotlib.pyplot as plt
import glob
import numpy
import math
import plot_defaults
import sys
import itertools
from helper import *
from output_parser import EthstatsParser, MPStatParser

parser = argparse.ArgumentParser(description="Plot comparing overhead of none,htb,etc..")
parser.add_argument('--dir',
                    required=True,
                    help="expt output dir")

parser.add_argument('--maxy',
                    default=40,
                    type=int,
                    help="max y-axis")

parser.add_argument('--num-runs', '-r',
                    default=3,
                    type=int,
                    help="number of times the expt was run")

parser.add_argument('--out', '-o',
                    help="save plot to file")

args = parser.parse_args()
rspaces = re.compile(r'\s+')

plot_defaults.rcParams['figure.figsize'] = 4, 3.5

rls = ["none", "htb", "eyeq"]#, "tbf"]
rls_seen = []
rl_name = dict(none="app", htb="htb",eyeq="eyeq")
colour_rl = dict(none="yellow", htb="green", tbf="blue", eyeq="grey")

rates = [1000, 3000, 5000, 7000, 9000]

runs = 1 + numpy.arange(args.num_runs)
# Stores references to the matplotlib artist that draws the bars so we
# can label it.
rl_bar = dict()

def DIR(rl, rate, run):
    return "rl-%s-nrls-1-rate-%s-run-%s" % (rl, rate, run)

def E(lst):
    return list(enumerate(lst))

def get_rl_colour(rl):
    return colour_rl[rl]

for (i,rl), (j,rate) in itertools.product(E(rls), E(rates)):
    ys = []
    for run in runs:
        dir = DIR(rl, rate, run)
        fs_dir = os.path.join(args.dir, dir)
        if not os.path.exists(fs_dir):
            print dir, "does not exist; ignoring..."
            continue
        ethstats_fname = os.path.join(args.dir, dir, "net.txt")
        mpstat_fname = os.path.join(args.dir, dir, "mpstat.txt")

        estats = EthstatsParser(ethstats_fname)
        mpstats = MPStatParser(mpstat_fname)

        #rates = estats.parse()
        summ = estats.summary()
        print rl, rate, summ, run, mpstats.summary()
        ys.append(mpstats.kernel())

    if len(ys) == 0:
        continue

    x = j * (len(rls) + 1) + i
    bar = plt.bar(x, mean(ys), width=1, color=get_rl_colour(rl),
                  yerr=stdev(ys), ecolor='red')
    rl_bar[rl] = bar[0]
    if rl not in rls_seen:
        rls_seen.append(rl)

plt.legend([rl_bar[rl] for rl in rls_seen],
           [rl_name[rl] for rl in rls_seen],
           loc="upper left")
width = len(rls) + 1
xtickloc = width * numpy.arange(len(rates)) + (width / 2)
plt.xticks(xtickloc, rates)
plt.ylim((0, args.maxy))
plt.ylabel("CPU usage %")
plt.xlabel("Rates in Mb/s")

if args.out:
    plt.savefig(args.out)
    print "saved to", args.out
