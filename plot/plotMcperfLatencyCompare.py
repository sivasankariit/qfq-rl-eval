#!/usr/bin/env python

import argparse
import functools
import matplotlib
matplotlib.rcParams['backend'] = 'Agg'
import boomslang
import numpy
import os
import sys

from pickleExptLogs import readPickledFile
from expsiftUtils import *
from plotMcperfLatency import cdfLineFromHist
from plotCompare import plotLineComparisonDirs


parser = argparse.ArgumentParser(description='Plot mcperf latency comparisons')
parser.add_argument('expt_dirs', nargs='+', help='Experiment directories')
parser.add_argument('plot_filename', help='Filename for the graph')
parser.add_argument('-r', dest='recursive', action='store_true',
                    help='Recursively look for experiment directories under '
                         'each specified directory')


FOR_PAPER = True
LATENCY_LIMITS = (0, 20) if FOR_PAPER else (0, 50000)
LOAD_LIMITS = (1000, 7000)
RL_ORDER = { 'htb' : 1, 'eyeq' : 2, 'qfq' : 3, 'none' : 4 }
RL_LABEL = { 'htb' : 'htb', 'eyeq' : 'eyeq', 'qfq' : 'nicpic', 'none' : 'none' }


def sortLineValSets(line_val_sets):
    line_val_sets.sort(key = lambda line_val_set:
                       RL_ORDER[getUniqueProp(line_val_set)]),


def serverLoadFromMcrate(mcrate_val_set, mctenants = 1, numclients = 1):
    return int(getUniqueProp(mcrate_val_set)) * mctenants * numclients


def getAvgLatency(directory):
    # Read the mcperf pickle file and return the average latency
    mcperf_summary_pfile = os.path.join(
            directory, 'pickled/mcperf_summary_p.txt')
    mcperf_summary = readPickledFile(mcperf_summary_pfile)
    return mcperf_summary['lat_avg']


def getpc99Latency(directory):
    # Read the mcperf pickle file and return the average latency
    mcperf_summary_pfile = os.path.join(
            directory, 'pickled/mcperf_summary_p.txt')
    mcperf_summary = readPickledFile(mcperf_summary_pfile)
    return mcperf_summary['lat_pc99']


def getpc999Latency(directory):
    # Read the mcperf pickle file and return the average latency
    mcperf_summary_pfile = os.path.join(
            directory, 'pickled/mcperf_summary_p.txt')
    mcperf_summary = readPickledFile(mcperf_summary_pfile)
    return mcperf_summary['lat_pc999']


# Returns the CDF of latency line for the mcperf experiment directory
def getLatencyCDF(directory):
    # Read latency histogram from the mcperf pickled files
    mcperf_pfile = os.path.join(directory, 'pickled/mcperf_p.txt')
    agg_hist = readPickledFile(mcperf_pfile)

    if FOR_PAPER:
        # Convert usec sample values to msec
        agg_hist = {k / 1000.0: v for k, v in agg_hist.items()}

    return cdfLineFromHist(agg_hist)


# Find the client and server machines used for the experiment
def getServersAndClients(directory):
    # Read the hosts info pickle file
    hosts_pfile = os.path.join(directory, 'pickled/hosts_p.txt')
    (servers, clients) = readPickledFile(hosts_pfile)
    return (servers, clients)


# Returns the value of unique property
def getUniqueProp(unique_prop_set):
    assert(len(unique_prop_set) == 1)
    for prop_val_str in unique_prop_set:
        prop, val = propAndVal(prop_val_str)
        return val


# Returns latency CDF comparison graph. The graph plots one line for the CDF of
# each experiment directory.
def plotMcperfLatencyCDFComparisonDirs(dir2props_dict = {}):

    colors = ('b', 'g', 'r', 'm', 'c', 'y')

    # Find all the common and unique properties among all directories
    common_props, unique_props = getCommonAndUniqueProperties(dir2props_dict)

    plot = boomslang.Plot()

    # Check if all directories have only one unique property
    one_unique_prop = True

    for directory in dir2props_dict:
        if not len(unique_props[directory]) == 1:
            one_unique_prop = False

    # Sort the expt directories if only one unique property is available
    expt_dirs = dir2props_dict.keys()
    if one_unique_prop:
        expt_dirs.sort(key = lambda directory:
                       RL_ORDER.get(getUniqueProp(unique_props[directory]),
                                    len(RL_ORDER) + 1))

    # Iterate through directories and generate CDF lines for each of them
    for index, directory in enumerate(expt_dirs):

        cdf_line = getLatencyCDF(directory)

        cdf_line.color = colors[index % len(colors)]
        cdf_line.width = 2
        if one_unique_prop:
            unique_prop = getUniqueProp(unique_props[directory])
            cdf_line.label = RL_LABEL.get(unique_prop, unique_prop)
        else:
            cdf_line.label = ",".join(unique_props[directory])

        plot.add(cdf_line)

    # Set title and axes labels
    yLabel = "Fractiles"
    if FOR_PAPER:
        xLabel = "Latency (msec)"
        title = ''
    else:
        xLabel = "Memcached transaction latency (usec)"
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

    # Set xLimit (max latency plotted)
    plot.xLimits = LATENCY_LIMITS

    if FOR_PAPER:
        # Set dimensions of the plot
        plot.setDimensions(width=4.5)

    return plot


