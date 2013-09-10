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


def sortLineValSets(line_val_sets):
    rl_order = { 'htb' : 1, 'qfq' : 2, 'eyeq' : 3, 'none' : 4}
    line_val_sets.sort(key = lambda line_val_set:
                       rl_order[getUniqueProp(line_val_set)]),


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

    return cdfLineFromHist(agg_hist)


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


# Returns the comparison of mcperf latency summaries. Each experiment's latency
# distribution is reduced to a single datapoint, Eg. avg, pc99, pc999 etc.
def plotMcperfLatencyComparisonDirs(dir2props_dict, # dict
                                    xgroup_props,   # list. Props to group along x axis
                                    line_props,     # list. Properties of line
                                    fn_sort_lines,
                                    fn_get_line_label,
                                    fn_get_xgroup_value,  # xValue. No separate label
                                    fn_get_datapoint,     # yValue
                                    xLabel,
                                    yLabel,
                                    title,
                                    yLimits = None):

    # 1. Turn each directory's set of prop=val strings into a dictionary to
    #     easily look up the value of a particular property for the directory
    dir2prop2val_dict = getDir2Prop2ValDict(dir2props_dict)


    # 2. Find all the common and unique properties among all directories
    common_props, unique_props = getCommonAndUniqueProperties(dir2props_dict)


    # 3A. Find all unique values of line properties (each is separate line)
    line2dir_dict = getDirGroupsByProperty(dir2props_dict, line_props,
                                           ignore = False)
    unique_lines = line2dir_dict.keys()
    # 3B. Sort the lines
    fn_sort_lines(unique_lines)


    # 4. Find all unique values of the xgroup properties
    xgroup2dir_dict = getDirGroupsByProperty(dir2props_dict, xgroup_props,
                                             ignore = False)
    unique_xgroups = xgroup2dir_dict.keys()


    # 5. For each unique line,
    #    For each unique xgroup,
    #        Create an individual datapoints list
    datapoints_dict = {}
    for line in unique_lines:
        datapoints_dict[line] = {}
        for xgroup in unique_xgroups:
            datapoints_dict[line][xgroup] = []


    # 6. Visit each directory and populate the corresponding datapoints list for
    #    that directory.
    for directory, prop_vals in dir2props_dict.iteritems():
        # Find the line and xgroup of the directory
        line = onlyIncludeProps(prop_vals, line_props)
        xgroup = onlyIncludeProps(prop_vals, xgroup_props)

        # Compute the datapoint for the directory
        datapoint = fn_get_datapoint(directory)

        # Add the data point
        datapoints_dict[line][xgroup].append(datapoint)


    # 7. For each unique line prop, create a line.
    #    Set the label and color for the line
    colors = ('b', 'g', 'r', 'm', 'c', 'y')
    all_lines_dict = {}
    for index, line in enumerate(unique_lines):
        l = boomslang.Line()
        l.color = colors[index % len(colors)]
        l.label = fn_get_line_label(line)
        l.width = 2
        l.marker = 'o'
        all_lines_dict[line] = l


    # 8. Compute average and stddev for each (line, xgroup) combination. This
    #    represents the avg and stddev across multiple trials.
    #    Add these to the corresponding lines.
    for line, line_dict in datapoints_dict.iteritems():
        for xgroup, datapoints in line_dict.iteritems():
            avg = numpy.average(datapoints)
            stddev = numpy.std(datapoints)

            # Append xValue, yValue, yError to the line
            xValue = fn_get_xgroup_value(xgroup)
            all_lines_dict[line].xValues.append(xValue)
            all_lines_dict[line].yValues.append(avg)
            all_lines_dict[line].yErrors.append(stddev)


    # 9. Create the plot and add all the lines
    plot = boomslang.Plot()
    for line in unique_lines:
        plot.add(all_lines_dict[line])

    # 9A. Set title and axes labels
    plot.setXLabel(xLabel)
    plot.setYLabel(yLabel)
    plot.setTitle(title)
    plot.hasLegend()

    # 9B. Font size
    plot.setLegendLabelSize("small")
    plot.setTitleSize("small")
    plot.setAxesLabelSize("small")
    plot.setXTickLabelSize("small")
    plot.setYTickLabelSize("small")

    # 9C. Grid
    plot.grid.color = "lightgray"
    plot.grid.style = "dotted"
    plot.grid.lineWidth = 0.8
    plot.grid.visible = True

    # 9D. yLimits
    if yLimits:
        plot.yLimits = yLimits


    # 10. Return the plot
    return plot


def plotMcperfLatencyComparisonDirsWrapper(dir2props_dict, stat='avg'):

    # Available stat functions: 'avg', 'pc99', 'pc999'
    if stat == 'avg':
        fn_get_datapoint = lambda directory: getAvgLatency(directory)
        yLabel = 'Average latency (usec)'
        title = 'Memcached response latency (average)'
    elif stat == 'pc99':
        fn_get_datapoint = lambda directory: getpc99Latency(directory)
        yLabel = '99th perc. latency (usec)'
        title = 'Memcached response latency (99th percentile)'
    elif stat == 'pc999':
        fn_get_datapoint = lambda directory: getpc999Latency(directory)
        yLabel = '99.9th perc. latency (usec)'
        title = 'Memcached response latency (99.9th percentile)'

    return plotMcperfLatencyComparisonDirs(
            dir2props_dict,

            xgroup_props = ['mcrate'],
            line_props = ['rl'],

            fn_sort_lines = lambda lines: sortLineValSets(lines),

            fn_get_line_label = (lambda line_val_set:
                getUniqueProp(line_val_set)),

            fn_get_xgroup_value = (lambda xgroup_val_set:
                getUniqueProp(xgroup_val_set)),

            fn_get_datapoint = fn_get_datapoint,

            xLabel = 'Load on server (reqs per sec)',
            yLabel = yLabel,
            title = title,
            yLimits = (0, 50000))


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
