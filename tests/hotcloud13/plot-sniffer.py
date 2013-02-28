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

parser = argparse.ArgumentParser(description="Plot for IPG")
parser.add_argument('--file', '-f',
                    help="Sniffer output to parse",
                    required=True)

parser.add_argument('--out', '-o',
                    help="save plot to file")

args = parser.parse_args()


def plot_file(file):
    sniff = SnifferParser(file)
    data = sniff.get_ipt()
    x, y = cdf_list(data)
    plt.plot(x, y, lw=2)

    avg, pc99 = sniff.summary()
    plt.axvline(avg, lw=2, ls='--', color='green')
    plt.axvline(pc99, lw=2, ls='--', color='red')
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
