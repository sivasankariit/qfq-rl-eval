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

parser.add_argument('--out', '-o',
                    help="save plot to file")

args = parser.parse_args()
rspaces = re.compile(r'\s+')

plot_defaults.rcParams['figure.figsize'] = 4, 3.5

rls = ["none", "htb"]#, "tbf"]
rates = [3000]# [1000, 3000, 5000, 7000, 9000]

def DIR(rl, rate):
    return "rl-%s-nrls-1-rate-%s" % (rl, rate)

for rl, rate in itertools.product(rls, rates):
    dir = DIR(rl, rate)
    ethstats_fname = os.path.join(args.dir, dir, "net.txt")
    mpstat_fname = os.path.join(args.dir, dir, "mpstat.txt")

    estats = EthstatsParser(ethstats_fname)
    mpstats = MPStatParser(mpstat_fname)

    rates = estats.parse()
    summ = estats.summary()
    print rl, rate, summ, mpstats.summary()
