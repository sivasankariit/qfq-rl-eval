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
from output_parser import SnifferParser

# 24 bytes framing overhead per packet in Ethernet
FRAMING_OVERHEAD = 24

parser = argparse.ArgumentParser(description="Plot for IPG")
parser.add_argument('--file', '-f',
                    help="Sniffer output to parse",
                    required=True)

parser.add_argument('--rate', '-r',
                    type=float,
                    help="Line rate in Gb/s",
                    default=10)

parser.add_argument('--out', '-o',
                    help="save plot to file")

args = parser.parse_args()

def ideal_ipt_nsec(packet_len, rate_gbps):
    return (packet_len + FRAMING_OVERHEAD) * 8 / (rate_gbps)

def plot_file(file):
    sniff = SnifferParser(file)
    print "Seen packet lengths", sniff.seen_packet_len
    if len(sniff.seen_packet_len) != 1:
        print 'Saw more than one packet length on wire'
    data = sniff.get_ipt()
    x, y = cdf_list(data)
    plt.plot(x, y, lw=2)

    avg, pc99 = sniff.summary()
    ideal = ideal_ipt_nsec(sniff.seen_packet_len[0], args.rate)

    print "Ideal: %.3f \nMean: %.3f \n99thpcile: %.3f" % (ideal, avg, pc99)

    plt.axvline(avg, lw=2, ls='--', color='green')
    plt.axvline(pc99, lw=2, ls='--', color='red')
    plt.axvline(ideal, lw=2, ls='-.', color='magenta', alpha=0.8)

    plt.xlabel("Inter-packet time in nanosec")
    plt.ylabel("fractiles")
    plt.title("CDF of inter-packet _time_ (not inter-packet gap) in nanosec")
    if args.out:
        print 'saved cdf to', args.out
        plt.savefig(args.out)
    else:
        print 'displaying plot...'
        plt.show()

plot_file(args.file)
