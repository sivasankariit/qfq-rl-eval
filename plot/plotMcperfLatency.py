#!/usr/bin/env python

import argparse
import matplotlib
matplotlib.rcParams['backend'] = 'Agg'
import boomslang
import numpy
import os
import sys

from pickleExptLogs import readPickledFile


parser = argparse.ArgumentParser(description='Plot mcperf latency data')
parser.add_argument('expt_dir', help='Experiment directory')
parser.add_argument('plotfile_prefix',
                    help='Filename prefix for output graphs')
parser.add_argument('--force_replot', '-f', dest='force_replot',
                    help='Replot graphs even if they already exist ',
                    action="store_true")


# Return a CDF line from histogram data
#
# @hist : List of tuples representing the histogram. Each tuple contains the
#         sample value and frequency
def cdfLineFromHist(hist, color="blue", width=2):
    sorted_hist = sorted(hist.items())
    cum_sum = numpy.cumsum(map(lambda (k,v): v, sorted_hist))
    num_samples = cum_sum[-1]

    cdf_line = boomslang.Line(color=color, width=width)
    cdf_line.xValues = map(lambda (k,v): k, sorted_hist)
    cdf_line.yValues = map(lambda y: y * 1.0 / num_samples, cum_sum)

    return cdf_line


# Plot a CDF graph from histogram data with 4 kinds of lines
# 1. CDF Line   : CDF in blue color
# 2. Avg VLine  : Average in green color
# 3. pc99 VLine : (99th percentile) in red color
# 4. pc99 VLine : (99.9th percentile) in magenta color
#
# @hist : List of tuples representing the histogram. Each tuple contains the
#         sample value and frequency
def plotCDFGraphFromHist(hist, avg, pc99, pc999,
                         xLabel, yLabel, title):

    plot = boomslang.Plot()

    # Plot the CDF line
    cdf_line = cdfLineFromHist(hist, color="blue", width=2)
    plot.add(cdf_line)

    # Plot VLine for avg
    avg_vline = boomslang.VLine(color="green", lineStyle="--")
    avg_vline.xValues = [avg]
    avg_vline.label = "Avg."
    plot.add(avg_vline)

    # Plot VLine for pc99
    pc99_vline = boomslang.VLine(color="red", lineStyle="--")
    pc99_vline.xValues = [pc99]
    pc99_vline.label = "99th perc."
    plot.add(pc99_vline)

    # Plot VLine for pc999
    pc999_vline = boomslang.VLine(color="magenta", lineStyle="--")
    pc999_vline.xValues = [pc999]
    pc999_vline.label = "99.9th perc."
    plot.add(pc999_vline)

    # Set title and axes labels
    plot.setXLabel(xLabel)
    plot.setYLabel(yLabel)
    plot.setTitle(title)
    plot.hasLegend()

    # Font size
    plot.setLegendLabelSize("small")
    plot.setTitleSize("small")
    plot.setAxesLabelSize("small")
    plot.setXTickLabelSize("small")
    plot.setYTickLabelSize("small")

    # Grid
    plot.grid.color = "lightgray"
    plot.grid.style = "dotted"
    plot.grid.lineWidth = 0.8
    plot.grid.visible = True

    return plot


# Plot CDF of burst lengths in packets for each traffic class
def plotMcperfLatency(directory):
    # Read latency histogram from the mcperf pickled files
    mcperf_pfile = os.path.join(directory, 'pickled/mcperf_p.txt')
    mcperf_summary_pfile = os.path.join(
            directory, 'pickled/mcperf_summary_p.txt')
    agg_hist = readPickledFile(mcperf_pfile)
    mcperf_summary = readPickledFile(mcperf_summary_pfile)

    return plotCDFGraphFromHist(agg_hist, mcperf_summary['lat_avg'],
                                mcperf_summary['lat_pc99'],
                                mcperf_summary['lat_pc999'],
                                "Memcached transaction latency (usecs)",
                                "Fractiles",
                                "CDF of memcached transaction latency")


def main(argv):
    # Parse flags
    args = parser.parse_args()

    # Plot memcached latency in microseconds
    if (args.force_replot or
        not os.path.exists(args.plotfile_prefix + 'mcperf_lat_cdf.png')):
        mclat_plot = plotMcperfLatency(args.expt_dir)
        mclat_plot.save(args.plotfile_prefix + 'mcperf_lat_cdf.png')


if __name__ == '__main__':
    main(sys.argv)
