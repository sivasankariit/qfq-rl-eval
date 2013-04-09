#!/usr/bin/env python

import argparse
import cPickle
import os
import random
import sys
import tarfile
from plumbum.cmd import head

from SnifferParser import SnifferParser
from MPStatParser import MPStatParser
from EthstatsParser import EthstatsParser


parser = argparse.ArgumentParser(description='Pickle experiment logs')
parser.add_argument('expt_dir', help='Experiment directory')
parser.add_argument('tmp_dir', help='Temp directory')
parser.add_argument('-f', dest='force_rewrite',
                    help='Repickle even if pickle file already exists',
                    action="store_true")


pickled_files = {'sniffer' : ['burstlen_pkt.txt',
                              'burstlen_nsec.txt',
                              'pkt_len_freq.txt'],
                 'mpstat' : ['mpstat_p.txt'],
                 'ethstats' : ['net_p.txt']}
stats_files = {'sniffer' : ['snf_stats.txt',
                            'pkt_snf_head20000.txt'],
               'mpstat' : ['cpu_util.txt'],
               'ethstats' : ['net_util.txt']}


# Used to load data from a picked file to variables
def readPickledFile(infile):
    fd = open(infile, 'rb')
    data = cPickle.load(fd)
    fd.close()
    return data


def pickleSnfFile(snf_file, pickle_dir, stats_dir, max_lines=100000):

    # Parse the sniffer log file
    sniff = SnifferParser(snf_file, max_lines=max_lines)

    # Pickle burstlen_pkt data
    burstlen_pkt_pfile = os.path.join(pickle_dir, 'burstlen_pkt.txt')
    burstlen_pkt = sniff.get_burstlen_pkt()
    summary_burstlen_pkt = sniff.summary_burstlen_pkt()
    data = (burstlen_pkt, summary_burstlen_pkt)
    fd = open(burstlen_pkt_pfile, 'wb')
    cPickle.dump(data, fd)
    fd.close()

    # Pickle burstlen_nsec data
    burstlen_nsec_pfile = os.path.join(pickle_dir, 'burstlen_nsec.txt')
    burstlen_nsec = sniff.get_burstlen_nsec()
    summary_burstlen_nsec = sniff.summary_burstlen_nsec()
    data = (burstlen_nsec, summary_burstlen_nsec)
    fd = open(burstlen_nsec_pfile, 'wb')
    cPickle.dump(data, fd)
    fd.close()

    # Pickle inter-packet arrival time data
    ipt_pfile = os.path.join(pickle_dir, 'ipt.txt')
    ipt = sniff.get_ipt()
    summary_ipt = sniff.summary_ipt()
    data = (ipt, summary_ipt)
    fd = open(ipt_pfile, 'wb')
    cPickle.dump(data, fd)
    fd.close()

    # Pickle packet length data
    pkt_len_freq_pfile = os.path.join(pickle_dir, 'pkt_len_freq.txt')
    pkt_len_freq = sniff.get_pkt_len_freq()
    most_freq_pkt_len = sniff.get_most_freq_pkt_length()
    data = (most_freq_pkt_len, pkt_len_freq)
    fd = open(pkt_len_freq_pfile, 'wb')
    cPickle.dump(data, fd)
    fd.close()

    # Write stats about the sniffer data
    snf_stats_file = os.path.join(stats_dir, 'snf_stats.txt')
    snf_stats_fd = open(snf_stats_file, 'w')
    snf_stats_fd.write('Seen packet lengths: %s\n' %
                       str(sorted(sniff.get_seen_packet_lengths())))
    snf_stats_fd.write('Most frequent packet length: %d\n' % most_freq_pkt_len)
    snf_stats_fd.write('--- Inter-packet times (port_number, avg, pc99)---\n')
    snf_stats_fd.write('%s\n' % str(summary_ipt))
    snf_stats_fd.write('--- Burst length in packets (port_number, avg, pc99)---\n')
    snf_stats_fd.write('%s\n' % str(summary_burstlen_pkt))
    snf_stats_fd.write('--- Burst length in nanosecs (port_number, avg, pc99)---\n')
    snf_stats_fd.write('%s\n' % str(summary_burstlen_nsec))
    snf_stats_fd.close()

    # Save first 20000 lines of sniffer file
    snf_head_file = os.path.join(stats_dir, 'pkt_snf_head20000.txt')
    (head['-n', '20000', snf_file] > snf_head_file)()


