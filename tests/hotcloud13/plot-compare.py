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
from output_parser import EthstatsParser, MPStatParser, SnifferParser
from site_config import config

parser = argparse.ArgumentParser(description="Plot comparing overhead of none,htb,etc..")
parser.add_argument('--dir',
                    required=True,
                    help="expt output dir")

parser.add_argument('--maxy',
                    default=30,
                    type=int,
                    help="max y-axis")

parser.add_argument('--num-runs', '-r',
                    default=3,
                    type=int,
                    help="number of times the expt was run")

parser.add_argument('--tolerance', '-t',
                    default=0.1,
                    type=float,
                    help="tolerance of achieved rate in fraction")

parser.add_argument('--num-class', '-n',
                    default=None,
                    type=int,
                    help="plot for a fixed num_classes")

parser.add_argument('--rates',
                    nargs="+",
                    type=int,
                    default=[],
                    help="plot for the above sweep of rate limits")

parser.add_argument('--out', '-o',
                    help="save plot to file")

args = parser.parse_args()
rspaces = re.compile(r'\s+')

def ints(str):
    return map(int, str.split(' '))

SUBPLOT_HEIGHT = 4
SUBPLOT_WIDTH = 3.5
SUBPLOT_ROWS = len(args.rates)
SUBPLOT_COLS = 2 # CPU and stdev
plot_defaults.rcParams['figure.figsize'] = (SUBPLOT_HEIGHT * SUBPLOT_ROWS, SUBPLOT_WIDTH * SUBPLOT_COLS)

rls = config['EXPT_RL'].split(' ')
rls_seen = []

rl_name = dict(none="app", htb="htb",eyeq="eyeq", hwrl="hwrl")
rl_name['hwrl+'] = 'hwrl+'

colour_rl = dict(none="yellow", htb="green", tbf="blue", eyeq="grey", hwrl="cyan")
colour_rl['hwrl+'] = "cyan"

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

def err(s):
    return T.colored(s, "red", attrs=["bold"])

def plot_by_qty(ax, fixed, major, minor, fn_qty, opts={}):
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
            sniff_fname = os.path.join(args.dir, dir, "pkt_snf.txt")

            estats = EthstatsParser(ethstats_fname, iface='eth1')
            mpstats = MPStatParser(mpstat_fname)
            sniff = SnifferParser(sniff_fname, max_lines=1000000)

            summ = estats.summary()
            print '-'*80
            print "Parameters", d
            print "\tcpu ", mpstats.summary()
            print "\tnet ", summ
            print '-'*80
            yvalue = fn_qty(estats, mpstats, sniff)
            ys.append(yvalue)

        if len(ys) == 0 or mean(ys) == 0:
            continue

        x = j * (len(minor['data']) + 1) + i
        bar = ax.bar(x, mean(ys), width=1, color=get_minor_colour(XX),
                     yerr=stdev(ys), ecolor='red')
        if XX == 'hwrl' and YY > 16:
            bar[0].set_hatch('x')
            bar[0].set_facecolor('white')
            XX = XX + "+"
        minor_bar[XX] = bar[0]
        if XX not in minors_seen:
            minors_seen.append(XX)

    if opts.get('legend'):
        lg = ax.legend([minor_bar[XX] for XX in minors_seen],
                       [rl_name[XX] for XX in minors_seen],
                       loc="upper right")
        lg.draw_frame(False)
    width = len(minor['data']) + 1
    xtickloc = width * numpy.arange(len(major['data'])) + ((width - 1.0) / 2)
    # This is a pain with matplotlib; the ax and plt apis are slightly
    # different.  plt.xticks(xtickloc, xticklabels) will work, but it
    # has to be split as follows for axis.
    ax.set_xticks(xtickloc)
    ax.set_xticklabels(major['data'])

    if opts.get('yticklabels'):
        ax.set_yticklabels(opts.get('yticklabels'))

    ax.set_ylim(opts.get('ylim'))
    ax.set_ylabel(opts.get('ylabel'))
    ax.set_xlabel(major['label'])

    if opts.get('annotate'):
        ax.text(0.12, 0.9,
                opts.get('annotate'),
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes)

    if opts.get('show'):
        plt.show()

if args.rates:
    def plot_cpu(estats, mpstats, sniff, rate):
        achieved = estats.summary()
        if abs(achieved['mean'] - rate) > args.tolerance * rate:
            if achieved['mean'] > rate:
                print T.colored("higher rate", "green", attrs=["bold"])
            print err('tolerance failed: achieved %.3f, rate: %.3f' % (achieved['mean'], rate))
            return 0
        return mpstats.kernel()
    def plot_ipt(estats, mpstats, sniff, rate):
        achieved = estats.summary()
        m = sniff.mean_ipt()
        ideal_mean = sniff.ideal_ipt_nsec(total_rate_gbps=rate/1000.0)
        std_norm = sniff.stdev_ipt()
        if ideal_mean > 0:
            std_norm /= ideal_mean
        if abs(achieved['mean'] - rate) > args.tolerance * rate:
            print err('tolerance failed: achieved %.3f, rate: %.3f' % (achieved['mean'], rate))
            return 0
        return std_norm

    # plot keeping rate fixed.
    fig = plt.figure()
    plt_num = 0
    for rate in args.rates:
        assert(rate in rates)
        plt_num += 1
        ax = fig.add_subplot(SUBPLOT_ROWS, SUBPLOT_COLS, plt_num)
        plot_by_qty(ax,
                    {'rate': rate},
                    minor={'name': 'rl',
                           'data': rls},
                    major={'name': 'num_class',
                           'data': num_classes,
                           'label': "number of classes"},
                    fn_qty=lambda e,m,s: plot_cpu(e, m, s, rate),
                    opts={'ylim': (0, args.maxy), 'legend': False,
                          'annotate': "Rate: %d Gb/s" % (rate/1000),
                          'yticklabels': ['0', '', '10', '', '20', '', '30'],
                          'ylabel': "Kernel CPU Util. (%)"})

        # This should be the stdev plot.
        plt_num += 1
        ax = fig.add_subplot(SUBPLOT_ROWS, SUBPLOT_COLS, plt_num)
        # Set yticks explicitly otherwise matplotlib does not seem to assign
        # tick for such a floating point ylim
        ax.set_yticks([0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3])
        plot_by_qty(ax,
                    {'rate': rate},
                    minor={'name': 'rl',
                           'data': rls},
                    major={'name': 'num_class',
                           'data': num_classes,
                           'label': "number of classes"},
                    fn_qty=lambda e,m,s: plot_ipt(e, m, s, rate),
                    opts={'ylim': (0, 0.3), 'legend': (plt_num == 2),
                          'annotate': "Rate: %d Gb/s" % (rate/1000),
                          'yticklabels': ['0', '', '0.1', '', '0.2', '', '0.3'],
                          'ylabel': "Normalized stddev"})

    plt.tight_layout()
    if args.out:
        plt.savefig(args.out)
    else:
        plt.show()
