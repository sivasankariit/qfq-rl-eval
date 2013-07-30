#!/usr/bin/env python
#
# This script walks through all directories under the base directory recursively
# and whenever an experiment root directory is visited, it plots respective
# graphs for the individual experiments.
# The corresponding data for plotting is also pickled and stored in each
# experiment directory.

import argparse
import imp
import os
import plumbum
import sys
from site_config import *

# Import expsiftUtils from PLOT_SCRIPTS_DIR
sys.path.append(config['PLOT_SCRIPTS_DIR'])
from expsiftUtils import readDirTagFileProperty


parser = argparse.ArgumentParser(description='Plot graphs recursively for '
                                 'expt directories')
parser.add_argument('base_dir',
                    help='Base directory to search for experiments')
parser.add_argument('--force_replot', '-f', dest='force_replot',
                    help='Replot graphs even if they already exist '
                         '(not implemented yet)',
                    action="store_true")


memcached_workloads = ['memcached_set', 'memcached_get',
                       'memcached_set+trafgen_udp',
                       'memcached_get+trafgen_udp']
trafgen_workloads = ['trafgen_tcp', 'trafgen_udp']


def main(argv):
    # Parse flags
    args = parser.parse_args()

    # Check if the base directory is valid
    exists = os.path.exists(args.base_dir)
    isdir = os.path.isdir(args.base_dir)
    if not exists:
        print 'Base directory does not exist'
        sys.exit(1)
    if not isdir:
        print 'Base directory not valid'
        sys.exit(1)
    args.base_dir = os.path.abspath(args.base_dir)

    # Create Plumbum commands for pickling data and plotting
    pickle_cmd = plumbum.local[os.path.join(config['PLOT_SCRIPTS_DIR'],
                                            'pickleExptLogs.py')]
    plot_sniffer_cmd = plumbum.local[os.path.join(config['PLOT_SCRIPTS_DIR'],
                                                  'plotSniffer.py')]
    plot_mcperf_lat_cmd = plumbum.local[os.path.join(config['PLOT_SCRIPTS_DIR'],
                                                     'plotMcperfLatency.py')]

    # Temp directory for plotting graphs
    plot_tmpdir = config['PLOT_TMPDIR']

    print 'Exploring base directory :', args.base_dir

    num_exp_dirs = 0
    for (path, dirs, files) in os.walk(args.base_dir, followlinks=True):
        # Check if an experiment directory was found
        if os.path.exists(os.path.join(path, 'expsift_tags')):
            print 'Found experiment directory:', path
            num_exp_dirs += 1

            # Pickle experiment logs
            print '... Pickling experiment data'
            if args.force_replot:
                pickle_cmd('-f', path, plot_tmpdir)
            else:
                pickle_cmd(path, plot_tmpdir)

            # Read the workload type for the experiment directory
            workload = readDirTagFileProperty(path, 'workload')
            if (not workload in trafgen_workloads and
                not workload in memcached_workloads):
               print 'Workload not recognized for expt: %s' % args.expt_dir
               sys.exit(1)

            # Plot experiment graphs
            print '... Plotting experiment graphs'
            expt_plot_dir = os.path.join(path, 'plot/')
            if not os.path.exists(expt_plot_dir):
                os.makedirs(expt_plot_dir)
            if workload in trafgen_workloads:
                if args.force_replot:
                    plot_sniffer_cmd('-f', path, expt_plot_dir)
                else:
                    plot_sniffer_cmd(path, expt_plot_dir)
            elif workload in memcached_workloads:
                if args.force_replot:
                    plot_mcperf_lat_cmd('-f', path, expt_plot_dir)
                else:
                    plot_mcperf_lat_cmd(path, expt_plot_dir)

    print 'Plotted graphs for %d experiments under %s' % (num_exp_dirs,
            args.base_dir)


if __name__ == '__main__':
    main(sys.argv)
