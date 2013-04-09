#!/usr/bin/env python

import argparse
import boomslang
import numpy
import os
import sys

from MPStatParser import MPStatParser
from pickleExptLogs import readPickledFile
from expsiftUtils import *


parser = argparse.ArgumentParser(description='Plot CPU comparison graph')
parser.add_argument('expt_dirs', nargs='+', help='Experiment directories')
parser.add_argument('plot_filename', help='Filename for the graph')
parser.add_argument('-r', dest='recursive', action='store_true',
                    help='Recursively look for experiment directories under '
                         'each specified directory')


# Returns a boomslang ClusteredBars() object to which the specified Bars have
# been added.
def clusteredBarsGraph(bars, xTickLabels, spacing=0.5):
    clusteredBars = boomslang.ClusteredBars()
    clusteredBars.spacing = spacing
    for bar in bars:
        clusteredBars.add(bar)
    clusteredBars.xTickLabels = xTickLabels
    return clusteredBars


# Returns a boomslang Bar() object with the specified parameters
def barGraph(xValues, yValues, yErrors,
             label='Bar', color='red', errorBarColor='black'):
    bar = boomslang.Bar()
    bar.xValues = xValues
    bar.yValues = yValues
    bar.yErrors = yErrors
    bar.color = color
    bar.errorBarColor = errorBarColor
    bar.label = label
    return bar


