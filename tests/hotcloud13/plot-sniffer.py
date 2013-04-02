#!/usr/bin/python
import sys
import os

sys.path.append(os.getcwd())
sys.path.insert(0, os.path.abspath('../'))

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
from output_parser import SnifferParser

# 24 bytes framing overhead per packet in Ethernet
FRAMING_OVERHEAD = 24

parser = argparse.ArgumentParser(description="Plot for IPG")
parser.add_argument('--file', '-f',
                    help="Sniffer output to parse",
                    required=True)

parser.add_argument('--rate', '-r',
                    type=float,
                    help="Total rate in Gb/s",
                    default=10)

parser.add_argument('--num-classes', '-n',
                    type=float,
                    help="Number of classes",
                    default=1)

parser.add_argument('--out', '-o',
                    help="save plot to file")

parser.add_argument('--burstout', '-b',
                    help="save burst length plot to file")

parser.add_argument('--divisor',
                    help="Divide x-axis data by this value",
                    default=1000)

parser.add_argument('--max-samples', '--max',
                    dest='max',
                    type=int,
                    help="Maximum samples to parse",
                    default=10000)

args = parser.parse_args()

def ideal_ipt_nsec(packet_len, rate_gbps):
    return (packet_len + FRAMING_OVERHEAD) * 8 / (rate_gbps)

def plot_file(file):
    units = 'nanosec'
    if args.divisor == 1000:
        units = 'microsec'
    sniff = SnifferParser(file, max_lines=args.max)
    print "Seen packet lengths", sniff.seen_packet_len
    if len(sniff.seen_packet_len) != 1:
        print 'Saw more than one packet length on wire'

    # Plot inter-packet arrival times
    plt.figure()
    for port in sniff.get_ipt().keys():
        data = sniff.get_ipt()[port]
        xs, ys = cdf_list(data)
        xs = map(lambda e: e/args.divisor, xs)
        plt.plot(xs, ys, lw=2, label=str(port))

    #plt.legend(loc="upper right", bbox_to_anchor=(1.2, 1))
    d = sniff.summary()

    ideal = ideal_ipt_nsec(sniff.seen_packet_len[0], args.rate / args.num_classes)
    print ideal, d
    plt.axvline(ideal / args.divisor, lw=2, ls='-.', color='magenta', alpha=0.8)
    for port in d.keys():
        avg, pc99 = d[port]
        plt.axvline(avg / args.divisor, lw=2, ls='--', color='green')
        plt.axvline(pc99 / args.divisor, lw=2, ls='--', color='red')

    #plt.axvline(avg, lw=2, ls='--', color='green')
    #plt.axvline(pc99, lw=2, ls='--', color='red')
    #plt.axvline(ideal, lw=2, ls='-.', color='magenta', alpha=0.8)

    plt.xlabel("Inter-packet time in %s" % units)
    plt.ylabel("fractiles")
    plt.title("CDF of inter-packet _time_ (not inter-packet gap) in %s" % units)
    if args.out:
        print 'saved cdf to', args.out
        plt.savefig(args.out)
        if args.out.endswith('.pdf'):
            zoomed = args.out[:-4] + "_zoomed.pdf"
            ideals = [10000, 15000, 20000, 30000, 40000]
            for cutoff in ideals:
                if ideal < cutoff:
                    plt.xlim((0, cutoff / args.divisor))
                    break
            plt.title("CDF of inter-packet _time_ (not inter-packet gap) in %s [zoomed]" % units)
            plt.savefig(zoomed)
            print 'saved zoomed cdf to', zoomed
    else:
        print 'displaying plot...'
        plt.show()

    if not args.burstout:
        return

    # Plot burst lengths
    plt.figure()
    for port in sniff.get_burstlen().keys():
        data = sniff.get_burstlen()[port]
        xs, ys = cdf_list(data)
        xs = map(lambda e: e, xs)
        plt.plot(xs, ys, lw=2, label=str(port))

    #plt.legend(loc="upper right", bbox_to_anchor=(1.2, 1))
    d = sniff.summary_burstlen()
    print "burst lengths"
    print d
    for port in d.keys():
        avg, pc99 = d[port]
        plt.axvline(avg, lw=2, ls='--', color='green')
        plt.axvline(pc99, lw=2, ls='--', color='red')

    plt.xlabel("Burst length in packets")
    plt.ylabel("fractiles")
    plt.title("CDF of burst lengths in packets")
    print 'saved burst length cdf to', args.burstout
    plt.savefig(args.burstout)

    # Plot burst times (burst length in microsecs)
    plt.figure()
    for port in sniff.get_bursttime().keys():
        data = sniff.get_bursttime()[port]
        xs, ys = cdf_list(data)
        xs = map(lambda e: e/args.divisor, xs)
        plt.plot(xs, ys, lw=2, label=str(port))

    d = sniff.summary_bursttime()
    print "burst times"
    print d
    for port in d.keys():
        avg, pc99 = d[port]
        plt.axvline(avg / args.divisor, lw=2, ls='--', color='green')
        plt.axvline(pc99 / args.divisor, lw=2, ls='--', color='red')

    plt.xlabel("Burst length in %s" % units)
    plt.ylabel("fractiles")
    plt.title("CDF of burst lengths in %s" % units)
    timecdf = args.burstout[:-4] + "_time.pdf"
    print 'saved burst time cdf to', timecdf
    plt.savefig(timecdf)

plot_file(args.file)
