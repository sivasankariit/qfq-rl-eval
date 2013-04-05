from helper import *
from collections import defaultdict


# Class for parsing output from the myri10g sniffer
#
# Sniffer output format:
# timestamp_ns src_mac dst_mac pkt_len src_port
#
# src_mac and dst_mac indicate last byte of the mac addresses.
# pkt_len is in bytes
# src_port is the TCP or UDP port
#
# Each src_port corresponds to one traffic class. Properties are parsed and
# stored individually for each traffic class
#
# ipt = Interpacket times in nanoseconds for each TC
# burstlen_pkt = Contiguous burst length in packets for each TC
# burstlen_ns  = Contiguous burst length in ns for each TC
class SnifferParser:

    def __init__(self, filename, max_lines=100000, ignore_frac=0.1):
        self.filename = filename
        self.max_lines = max_lines
        self.ignore_frac = ignore_frac
        self.pkt_len_freq = {}
        self.ipt = defaultdict(list)
        self.burstlen_pkt = defaultdict(list)
        self.burstlen_nsec = defaultdict(list)

        # NOTE: Will throw exception if the file is not present.
        self.lines = open(filename).xreadlines()
        # Ignore first line
        self.lines.next()
        # Parse the file and populate dataset
        self.parse()

    def get_ipt(self):
        return self.ipt

    def get_burstlen_pkt(self):
        return self.burstlen_pkt

    def get_burstlen_nsec(self):
        return self.burstlen_nsec

    def get_seen_packet_lengths(self):
        return self.pkt_len_freq.keys()

    def get_pkt_len_freq(self):
        return self.pkt_len_freq

    def get_most_freq_pkt_length(self):
        max_freq = max(self.pkt_len_freq.values())
        pkt_lens = [ l for (l, freq) in self.pkt_len_freq.iteritems()
                       if freq == max_freq ]
        return pkt_lens[0]

    def parse_line(self, line):
        nsec, _, _, packet_len, port = line.strip().split(' ')
        nsec = nsec.split('.')[0]
        return int(nsec), int(packet_len), int(port)

    def parse(self):
        line_num = 0
        data = defaultdict(list)
        prev_nsec = defaultdict(int)
        prev_port = 0
        curr_burstlen_pkt = 0
        burst_starttime = 0
        for line in self.lines:
            line_num += 1
            if line_num > self.max_lines:
                break
            d = self.parse_line(line)
            pkt_len = d[1]
            port = d[2]
            # Record inter-packet times for each class
            if prev_nsec[port] == 0:
                prev_nsec[port] = d[0]
            else:
                nsec, packet_len, port = d
                delta = nsec - prev_nsec[port]
                prev_nsec[port] = nsec
                data[port].append((delta, packet_len))
            # Record burst lengths of each class
            if prev_port == 0:
                prev_port = port
                curr_burstlen_pkt = 1
                burst_starttime = d[0]
            elif prev_port == port:
                curr_burstlen_pkt += 1
            else:
                self.burstlen_pkt[prev_port].append(curr_burstlen_pkt)
                self.burstlen_nsec[prev_port].append(d[0] - burst_starttime)
                prev_port = port
                curr_burstlen_pkt = 1
                burst_starttime = d[0]
            if pkt_len not in self.pkt_len_freq:
                self.pkt_len_freq[pkt_len] = 1
            else:
                self.pkt_len_freq[pkt_len] += 1
        self.data = defaultdict(list)
        self.ipt = defaultdict(list)
        for port in data.keys():
            self.data[port] = data[port]
            if self.ignore_frac > 0:
                L = int(self.data[port].__len__() * self.ignore_frac)
                self.data[port] = self.data[port][L:-L]
                L = int(self.burstlen_pkt[port].__len__() * self.ignore_frac)
                self.burstlen_pkt[port] = self.burstlen_pkt[port][L:-L]
            self.ipt[port] = map(lambda e: e[0], self.data[port])
            self.ipt[port].sort()
            self.burstlen_pkt[port].sort()
            self.burstlen_nsec[port].sort()

    def summary_ipt(self):
        ret = dict()
        for port in self.ipt.keys():
            if port == 0:
                continue
            avg = mean(self.ipt[port])
            L = len(self.ipt[port])
            pc99 = self.ipt[port][int(0.99 * L)]
            ret[port] = (avg, pc99)
        return ret

    def summary_burstlen_pkt(self):
        ret = dict()
        for port in self.burstlen_pkt.keys():
            if port == 0:
                continue
            avg = mean(self.burstlen_pkt[port])
            L = len(self.burstlen_pkt[port])
            pc99 = self.burstlen_pkt[port][int(0.99 * L)]
            ret[port] = (avg, pc99)
        return ret

    def summary_burstlen_nsec(self):
        ret = dict()
        for port in self.burstlen_nsec.keys():
            if port == 0:
                continue
            avg = mean(self.burstlen_nsec[port])
            L = len(self.burstlen_nsec[port])
            pc99 = self.burstlen_nsec[port][int(0.99 * L)]
            ret[port] = (avg, pc99)
        return ret

    def mean_ipt(self):
        """Returns average of the average ipt per class."""
        means = []
        for port in self.ipt.keys():
            avg = mean(self.ipt[port])
            means.append(avg)
        return mean(means)

    def stdev_ipt(self, wrt=None):
        """Returns avg of the stdev of ipt per class with respect to
        mean @wrt."""
        stdevs = []
        for port in self.ipt.keys():
            std = stdev(self.ipt[port], wrt)
            stdevs.append(std)
        return mean(stdevs)

    # NOTE: Will fail if no TCs are found - the input file was empty or
    # non-existent.
    def ideal_ipt_nsec(self, total_rate_gbps):
        FRAMING_OVERHEAD = 24
        class_rate_gbps = total_rate_gbps / len(self.ipt.keys())
        return (self.seen_packet_len[0] + FRAMING_OVERHEAD) * 8.0 / (class_rate_gbps)
