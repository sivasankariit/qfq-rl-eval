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
from site_config import config

parser = argparse.ArgumentParser(description="Plot comparing overhead of none,htb,etc..")
parser.add_argument('--dir',
                    required=True,
                    help="expt output dir")

parser.add_argument('--maxy',
                    default=20,
                    type=int,
                    help="max y-axis")

parser.add_argument('--num-runs', '-r',
                    default=3,
                    type=int,
                    help="number of times the expt was run")

parser.add_argument('--num-class', '-n',
                    default=None,
                    type=int,
                    help="plot for a fixed num_classes")

parser.add_argument('--rate', '-R',
                    default=None,
                    type=int,
                    help="plot for a fixed rate limit")

parser.add_argument('--out', '-o',
                    help="save plot to file")

args = parser.parse_args()
rspaces = re.compile(r'\s+')

def ints(str):
    return map(int, str.split(' '))

plot_defaults.rcParams['figure.figsize'] = 4, 3.5

rls = config['EXPT_RL'].split(' ')
rls_seen = []
rl_name = dict(none="app", htb="htb",eyeq="eyeq", hwrl="hwrl")
colour_rl = dict(none="yellow", htb="green", tbf="blue", eyeq="grey", hwrl="cyan")

rates = ints(config["EXPT_RATES"])

num_classes = ints(config["EXPT_NCLASSES"])

runs = 1 + numpy.arange(args.num_runs)
# Stores references to the matplotlib artist that draws the bars so we
# can label it.
rl_bar = dict()

def DIR(rl, rate, num_class, run):
    return "rl-%s-rate-%s-ncl-%s-run-%s" % (rl, rate, num_class, run)

def E(lst):
    return list(enumerate(lst))

def get_rl_colour(rl):
    return colour_rl[rl]

def get_minor_colour(minor):
    return colour_rl[minor]

def plot_by_qty(fixed, major, minor):
    minor_bar = {}
    minors_seen = []
    for (i,XX), (j,YY) in itertools.product(E(minor['data']), E(major['data'])):
        ys = []
        for run in runs:
            d = dict()
            d.update(fixed)
            d.update({major['name']: YY,
                      minor['name']: XX,
                      'run': run})
            dir = DIR(**d)
            fs_dir = os.path.join(args.dir, dir)
            if not os.path.exists(fs_dir):
                print dir, "does not exist; ignoring..."
                continue
            ethstats_fname = os.path.join(args.dir, dir, "net.txt")
            mpstat_fname = os.path.join(args.dir, dir, "mpstat.txt")
            estats = EthstatsParser(ethstats_fname, iface='eth1')
            mpstats = MPStatParser(mpstat_fname)
            summ = estats.summary()
            print d, mpstats.summary(), summ
            ys.append(mpstats.kernel())

        if len(ys) == 0:
            continue

        x = j * (len(minor['data']) + 1) + i
        bar = plt.bar(x, mean(ys), width=1, color=get_minor_colour(XX),
                      yerr=stdev(ys), ecolor='red')
        minor_bar[XX] = bar[0]
        if XX not in minors_seen:
            minors_seen.append(XX)

    plt.legend([minor_bar[XX] for XX in minors_seen],
               minors_seen,
               loc="upper right")
    width = len(minor['data']) + 1
    xtickloc = width * numpy.arange(len(major['data'])) + (width / 2)
    plt.xticks(xtickloc, major['data'])
    plt.ylim((0, args.maxy))
    plt.ylabel("CPU usage %")
    plt.xlabel(major['label'])

    if args.out:
        plt.savefig(args.out)
        print "saved to", args.out
    else:
        plt.show()


if args.num_class:
    # plot keeping num_class fixed.
    plot_by_qty({'num_class': args.num_class},
                minor={'name': 'rl',
                       'data': rls},
                major={'name': 'rate',
                       'data': rates,
                       'label': "rates"})
elif args.rate:
    # plot keeping rate fixed.
    plot_by_qty({'rate': args.rate},
                minor={'name': 'rl',
                       'data': rls},
                major={'name': 'num_class',
                       'data': num_classes,
                       'label': "number of classes"})