def pickleMPStat(mpstat_file, pickle_dir, stats_dir):

    # Parse the mpstat log file
    mstats = MPStatParser(mpstat_file)

    # Pickle CPU utilization data
    mpstat_pfile = os.path.join(pickle_dir, 'mpstat_p.txt')
    kernel_usage = mstats.kernel_usage()
    summary = mstats.summary()
    data = (kernel_usage, summary)
    fd = open(mpstat_pfile, 'wb')
    cPickle.dump(data, fd)
    fd.close()

    # Write stats about CPU utilization
    cpu_stats_file = os.path.join(stats_dir, 'cpu_util.txt')
    cpu_stats_fd = open(cpu_stats_file, 'w')
    cpu_stats_fd.write('Kernel usage (average) = %s\n' % str(kernel_usage))
    cpu_stats_fd.write('--- Average usage breakdown ---\n')
    cpu_stats_fd.write(str(summary))
    cpu_stats_fd.close()


def pickleEthstats(ethstats_file, pickle_dir, stats_dir):

    # Parse the mpstat log file
    estats = EthstatsParser(ethstats_file)

    # Pickle CPU utilization data
    ethstats_pfile = os.path.join(pickle_dir, 'net_p.txt')
    summary = estats.summary()
    fd = open(ethstats_pfile, 'wb')
    cPickle.dump(summary, fd)
    fd.close()

    # Write stats about network utilization
    net_stats_file = os.path.join(stats_dir, 'net_util.txt')
    net_stats_fd = open(net_stats_file, 'w')
    net_stats_fd.write(str(summary))
    net_stats_fd.close()


def allFilesGenerated(category, pickle_dir, stats_dir):
    res = True
    for filename in pickled_files[category]:
        filename = os.path.join(pickle_dir, filename)
        if not os.path.exists(filename):
            res = False
    for filename in stats_files[category]:
        filename = os.path.join(stats_dir, filename)
        if not os.path.exists(filename):
            res = False
    return res


def main(argv):
    # Parse flags
    args = parser.parse_args()

    # Temp directory to extract the sniffer data and pickle it
    snf_data_dir = os.path.join(args.tmp_dir, 'snf_data')
    if not os.path.exists(snf_data_dir):
        os.makedirs(snf_data_dir)

    # Extract the sniffer data to the temp directory
    snf_tarfile = os.path.join(args.expt_dir, 'logs/pkt_snf.tar.gz')
    tar = tarfile.open(snf_tarfile)
    tar.extractall(snf_data_dir)
    tar.close()

    # Create directory for pickled files
    pickle_dir = os.path.join(args.expt_dir, 'pickled')
    if not os.path.exists(pickle_dir):
        os.makedirs(pickle_dir)

    # Create directory for saving statistics
    stats_dir = os.path.join(args.expt_dir, 'stats')
    if not os.path.exists(stats_dir):
        os.makedirs(stats_dir)

    # Pickle sniffer data if required
    if (args.force_rewrite or
        not allFilesGenerated('sniffer', pickle_dir, stats_dir)):
        pickleSnfFile(os.path.join(snf_data_dir, 'pkt_snf.txt'),
                      pickle_dir, stats_dir, max_lines = 1000000)

    # Pickle mpstat data
    if (args.force_rewrite or
        not allFilesGenerated('mpstat', pickle_dir, stats_dir)):
        pickleMPStat(os.path.join(args.expt_dir, 'logs/mpstat.txt'),
                     pickle_dir, stats_dir)

    # Pickle ethstats data
    if (args.force_rewrite or
        not allFilesGenerated('ethstats', pickle_dir, stats_dir)):
        pickleEthstats(os.path.join(args.expt_dir, 'logs/net.txt'),
                       pickle_dir, stats_dir)


if __name__ == '__main__':
    main(sys.argv)
