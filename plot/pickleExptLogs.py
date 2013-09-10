#!/usr/bin/env python

import argparse
import bisect
import cPickle
import glob
import numpy
import os
import random
import sys
import tarfile
from plumbum.cmd import head

from SnifferParser import SnifferParser
from MPStatParser import MPStatParser
from EthstatsParser import EthstatsParser
from McperfParser import McperfParser

from McperfParser import parseHostsFile
from expsiftUtils import readDirTagFileProperty


parser = argparse.ArgumentParser(description='Pickle experiment logs')
parser.add_argument('expt_dir', help='Experiment directory')
parser.add_argument('tmp_dir', help='Temp directory')
parser.add_argument('-f', dest='force_rewrite',
                    help='Repickle even if pickle file already exists',
                    action="store_true")


pickled_files = {'sniffer' : ['burstlen_pkt.txt',
                              'burstlen_pkt_summary.txt',
                              'burstlen_nsec.txt',
                              'burstlen_nsec_summary.txt',
                              'ipt.txt',
                              'ipt_summary.txt',
                              'pkt_len_freq.txt'],
                 'mpstat' : ['mpstat_p.txt'],
                 'ethstats' : ['net_p.txt'],
                 'mpstat_mc' : ['mpstat_mc_p.txt'],
                 'mcperf' : ['mcperf_p.txt',
                             'hosts_p.txt']}
stats_files = {'sniffer' : ['snf_stats.txt',
                            'pkt_snf_head20000.txt'],
               'mpstat' : ['cpu_util.txt'],
               'ethstats' : ['net_util.txt'],
               'mpstat_mc' : ['cpu_util.txt'],
               'mcperf' : ['mcperf.txt']}

memcached_workloads = ['memcached_set', 'memcached_get',
                       'memcached_set+trafgen_udp',
                       'memcached_get+trafgen_udp']
trafgen_workloads = ['trafgen_tcp', 'trafgen_udp']

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
    # Pickle the actual data and summary separately
    burstlen_pkt_pfile = os.path.join(pickle_dir, 'burstlen_pkt.txt')
    burstlen_pkt_summary_pfile = os.path.join(pickle_dir,
                                              'burstlen_pkt_summary.txt')
    burstlen_pkt = sniff.get_burstlen_pkt()
    summary_burstlen_pkt = sniff.summary_burstlen_pkt()
    fd = open(burstlen_pkt_pfile, 'wb')
    cPickle.dump(burstlen_pkt, fd)
    fd.close()
    fd = open(burstlen_pkt_summary_pfile, 'wb')
    cPickle.dump(summary_burstlen_pkt, fd)
    fd.close()

    # Pickle burstlen_nsec data
    # Pickle the actual data and summary separately
    burstlen_nsec_pfile = os.path.join(pickle_dir, 'burstlen_nsec.txt')
    burstlen_nsec_summary_pfile = os.path.join(pickle_dir,
                                               'burstlen_nsec_summary.txt')
    burstlen_nsec = sniff.get_burstlen_nsec()
    summary_burstlen_nsec = sniff.summary_burstlen_nsec()
    fd = open(burstlen_nsec_pfile, 'wb')
    cPickle.dump(burstlen_nsec, fd)
    fd.close()
    fd = open(burstlen_nsec_summary_pfile, 'wb')
    cPickle.dump(summary_burstlen_nsec, fd)
    fd.close()

    # Pickle inter-packet arrival time data
    ipt_pfile = os.path.join(pickle_dir, 'ipt.txt')
    ipt_summary_pfile = os.path.join(pickle_dir, 'ipt_summary.txt')
    ipt = sniff.get_ipt()
    summary_ipt = sniff.summary_ipt()
    fd = open(ipt_pfile, 'wb')
    cPickle.dump(ipt, fd)
    fd.close()
    fd = open(ipt_summary_pfile, 'wb')
    cPickle.dump(summary_ipt, fd)
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