def plotMcperfLatencyComparisonDirsWrapper(dir2props_dict, stat='avg'):

    units = 'msec' if FOR_PAPER else 'usec'
    div = 1000.0 if FOR_PAPER else 1

    # Available stat functions: 'avg', 'pc99', 'pc999'
    if stat == 'avg':
        fn_get_datapoint = lambda directory: getAvgLatency(directory) / div
        yLabel = 'Average latency (%s)' % units
        title = 'Memcached response latency (average)'
    elif stat == 'pc99':
        fn_get_datapoint = lambda directory: getpc99Latency(directory) / div
        yLabel = '99th perc. latency (%s)' % units
        title = 'Memcached response latency (99th percentile)'
    elif stat == 'pc999':
        fn_get_datapoint = lambda directory: getpc999Latency(directory) / div
        yLabel = '99.9th perc. latency (%s)' % units
        title = 'Memcached response latency (99.9th percentile)'

    if FOR_PAPER:
        title = ''

    # Turn each directory's set of prop=val strings into a dictionary to
    # easily look up the value of a particular property for the directory
    dir2prop2val_dict = getDir2Prop2ValDict(dir2props_dict)

    # Make sure that all the experiments had the same number of client/server
    # machines and number of tenants.
    mctenants_vals = set()
    trafgentenants_vals = set()
    for directory in dir2props_dict.iterkeys():
        mctenants_vals.add(dir2prop2val_dict[directory]['mctenants'])
        trafgentenants_vals.add(dir2prop2val_dict[directory]['trafgentenants'])
    assert(len(mctenants_vals) == 1)
    assert(len(trafgentenants_vals) == 1)
    mctenants = int(mctenants_vals.pop())

    # Make sure that all the experiments had the same number of client and
    # server machines
    numclients_vals = set()
    numservers_vals = set()
    for directory in dir2props_dict.iterkeys():
        servers, clients = getServersAndClients(directory)
        numclients_vals.add(len(clients))
        numservers_vals.add(len(servers))
    assert(len(numclients_vals) == 1)
    assert(len(numservers_vals) == 1)
    numclients = numclients_vals.pop()

    # Function to convert mcrate value to total server load
    # fn_get_xgroup_value = functools.partial(serverLoadFromMcrate,
    #                                         mctenants = mctenants,
    #                                         numclients = numclients)
    # Load per tenant per client
    fn_get_xgroup_value = (lambda mcrate_val_set:
        int(getUniqueProp(mcrate_val_set)))

    return plotLineComparisonDirs(
            dir2props_dict,

            xgroup_props = ['mcrate'],
            line_props = ['rl'],

            fn_sort_lines = lambda lines: sortLineValSets(lines),

            fn_get_line_label = (lambda line_val_set:
                RL_LABEL[getUniqueProp(line_val_set)]),

            fn_get_xgroup_value = fn_get_xgroup_value,

            fn_get_datapoint = fn_get_datapoint,

            xLabel = 'Load per tenant per client (reqs/sec)',
            yLabel = yLabel,
            title = title,
            xLimits = LOAD_LIMITS,
            yLimits = LATENCY_LIMITS,
            for_paper = FOR_PAPER)


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
    #mclat_plot = plotMcperfLatencyComparisonDirsWrapper(dir2props_dict, 'avg')
    #mclat_plot = plotMcperfLatencyComparisonDirsWrapper(dir2props_dict, 'pc99')
    #mclat_plot = plotMcperfLatencyComparisonDirsWrapper(dir2props_dict, 'pc999')
    mclat_plot.save(args.plot_filename)


if __name__ == '__main__':
    main(sys.argv)
