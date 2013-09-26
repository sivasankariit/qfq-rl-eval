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
from plotMcperfLatencyCompare import plotMcperfLatencyCDFComparisonDirs
import plotMcperfLatencyCompare


parser = argparse.ArgumentParser(description='Plot mcperf latency comparisons')
parser.add_argument('plot_filename', help='Filename for the graph')


plotMcperfLatencyCompare.FOR_PAPER = True
plotMcperfLatencyCompare.LATENCY_LIMITS = (0, 1.5)
plotMcperfLatencyCompare.RL_ORDER = { 'htb' : 1, 'eyeq' : 2, 'qfq' : 3, 'none' : 4 }
plotMcperfLatencyCompare.RL_LABEL = { 'htb' : 'HTB', 'eyeq' : 'PTB', 'qfq' : 'SENIC', 'none' : 'none' }


def main(argv):
    # Parse flags
    args = parser.parse_args()

    expt_dirs_2000 = ['../test_scripts/nsdi-paper-data/Sep21--10-34-combine/memcached-rl-htb-mcrate-2000-mctenants-10-trafgentenants-0-run-1/',
                      '../test_scripts/nsdi-paper-data/Sep21--10-34-combine/memcached-rl-qfq-mcrate-2000-mctenants-10-trafgentenants-0-run-1/',
                      '../test_scripts/nsdi-paper-data/Sep21--10-34-combine/memcached-rl-eyeq-mcrate-2000-mctenants-10-trafgentenants-0-run-1/']

    expt_dirs_3000 = ['../test_scripts/nsdi-paper-data/Sep21--10-34-combine/memcached-rl-htb-mcrate-3000-mctenants-10-trafgentenants-0-run-1/',
                      '../test_scripts/nsdi-paper-data/Sep21--10-34-combine/memcached-rl-qfq-mcrate-3000-mctenants-10-trafgentenants-0-run-1/',
                      '../test_scripts/nsdi-paper-data/Sep21--10-34-combine/memcached-rl-eyeq-mcrate-3000-mctenants-10-trafgentenants-0-run-1/']

    # Read the properties for each directory from the expsift tags files
    dir2props_dict_2000 = getDir2PropsDict(expt_dirs_2000)
    dir2props_dict_3000 = getDir2PropsDict(expt_dirs_3000)

    # Plot memcached latency comparison graph (msec)
    mclat_plot_2000 = plotMcperfLatencyCDFComparisonDirs(dir2props_dict_2000)
    mclat_plot_3000 = plotMcperfLatencyCDFComparisonDirs(dir2props_dict_3000)

    # Specify the xTicks values to display
    ticklabels_line_2000 = boomslang.Line()
    ticklabels_line_2000.xTickLabels = [0.5, 1.0, 1.5]
    ticklabels_line_2000.xTickLabelPoints = [0.5, 1.0, 1.5]
    mclat_plot_2000.add(ticklabels_line_2000)
    ticklabels_line_3000 = boomslang.Line()
    ticklabels_line_3000.xTickLabels = [0.5, 1.0, 1.5]
    ticklabels_line_3000.xTickLabelPoints = [0.5, 1.0, 1.5]
    mclat_plot_3000.add(ticklabels_line_3000)

    # Set title and legend
    mclat_plot_2000.title = "2000 rpstc"
    mclat_plot_3000.title = "3000 rpstc"
    mclat_plot_3000.setYLabel('')
    mclat_plot_3000.legend = None
    mclat_plot_2000.hasLegend(location="lower right")
    mclat_plot_2000.setLegendLabelSize("small")

    # Plot layout
    layout = boomslang.PlotLayout()
    layout.addPlot(mclat_plot_2000, grouping='lat_cdfs')
    layout.addPlot(mclat_plot_3000, grouping='lat_cdfs')
    layout.setFigureDimensions(5, 3)

    # Save the plot
    layout.save(args.plot_filename)
    return


if __name__ == '__main__':
    main(sys.argv)