def pickleMcperf(mcperf_files, pickle_dir, stats_dir):

    mc_hists = []
    reqrs = []
    rsprs = []
    reqsizes = []
    rspsizes = []
    reqss = []
    rspss = []
    # Parse the mcperf log files
    for mcperf_file in mcperf_files:
        mcstats = McperfParser(mcperf_file)
        mc_hists.append(mcstats.get_hist())
        reqrs.append(mcstats.get_reqr())
        rsprs.append(mcstats.get_rspr())
        reqsizes.append(mcstats.get_reqsize())
        rspsizes.append(mcstats.get_rspsize())
        reqss.append(mcstats.get_reqs())
        rspss.append(mcstats.get_rsps())

    # Compute combined histogram
    agg_hist = dict()
    for hist in mc_hists:
        agg_hist.update({k:v+hist[k] for k,v in agg_hist.iteritems() if k in hist})
        agg_hist.update({k:v for k,v in hist.iteritems() if k not in agg_hist})

    # Compute total request and response rates
    agg_reqr = sum(reqrs)
    agg_rspr = sum(rsprs)

    # Compute total requests and responses
    agg_reqs = sum(reqss)
    agg_rsps = sum(rspss)

    # Compute average request and response sizes
    avg_reqsize = numpy.average(reqsizes, weights = reqss)
    avg_rspsize = numpy.average(rspsizes, weights = reqss)
    #avg_reqsize = (sum(map(lambda size, num : size * num, reqsizes, reqss)) / agg_reqs)
    #avg_rspsize = (sum(map(lambda size, num : size * num, rspsizes, rspss)) / agg_rsps)

    # Pickle mcperf histogram data
    mcperf_pfile = os.path.join(pickle_dir, 'mcperf_p.txt')
    fd = open(mcperf_pfile, 'wb')
    cPickle.dump(agg_hist, fd)
    fd.close()

    # Compute CDF and find avg, median, pc99, pc999 latencies
    sorted_hist = sorted(agg_hist.items())
    w_sum = sum(map(lambda (k,v): float(k)*float(v), sorted_hist))
    cum_sum = numpy.cumsum(map(lambda (k,v): v, sorted_hist))
    num_samples = cum_sum[-1]
    lat_avg = w_sum / num_samples
    lat_median = sorted_hist[bisect.bisect(cum_sum, num_samples * 50 / 100)][0]
    lat_pc99 = sorted_hist[bisect.bisect(cum_sum, num_samples * 99 / 100)][0]
    lat_pc999 = sorted_hist[bisect.bisect(cum_sum, int(num_samples * 99.9/100))][0]

    # Pickle mcperf latency summary
    mcperf_summary = { 'agg_reqr'   : agg_reqr,
                       'agg_rspr'   : agg_rspr,
                       'avg_reqsize': avg_reqsize,
                       'avg_rspsize': avg_rspsize,
                       'agg_reqs'   : agg_reqs,
                       'agg_rsps'   : agg_rsps,
                       'lat_avg'    : lat_avg,
                       'lat_median' : lat_median,
                       'lat_pc99'   : lat_pc99,
                       'lat_pc999'  : lat_pc999 }
    mcperf_summary_pfile = os.path.join(pickle_dir, 'mcperf_summary_p.txt')
    fd = open(mcperf_summary_pfile, 'wb')
    cPickle.dump(mcperf_summary, fd)
    fd.close()

    # Write stats about memcached latencies
    mcperf_stats_file = os.path.join(stats_dir, 'mcperf.txt')
    mcperf_stats_fd = open(mcperf_stats_file, 'w')
    mcperf_stats_fd.write('Aggregate request rate = %s req/s\n' % str(agg_reqr))
    mcperf_stats_fd.write('Aggregate response rate = %s rsp/s\n' % str(agg_rspr))
    mcperf_stats_fd.write('Total requests = %s\n' % str(agg_reqs))
    mcperf_stats_fd.write('Total responses = %s\n' % str(agg_rsps))
    mcperf_stats_fd.write('Average request size = %0.1f B\n' % avg_reqsize)
    mcperf_stats_fd.write('Average response size = %0.1f B\n' % avg_rspsize)
    mcperf_stats_fd.write('Latency stats (usec):\n')
    mcperf_stats_fd.write('  Average = %0.1f\n' % lat_avg)
    mcperf_stats_fd.write('  Median  = %s\n' % str(lat_median))
    mcperf_stats_fd.write('  pc99    = %s\n' % str(lat_pc99))
    mcperf_stats_fd.write('  pc999   = %s\n' % str(lat_pc999))
    mcperf_stats_fd.close()


