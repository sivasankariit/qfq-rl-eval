#!/usr/bin/env python

import argparse
import matplotlib
matplotlib.rcParams['backend'] = 'Agg'
import boomslang
import numpy
import os
import sys

from pickleExptLogs import readPickledFile
from expsiftUtils import *
from plotMcperfLatency import cdfLineFromHist


parser = argparse.ArgumentParser(description='Plot mcperf latency comparisons')
parser.add_argument('expt_dirs', nargs='+', help='Experiment directories')
parser.add_argument('plot_filename', help='Filename for the graph')
parser.add_argument('-r', dest='recursive', action='store_true',
                    help='Recursively look for experiment directories under '
                         'each specified directory')


# Returns the CDF of latency line for the mcperf experiment directory
def getLatencyCDF(directory):
    # Read latency histogram from the mcperf pickled files
    mcperf_pfile = os.path.join(directory, 'pickled/mcperf_p.txt')
    agg_hist = readPickledFile(mcperf_pfile)

    return cdfLineFromHist(agg_hist)


# Returns the value of unique property
def getUniqueProp(unique_prop):
    assert(len(unique_prop) == 1)
    for prop_val_str in unique_prop:
        prop, val = propAndVal(prop_val_str)
        return val


# Returns latency CDF comparison graph
def plotMcperfLatencyCDFComparisonDirs(dir2props_dict = {}):

    colors = ('b', 'g', 'r', 'm', 'c', 'y')

    # Find all the common and unique properties among all directories
    common_props, unique_props = getCommonAndUniqueProperties(dir2props_dict)

    plot = boomslang.Plot()

    # Check if all directories have only one unique property
    one_unique_prop = True
    for directory in dir2props_dict:
        if not len(unique_props[directory]) == 1:
            oneUniqueProp = False

    # Iterate through directories and generate CDF lines for each of them
    for index, directory in enumerate(dir2props_dict.keys()):

        cdf_line = getLatencyCDF(directory)

        cdf_line.color = colors[index % len(colors)]
        cdf_line.width = 2
        if one_unique_prop:
            cdf_line.label = getUniqueProp(unique_props[directory])
        else:
            cdf_line.label = ",".join(unique_props[directory])

        plot.add(cdf_line)

    # Set title and axes labels
    xLabel = "Memcached transaction latency (usecs)"
    yLabel = "Fractiles"
    title = "CDF of memcached transaction latency"
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


def main(argv):
    # Parse flags
    args = parser.parse_args()

    # Generate the list of experiment directories to compare
    expt_dirs = []
    if args.recursive:
        for directory in args.expt_dirs:
            directory = os.path.abspath(directory)
            for (path, dirs, files) in os.walk(directory, followlinks=True):
                # Check if an experiment directory was found
                if os.path.exists(os.path.join(path, 'expsift_tags')):
                    #print 'Found experiment directory:', path
                    expt_dirs.append(path)
        print 'Found %d experiment directories to compare' % len(expt_dirs)
    else:
        expt_dirs = args.expt_dirs

    # Check if any experiment directories were found or not
    if len(expt_dirs) == 0:
        return

    # Read the properties for each directory from the expsift tags files
    dir2props_dict = getDir2PropsDict(expt_dirs)

    # Plot memcached latency comparison graph (microseconds)
    mclat_plot = plotMcperfLatencyCDFComparisonDirs(dir2props_dict)
    mclat_plot.save(args.plot_filename)


if __name__ == '__main__':
    main(sys.argv)
