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

parser = argparse.ArgumentParser(description="Plot netperf experiment outputs.")
parser.add_argument('--rr',
                    nargs="+",
                    help="rr files to parse")

parser.add_argument('--labels',
                    nargs="+",
                    help="labels on rr plot")

parser.add_argument('--ss-dir',
                    nargs="+",
                    help="stream output directories")

parser.add_argument('--out', '-o',
                    help="save plot to file")

parser.add_argument('--ymin',
                    type=float,
                    help="zoom into (ymin,1) on yaxis")

parser.add_argument('--ymax',
                    type=int,
                    help="zoom into (0,ymax) on yaxis")

parser.add_argument('--xlog',
                    action="store_true",
                    help="make x-axis log scale")

parser.add_argument('--normalise',
                    action="store_true",
                    help="make x-axis log scale")

parser.add_argument('--plot_every',
                    action="store_true",
                    help="plot all rr points")

args = parser.parse_args()
rspaces = re.compile(r'\s+')
plot_defaults.rcParams['figure.figsize'] = 4, 3.5

def cdf(lst):
    vals = []
    nums = []
    cum = 0
    for val, num in lst:
        cum += num
        vals.append(val)
        nums.append(cum)
    return vals, map(lambda n: n*1.0/cum, nums)

def plot_cdf(x, y, **opts):
    #plt.figure()
    plt.plot(x, y, **opts)
    if args.xlog:
        plt.xscale("log")
    #plt.show()


class STParser:
    def __init__(self, filename):
        self.filename = filename
        self.lines = open(filename).readlines()
        self.done = False
        try:
            self.parse()
            self.done = True
        except:
            print 'error parsing %s' % filename
        return

    def parse(self):
        mbps_line = self.lines[6]
        fields = rspaces.split(mbps_line)
        self.mbps = float(fields[5])
        self.cpu_local = float(fields[6])
        return

class RRParser:
    def __init__(self, filename):
        self.filename = filename
        self.lines = open(filename).readlines()
        self.done = False
        try:
            self.parse()
            self.done = True
        except:
            print 'error parsing %s' % filename

    def parse(self):
        tps_line = self.lines[6]
        fields = rspaces.split(tps_line)
        self.tps = float(fields[5])
        self.cpu_local = float(fields[6])
        self.cpu_remote = float(fields[7])

        lat_line = self.lines[11]
        fields = rspaces.split(lat_line)
        self.latency = float(fields[4])
        self.mbps_out = float(fields[6])
        self.mbps_in = float(fields[7])
        self.parse_histogram()
        return

    def parse_histogram(self):
        unit = 1
        rsep = re.compile(r':\s+')
        ret = defaultdict(int)
        def parse_buckets(line):
            nums = line.split(":", 1)[1]
            nums = map(lambda e: int(e.strip()),
                       rsep.split(nums))
            return nums
        for lno in xrange(14, 22):
            nums = parse_buckets(self.lines[lno])
            for i,n in enumerate(nums):
                ret[unit+i*unit] += n
            unit *= 10
        ret = sorted(list(ret.iteritems()))
        self.histogram = ret
        return ret

def parse_st(dir):
    total_mbps = 0.0
    total_cpu_local = 0.0
    num_files = 0
    for f in glob.glob(os.path.join("%s/*" % dir)):
        r = STParser(f)
        if not r.done:
            continue
        total_mbps += r.mbps
        total_cpu_local += r.cpu_local
        num_files += 1
    avg_cpu_local = total_cpu_local / num_files
    return (dir, total_mbps, avg_cpu_local)

def plot_vbar(heights, start, skip, **kwargs):
    N = len(heights)
    xs = start + skip * numpy.arange(0, N)
    return plt.bar(xs, heights, width=1, **kwargs)

def plot_rr(dir, **kwargs):
    hist = defaultdict(int)
    total_tps = 0
    total_out_mbps = 0
    total_in_mbps = 0
    total_cpu_remote = 0
    def combine(hnew):
        for val,num in hnew:
            hist[val] += num
        return
    files = list(glob.glob(dir + "/rr-*"))
    print "%d output files..." % len(files)
    for f in files:
        r = RRParser(f)
        if not r.done:
            continue
        c = cdf(r.histogram)
        combine(r.histogram)
        if args.plot_every:
            plot_cdf(c[0], c[1], alpha=0.1)

        total_tps += r.tps
        total_out_mbps += r.mbps_out
        total_in_mbps += r.mbps_in
        total_cpu_remote += r.cpu_remote
    agg_cdf = cdf(sorted(list(hist.iteritems())))
    plot_cdf(agg_cdf[0], agg_cdf[1], **kwargs)
    plt.xlim((0, 2e3))
    #plt.figure(1).get_axes()[0].yaxis.set_major_locator(mp.ticker.MaxNLocator(10))
    plt.grid(True)
    plt.xlabel("usec")
    plt.ylabel("fraction")
    #title = "Total tps: %.3f / %.3fMbps IN / %.2f%%CPU" % (total_tps, total_in_mbps, total_cpu_remote / len(args.rr))
    #title += '\n(norm: %.3f Mbps/CPU%%) ' % (total_in_mbps/(total_cpu_remote/len(args.rr)))
    #plt.title(title)
    if args.ymin is not None:
        plt.ylim((args.ymin, 1))

def mean(l):
    return sum(l) * 1.0 / len(l)

def stdev(l):
    m = mean(l)
    sq = mean(map(lambda e: e * e, l))
    return math.sqrt(sq - m * m)

def process_series(lst):
    trans = zip(*lst)
    ret = []
    err = []
    for l in trans:
        l = list(l)
        ret.append(mean(l))
        err.append(stdev(l) / math.sqrt(len(l)))
    return ret, err

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
