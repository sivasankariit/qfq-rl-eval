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
from plotCompare import plotLineComparisonDirs


parser = argparse.ArgumentParser(description='Plot trafgen throughput comparisons')
parser.add_argument('expt_dirs', nargs='+', help='Experiment directories')
parser.add_argument('plot_filename', help='Filename for the graph')
parser.add_argument('-r', dest='recursive', action='store_true',
                    help='Recursively look for experiment directories under '
                         'each specified directory')


FOR_PAPER = True
THROUGHPUT_LIMITS = (0, 5) if FOR_PAPER else (0, 5000)
RL_ORDER = { 'htb' : 1, 'eyeq' : 2, 'qfq' : 3, 'none' : 4 }
RL_LABEL = { 'htb' : 'htb', 'eyeq' : 'eyeq', 'qfq' : 'nicpic', 'none' : 'none' }


def sortLineValSets(line_val_sets):
    line_val_sets.sort(key = lambda line_val_set:
                       RL_ORDER[getUniqueProp(line_val_set)]),


def serverLoadFromMcrate(mcrate_val_set, mctenants = 1, numclients = 1):
    return int(getUniqueProp(mcrate_val_set)) * mctenants * numclients


def getServerAvgTxRate(directory):
    # Read the trafgen pickle file and return the average trafgen Tx rate on
    # server machines
    trafgen_pfile = os.path.join(directory, 'pickled/trafgen_p.txt')
    (host_tx_goodput, host_rx_goodput) = readPickledFile(trafgen_pfile)

    # Find the list of servers used for the experiment
    servers, clients = getServersAndClients(directory)

    rates = [ int(host_tx_goodput.get(server, 0) * 1514.0 / 1472.0)
              for server in servers ]

    return numpy.mean(rates)


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


# Returns trafgen throughput comparison graph. The graph plots one line for the
# each kind of rl.
def plotTrafgenThroughputComparisonDirs(dir2props_dict):

    units = 'Gb/s' if FOR_PAPER else 'Mb/s'
    div = 1000.0 if FOR_PAPER else 1

    fn_get_datapoint = lambda directory: getServerAvgTxRate(directory) / div
    yLabel = 'UDP throughput (%s)' % units
    title = '' if FOR_PAPER else 'Average UDP throughput'

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
            yLimits = THROUGHPUT_LIMITS,
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

    # Plot trafgen throughput comparison graph
    trafgenrate_plot = plotTrafgenThroughputComparisonDirs(dir2props_dict)
    trafgenrate_plot.save(args.plot_filename)


if __name__ == '__main__':
    main(sys.argv)
