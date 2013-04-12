#!/usr/bin/env python

import argparse
import numpy
import os
import sys

from pickleExptLogs import readPickledFile
from expsiftUtils import *
from plotCompare import plotComparisonDirs
from plotCompare import getRateMbpsFromPropValSet
from plotCompare import getNClassesFromPropValSet
from plotCompare import sortRateValSets
from plotCompare import sortNClassesValSets
from plotCompare import getSysConfLabel


parser = argparse.ArgumentParser(description='Plot burst_len comparison graphs')
parser.add_argument('expt_dirs', nargs='+', help='Experiment directories')
parser.add_argument('plotfile_prefix', help='Filename prefix for output graphs')
parser.add_argument('-r', dest='recursive', action='store_true',
                    help='Recursively look for experiment directories under '
                         'each specified directory')


def getAvgBurstLenPkt(directory):
    # Read the sniffer pickle file and return the average burst length in
    # packets
    burstlen_pkt_summary_pfile = os.path.join(
            directory, 'pickled/burstlen_pkt_summary.txt')
    summary = readPickledFile(burstlen_pkt_summary_pfile)
    avg_burstlen = numpy.average(map(lambda port: summary[port][0],
                                     summary.keys()))
    return avg_burstlen


def getAvgBurstLenUsec(directory):
    # Read the sniffer pickle file and return the average burst length in
    # usecs (convert from nsecs)
    burstlen_nsec_summary_pfile = os.path.join(
            directory, 'pickled/burstlen_nsec_summary.txt')
    summary = readPickledFile(burstlen_nsec_summary_pfile)
    avg_burstlen = (numpy.average(map(lambda port: summary[port][0],
                                      summary.keys())) / 1000.0)
    return avg_burstlen


def getPc99BurstLenUsec(directory):
    # Read the sniffer pickle file and return the average of pc99 burst length
    # in usecs (convert from nsecs)
    burstlen_nsec_summary_pfile = os.path.join(
            directory, 'pickled/burstlen_nsec_summary.txt')
    summary = readPickledFile(burstlen_nsec_summary_pfile)
    avg_pc99_burstlen = (numpy.average(map(lambda port: summary[port][1],
                                           summary.keys())) / 1000.0)
    return avg_pc99_burstlen


# Returns the burstlen comparison summary graph
def plotBurstLenComparisonDirs(dir2props_dict, fn_get_datapoint,
                               yLabel, layout=None):
    return plotComparisonDirs(
            dir2props_dict,

            subplot_props = ['rate_mbps'],
            cluster_props = ['nclasses'],
            trial_props = ['run'],

            fn_sort_subplots = sortRateValSets,
            fn_sort_clusters = sortNClassesValSets,
            fn_sort_majorgroups = lambda majorgroups: majorgroups,

            fn_get_subplot_title = (lambda rate_val_set:
                'Rate: %s Gbps' %
                (getRateMbpsFromPropValSet(rate_val_set) / 1000)),

            fn_get_cluster_label = (lambda nclasses_val_set:
                str(getNClassesFromPropValSet(nclasses_val_set))),

            fn_get_majorgroup_label = getSysConfLabel,

            fn_get_datapoint = fn_get_datapoint,

            xLabel = 'Number of classes',
            yLabel = yLabel,
            layout = layout)


# Returns the "avg burstlen in pkts" comparison summary graph
def plotAvgBurstLenPktComparisonDirs(dir2props_dict = {}, layout = None):
    return plotBurstLenComparisonDirs(
            dir2props_dict,
            fn_get_datapoint = getAvgBurstLenPkt,
            yLabel = 'Avg. burst length (packets)',
            layout = layout)


# Returns the "avg burstlen in usecs" comparison summary graph
def plotAvgBurstLenUsecComparisonDirs(dir2props_dict = {}, layout = None):
    return plotBurstLenComparisonDirs(
            dir2props_dict,
            fn_get_datapoint = getAvgBurstLenUsec,
            yLabel = 'Avg. burst length (usecs)',
            layout = layout)


# Returns the "avg of pc99 burstlen in usecs" comparison summary graph
def plotPc99BurstLenUsecComparisonDirs(dir2props_dict = {}, layout = None):
    return plotBurstLenComparisonDirs(
            dir2props_dict,
            fn_get_datapoint = getPc99BurstLenUsec,
            yLabel = '99th perc. burst length (usecs)',
            layout = layout)


# Returns the "burstlen in usecs" comparison summary graph
def plotBurstLenUsecComparisonDirs(dir2props_dict = {}, layout = None):
    # Plot burstlen_usec avg comparison graph
    _, _, _, _, layout = plotAvgBurstLenUsecComparisonDirs(dir2props_dict)

    # Plot burstlen_usec pc99 comparison graph in the same layout
    return plotPc99BurstLenUsecComparisonDirs(dir2props_dict, layout)


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

    # Plot burstlen_pkt comparison graph
    _, _, _, _, burstlen_pkt_plot_layout = (
            plotAvgBurstLenPktComparisonDirs(dir2props_dict))
    burstlen_pkt_plot_layout.save(args.plotfile_prefix +
                                  'compare_burstlen_pkt.png')

    # Plot burstlen_usec comparison graph
    _, _, _, _, burstlen_usec_plot_layout = (
            plotBurstLenUsecComparisonDirs(dir2props_dict))
    burstlen_usec_plot_layout.save(args.plotfile_prefix +
                                   'compare_burstlen_usec.png')


if __name__ == '__main__':
    main(sys.argv)