def plotCPUDirs(dir2props_dict = {}):
    # We plot multiple subplots - rate is fixed for any subplot
    # We vary the number of classes within a subplot and plot separate bars for
    # each set of unique properties, ie. a separate bargraph for each system
    # config.
    #
    # Hierarchy:
    # - rate_mbps: Separate clusterbar subplot for each
    # - sysconf: Separate bargraph for each (eg. rl=htb, tso=on)
    # - nclasses: Separate xTickLocation for each


    # 1. Turn each directory's set of prop=val strings into a dictionary to
    #     easily look up the value of a particular property for the directory
    dir2prop2val_dict = getDir2Prop2ValDict(dir2props_dict)


    # 2. Find all the common and unique properties among all directories
    common_props, unique_props = getCommonAndUniqueProperties(dir2props_dict)


    # 3. Find all unique values of the 'rate_mbps' property.
    rate2dir_dict = getDirGroupsByProperty(dir2props_dict, ['rate_mbps'],
                                           ignore = False)
    unique_rates = []
    for rate_val_set in rate2dir_dict.iterkeys():
        # The rate_mbps=value string should be the only element in the set
        rate_dict = getPropsDict(rate_val_set)
        rate_mbps = int(rate_dict['rate_mbps'])
        unique_rates.append(rate_mbps)
    unique_rates.sort()


    # 4. Find all unique values of the 'nclasses' property.
    nclasses2dir_dict = getDirGroupsByProperty(dir2props_dict, ['nclasses'],
                                               ignore = False)
    unique_nclasses = []
    for nclasses_val_set in nclasses2dir_dict.iterkeys():
        # The nclasses=value string should be the only element in the set
        nclasses_dict = getPropsDict(nclasses_val_set)
        nclasses = int(nclasses_dict['nclasses'])
        unique_nclasses.append(nclasses)
    unique_nclasses.sort()


    # 5. Find all unique system configurations:
    #    Ignore 'rate_mbps', 'nclasses', and 'run'. The other properties
    #    constitute the system configuration.
    #    Each sysconf is denoted by a frozenset of prop=val strings that are
    #    unique to the sysconf
    sysconf2dir_dict = getDirGroupsByProperty(dir2props_dict,
                                              ['rate_mbps', 'nclasses', 'run'],
                                               ignore = True)
    unique_sysconf = sysconf2dir_dict.keys()


    # 6A. Allocate a separate xValue in the graphs for each 'nclasses' value.
    nclasses2xValue_dict = {}
    for xValue in xrange(len(unique_nclasses)):
        nclasses2xValue_dict[unique_nclasses[xValue]] = xValue


    # 6B. Allocate a color for bar graphs of each sysconf
    colors = ('y', 'g', 'c', 'r', 'm', 'b')
    sysconf2color_dict = {}
    for index, sysconf in enumerate(unique_sysconf):
        sysconf2color_dict[sysconf] = colors[index % len(colors)]


    # 7. Create an individual datapoints list:
    #    for each unique rate,
    #    for each unique sysconf,
    #    for each unique nclasses
    datapoints_dict = {}
    for rate in unique_rates:
        datapoints_dict[rate] = {}
        for sysconf in unique_sysconf:
            datapoints_dict[rate][sysconf] = {}
            for nclasses in unique_nclasses:
                datapoints_dict[rate][sysconf][nclasses] = []


    # 8. Visit each directory and populate the corresponding datapoints list for
    #    that directory
    for directory, prop_vals in dir2props_dict.iteritems():
        # Find the rate, sysconf and nclasses of the directory
        rate = int(dir2prop2val_dict[directory]['rate_mbps'])
        sysconf = removeIgnoredProps(prop_vals,
                                     ['rate_mbps', 'nclasses', 'run'])
        nclasses = int(dir2prop2val_dict[directory]['nclasses'])

        # Read CPU utilization from the pickled file
        mpstat_pfile = os.path.join(directory, 'pickled/mpstat_p.txt')
        (kernel_usage, summary) = readPickledFile(mpstat_pfile)

        # Add the data point (Kernel CPU usage)
        datapoints_dict[rate][sysconf][nclasses].append(kernel_usage)


    # 9. For each (rate, sysconf) combo, create a bar graph
    all_bars_dict = {}
    for rate, rate_dict in datapoints_dict.iteritems():
        all_bars_dict[rate] = {}
        for sysconf, sysconf_dict in rate_dict.iteritems():
            sysconf_label_props = ((sysconf - common_props) |
                                   onlyIncludeProps(sysconf, 'rl'))
            sysconf_label = ', '.join(sorted(sysconf_label_props))
            bar = barGraph([], [], [], color=sysconf2color_dict[sysconf],
                           label=sysconf_label)
            all_bars_dict[rate][sysconf] = bar


    # 10. Compute average and stddev for each (rate, sysconf, nclasses)
    #     combination. This represents the avg and stddev across multiple runs.
    #     Add these to the corresponding bar graphs.
    for rate, rate_dict in datapoints_dict.iteritems():
        for sysconf, sysconf_dict in rate_dict.iteritems():
            bar_values = []
            for nclasses, datapoints in sysconf_dict.iteritems():
                #sysconf_label_props = ((sysconf - common_props) |
                #                        onlyIncludeProps(sysconf, 'rl'))
                #print ('rate %d\t|| %s\t||\tnclasses %d\t|||| %s' % (rate,
                #       ','.join(sorted(sysconf_label_props)),
                #       nclasses, datapoints))
                avg = numpy.average(datapoints)
                stddev = numpy.std(datapoints)

                # Append an (xValue, yValue, yError) tuple
                bar_values.append((nclasses2xValue_dict[nclasses], avg, stddev))

            # Sort the tuples by xValue and assign it to the bar graph.
            # (Boomslang requires the values to be sorted)
            bar = all_bars_dict[rate][sysconf]
            bar_values.sort(key=lambda tup: tup[0])
            # Unzip bar_values into individual lists
            (bar.xValues, bar.yValues, bar.yErrors) = zip(*bar_values)


    # 11. Create a clusteredBars Plot for each rate.
    #     Place all the Plots in a single PlotLayout
    layout = boomslang.PlotLayout()
    for rate in datapoints_dict.iterkeys():
        xLabel = 'Number of classes'
        yLabel = 'Kernel CPU util. (%)'
        title = 'Rate: %s Gbps' % (rate / 1000)

        clusteredBars = clusteredBarsGraph(all_bars_dict[rate].values(),
                                           unique_nclasses)

        plot = boomslang.Plot()

        # Add the clusteredbars for the particular rate
        plot.add(clusteredBars)

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

        # Add the plot to the layout
        layout.addPlot(plot)


    # 12. Return the final PlotLayout with all the graphs
    return layout


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

    # Plot CPU comparison graph
    cpu_plot_layout = plotCPUDirs(dir2props_dict)
    cpu_plot_layout.save(args.plot_filename)


if __name__ == '__main__':
    main(sys.argv)
