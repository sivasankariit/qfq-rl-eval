import re
from helper import *
from collections import defaultdict

re_spaces = re.compile(r'\s+')
IFACE = "eth2"
ZERO = "0.00"

class EthstatsParser:
    def __init__(self, filename, iface=IFACE):
        self.f = filename
        self.iface = iface
        self.lines = open(filename).readlines()
        self.parse()

    def parse_line(self, line):
        iface, rest = line.split(":")
        iface = iface.strip()
        data = re_spaces.split(rest.strip())
        return {"iface": iface, "in":data[0], "out":data[3]}

    def parse(self):
        ret = dict()
        util = []
        for line in self.lines:
            d = self.parse_line(line)
            if d["iface"] == self.iface and d["out"] != ZERO:
                util.append(float(d["out"]))
        L = len(util)
        L = L/3
        util = util[L/10:-L/10]
        self.util = util
        return util

    def summary(self):
        return dict(mean=mean(self.util), stdev=stdev(self.util))


class MPStatParser:
    def __init__(self, filename):
        self.f = filename
        self.lines = open(filename).readlines()
        self.parse()

    def parse_line(self, line):
        if "all" not in line:
            return None
        data = re_spaces.split(line)
        user = data[3]
        sys = data[5]
        sirq = data[8]

        user, sys, sirq = map(float, [user, sys, sirq])
        return user, sys, sirq

    def parse(self):
        ret = dict(user=[], sys=[], sirq=[])
        keys = "user sys sirq".split(' ')
        for line in self.lines:
            data = self.parse_line(line)
            if data is None:
                continue
            for i,k in enumerate(keys):
                ret[k].append(data[i])
        self.usage = ret
        return ret

    def summary(self):
        muser = mean(self.usage["user"])
        msys = mean(self.usage["sys"])
        msirq = mean(self.usage["sirq"])
        return "user: %.2f, sys: %.2f, sirq: %.2f" % (muser, msys, msirq)

    def kernel(self):
        msys = mean(self.usage["sys"])
        msirq = mean(self.usage["sirq"])
        return msys + msirq


class SnifferParser:
    def __init__(self, filename, max_lines=10000, ignore_frac=0.1):
        self.filename = filename
        self.max_lines = max_lines
        self.ignore_frac = ignore_frac
        self.seen_packet_len = []
        self.ipt = defaultdict(list)

        try:
            self.lines = open(filename).xreadlines()
            # Ignore first line
            self.lines.next()
            self.parse()
        except IOError:
            # File is probably not present
            return

    def parse_line(self, line):
        nsec, _, _, packet_len, port = line.strip().split(' ')
        nsec = nsec.split('.')[0]
        return int(nsec), int(packet_len), int(port)

    def parse(self):
        line_num = 0
        data = defaultdict(list)
        prev_nsec = defaultdict(int)
        for line in self.lines:
            line_num += 1
            if line_num > self.max_lines:
                break
            d = self.parse_line(line)
            len = d[1]
            port = d[2]
            if prev_nsec[port] == 0:
                prev_nsec[port] = d[0]
            else:
                nsec, packet_len, port = d
                delta = nsec - prev_nsec[port]
                prev_nsec[port] = nsec
                # data.append((delta, packet_len))
                data[port].append((delta, packet_len))
            if len not in self.seen_packet_len:
                self.seen_packet_len.append(len)
        self.data = defaultdict(list)
        self.ipt = defaultdict(list)
        for port in data.keys():
            self.data[port] = data[port]
            if self.ignore_frac > 0:
                L = int(self.data[port].__len__() * self.ignore_frac)
                self.data[port] = self.data[port][L:-L]
            self.ipt[port] = map(lambda e: e[0], self.data[port])
            self.ipt[port].sort()

    def get_ipt(self):
        return self.ipt

    def summary(self):
        ret = dict()
        for port in self.ipt.keys():
            avg = mean(self.ipt[port])
            L = len(self.ipt[port])
            pc99 = self.ipt[port][int(0.99 * L)]
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

    def ideal_ipt_nsec(self, total_rate_gbps):
        FRAMING_OVERHEAD = 24
        try:
            class_rate_gbps = total_rate_gbps / len(self.ipt.keys())
            return (self.seen_packet_len[0] + FRAMING_OVERHEAD) * 8.0 / (class_rate_gbps)
        except:
            # Probably the file was not present.  Ignore any errors silently.
            return 0