def pickleMPStatMC(client_mpstat_files, server_mpstat_files,
                   pickle_dir, stats_dir):

    client_usage = []
    server_usage = []
    # Parse the mpstat log files
    for mpstat_file in client_mpstat_files:
        mstats = MPStatParser(mpstat_file)
        client_usage.append(mstats.get_avg_usage())
    for mpstat_file in server_mpstat_files:
        mstats = MPStatParser(mpstat_file)
        server_usage.append(mstats.get_avg_usage())

    # Compute average utilizations
    cli_muser = numpy.mean(map(lambda (muser, msys, msirq): muser, client_usage))
    cli_msys = numpy.mean(map(lambda (muser, msys, msirq): msys, client_usage))
    cli_msirq = numpy.mean(map(lambda (muser, msys, msirq): msirq, client_usage))
    srv_muser = numpy.mean(map(lambda (muser, msys, msirq): muser, server_usage))
    srv_msys = numpy.mean(map(lambda (muser, msys, msirq): msys, server_usage))
    srv_msirq = numpy.mean(map(lambda (muser, msys, msirq): msirq, server_usage))
    cli_summary = "user: %.2f, sys: %.2f, sirq: %.2f" % (
            cli_muser, cli_msys, cli_msirq)
    srv_summary = "user: %.2f, sys: %.2f, sirq: %.2f" % (
            srv_muser, srv_msys, srv_msirq)

    # Pickle CPU utilization data
    mpstat_pfile = os.path.join(pickle_dir, 'mpstat_mc_p.txt')
    cli_kernel_usage = cli_msys + cli_msirq
    srv_kernel_usage = srv_msys + srv_msirq
    summary = mstats.summary()
    data = (cli_kernel_usage, cli_summary, srv_kernel_usage, srv_summary)
    fd = open(mpstat_pfile, 'wb')
    cPickle.dump(data, fd)
    fd.close()

    # Write stats about CPU utilization
    cpu_stats_file = os.path.join(stats_dir, 'cpu_util.txt')
    cpu_stats_fd = open(cpu_stats_file, 'w')
    cpu_stats_fd.write('Client kernel usage (average) = %s\n' % str(cli_kernel_usage))
    cpu_stats_fd.write('--- Average usage breakdown ---\n')
    cpu_stats_fd.write(str(cli_summary))
    cpu_stats_fd.write('\nServer kernel usage (average) = %s\n' % str(srv_kernel_usage))
    cpu_stats_fd.write('--- Average usage breakdown ---\n')
    cpu_stats_fd.write(str(srv_summary))
    cpu_stats_fd.close()


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

    # Read the workload type for the experiment directory
    workload = readDirTagFileProperty(args.expt_dir, 'workload')
    if (not workload in trafgen_workloads and
        not workload in memcached_workloads):
       print 'Workload not recognized for expt: %s' % args.expt_dir
       sys.exit(1)

    # Create directory for pickled files
    pickle_dir = os.path.join(args.expt_dir, 'pickled')
    if not os.path.exists(pickle_dir):
        os.makedirs(pickle_dir)

    # Create directory for saving statistics
    stats_dir = os.path.join(args.expt_dir, 'stats')
    if not os.path.exists(stats_dir):
        os.makedirs(stats_dir)

    # Pickle data for trafgen workloads
    if workload in trafgen_workloads:

        # Temp directory to extract the sniffer data and pickle it
        snf_data_dir = os.path.join(args.tmp_dir, 'snf_data')
        if not os.path.exists(snf_data_dir):
            os.makedirs(snf_data_dir)

        # Extract the sniffer data to the temp directory
        snf_tarfile = os.path.join(args.expt_dir, 'logs/pkt_snf.tar.gz')
        tar = tarfile.open(snf_tarfile)
        tar.extractall(snf_data_dir)
        tar.close()

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

    # Pickle data for memcached workloads
    elif workload in memcached_workloads:

        # Read the list of server and client machines used for the experiment
        (servers, clients) = parseHostsFile(os.path.join(args.expt_dir,
                                                         'logs/hostsfile.txt'))

        # Pickle mcperf data
        if (args.force_rewrite or
            not allFilesGenerated('mcperf', pickle_dir, stats_dir)):

            # Pickle hosts info separately
            hosts_pfile = os.path.join(pickle_dir, 'hosts_p.txt')
            fd = open(hosts_pfile, 'wb')
            cPickle.dump((servers, clients), fd)
            fd.close()

            mcperf_files = []
            for client in clients:
                files = glob.glob(os.path.join(args.expt_dir, 'logs',
                                    client, 'mcperf-t*-c*-*.txt'))
                mcperf_files.extend(files)

            pickleMcperf(mcperf_files, pickle_dir, stats_dir)

        # Pickle mpstat data for clients and servers
        if (args.force_rewrite or
            not allFilesGenerated('mpstat_mc', pickle_dir, stats_dir)):
            client_mpstat_files = [ os.path.join(args.expt_dir, 'logs',
                                                 client, 'mpstat.txt')
                                    for client in clients ]
            server_mpstat_files = [ os.path.join(args.expt_dir, 'logs',
                                                 server, 'mpstat.txt')
                                    for server in servers ]

            pickleMPStatMC(client_mpstat_files, server_mpstat_files,
                           pickle_dir, stats_dir)


if __name__ == '__main__':
    main(sys.argv)
