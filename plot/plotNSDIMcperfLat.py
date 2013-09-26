#!/usr/bin/env python

import argparse
import functools
import matplotlib
matplotlib.rcParams['backend'] = 'Agg'
import boomslang
import numpy
import os
import sys

from expsiftUtils import *
from plotMcperfLatencyCompare import plotMcperfLatencyComparisonDirsWrapper
import plotMcperfLatencyCompare


parser = argparse.ArgumentParser(description='Plot mcperf latency comparisons')
parser.add_argument('plot_filename', help='Filename for the graph')
parser.add_argument('--dataset', default=0, type=int, help='mcperf_only=0/iso=1')


plotMcperfLatencyCompare.FOR_PAPER = True
plotMcperfLatencyCompare.LATENCY_LIMITS = (0, 20)
plotMcperfLatencyCompare.LOAD_LIMITS = (1000, 7000)
plotMcperfLatencyCompare.RL_ORDER = { 'htb' : 1, 'eyeq' : 2, 'qfq' : 3, 'none' : 4 }
plotMcperfLatencyCompare.RL_LABEL = { 'htb' : 'HTB', 'eyeq' : 'PTB', 'qfq' : 'SENIC', 'none' : 'none' }


def main(argv):
    # Parse flags
    args = parser.parse_args()

    if args.dataset == 0:
        expt_dirs_base = ['../test_scripts/nsdi-paper-data/Sep21--10-34-combine/']
        plotMcperfLatencyCompare.LOAD_LIMITS = (1000, 7000)
    elif args.dataset == 1:
        expt_dirs_base = ['../test_scripts/nsdi-paper-data/Sep20--07-02-iso-combine/']
        plotMcperfLatencyCompare.LOAD_LIMITS = (1000, 5000)
    else:
        print 'Unknown dataset'
        return

    expt_dirs = []
    for directory in expt_dirs_base:
        directory = os.path.abspath(directory)
        for (path, dirs, files) in os.walk(directory, followlinks=True):
            # Check if an experiment directory was found
            if os.path.exists(os.path.join(path, 'expsift_tags')):
                #print 'Found experiment directory:', path
                expt_dirs.append(path)
    print 'Found %d experiment directories to compare' % len(expt_dirs)

    # Read the properties for each directory from the expsift tags files
    dir2props_dict = getDir2PropsDict(expt_dirs)

    # Plot memcached latency comparison graphs (msec)
    avg_plot = plotMcperfLatencyComparisonDirsWrapper(dir2props_dict, 'avg')
    pc99_plot = plotMcperfLatencyComparisonDirsWrapper(dir2props_dict, 'pc99')
    pc999_plot = plotMcperfLatencyComparisonDirsWrapper(dir2props_dict, 'pc999')

    # Set xLabel
    avg_plot.setXLabel("Load (rpstc)")
    pc99_plot.setXLabel("Load (rpstc)")
    pc999_plot.setXLabel("Load (rpstc)")

    # Set yLabel
    avg_plot.setYLabel("Latency (msec)")
    pc99_plot.setYLabel("Latency (msec)")
    pc999_plot.setYLabel("Latency (msec)")

    # Title
    avg_plot.title = "Average"
    pc99_plot.title = "99th percentile"
    pc999_plot.title = "99.9th percentile"

    # Tick labels
    xmin,xmax = plotMcperfLatencyCompare.LOAD_LIMITS
    xTickLabels = range(xmin, xmax+1, 1000)
    ticklabels_line = boomslang.Line()
    ticklabels_line.xTickLabels = xTickLabels
    ticklabels_line.xTickLabelPoints = xTickLabels
    avg_plot.add(ticklabels_line)
    pc99_plot.add(ticklabels_line)
    pc999_plot.add(ticklabels_line)

    # Label sizes
    avg_plot.setXTickLabelSize("small")
    pc99_plot.setXTickLabelSize("small")
    pc999_plot.setXTickLabelSize("small")
    avg_plot.setYTickLabelSize("small")
    pc99_plot.setYTickLabelSize("small")
    pc999_plot.setYTickLabelSize("small")
    avg_plot.setTitleSize("small")
    pc99_plot.setTitleSize("small")
    pc999_plot.setTitleSize("small")

    # Plot layout
    layout = boomslang.PlotLayout()
    layout.addPlot(avg_plot, grouping='throuput')
    layout.addPlot(pc99_plot, grouping='throuput')
    layout.addPlot(pc999_plot, grouping='throuput')
    layout.setFigureDimensions(13.5, 3)

    # Save the plot
    layout.save(args.plot_filename)
    return


if __name__ == '__main__':
    main(sys.argv)
