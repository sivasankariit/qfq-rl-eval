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

parser.add_argument('--out', '-o',
                    help="save plot to file")

args = parser.parse_args()
rspaces = re.compile(r'\s+')

plot_defaults.rcParams['figure.figsize'] = 4, 3.5

rls = ["none", "htb"]#, "tbf"]
rl_name = dict(none="app", htb="htb")
colour_rl = dict(none="yellow", htb="green", tbf="blue")
rates = [1000, 3000, 5000, 7000, 9000]
rl_bar = dict()

def DIR(rl, rate):
    return "rl-%s-nrls-1-rate-%s" % (rl, rate)

def E(lst):
    return list(enumerate(lst))

def get_rl_colour(rl):
    return colour_rl[rl]

for (i,rl), (j,rate) in itertools.product(E(rls), E(rates)):
    dir = DIR(rl, rate)
    ethstats_fname = os.path.join(args.dir, dir, "net.txt")
    mpstat_fname = os.path.join(args.dir, dir, "mpstat.txt")

    estats = EthstatsParser(ethstats_fname)
    mpstats = MPStatParser(mpstat_fname)

    #rates = estats.parse()
    summ = estats.summary()
    print rl, rate, summ, mpstats.summary()

    x = j * (len(rls) + 1) + i
    y = mpstats.kernel()
    bar = plt.bar(x, y, width=1, color=get_rl_colour(rl))
    rl_bar[rl] = bar[0]

plt.legend([rl_bar[rl] for rl in rls],
           [rl_name[rl] for rl in rls],
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

