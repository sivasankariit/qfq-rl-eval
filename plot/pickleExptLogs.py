#!/usr/bin/env python

import cPickle
import os
import random
import sys
import tarfile

from SnifferParser import SnifferParser


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


def main(argv):

    if len(argv) != 3:
        print 'Usage: ', argv[0], 'expt_dir tmp_dir'
        sys.exit(-1)

    expt_dir = argv[1]
    tmp_dir = argv[2]

    # Temp directory to extract the sniffer data and pickle it
    snf_data_dir = os.path.join(tmp_dir, 'snf_data')
    if not os.path.exists(snf_data_dir):
        os.makedirs(snf_data_dir)

    # Extract the sniffer data to the temp directory
    snf_tarfile = os.path.join(expt_dir, 'logs/pkt_snf.tar.gz')
    tar = tarfile.open(snf_tarfile)
    tar.extractall(snf_data_dir)
    tar.close()

    # Create directory for pickled files
    pickle_dir = os.path.join(expt_dir, 'pickled')
    if not os.path.exists(pickle_dir):
        os.makedirs(pickle_dir)

    # Create directory for saving statistics
    stats_dir = os.path.join(expt_dir, 'stats')
    if not os.path.exists(stats_dir):
        os.makedirs(stats_dir)

    # Pickle sniffer data
    pickleSnfFile(os.path.join(snf_data_dir, 'pkt_snf.txt'),
                  pickle_dir, stats_dir, max_lines = 1000000)


if __name__ == '__main__':
    main(sys.argv)
