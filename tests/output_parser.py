import re
from helper import *

re_spaces = re.compile(r'\s+')
IFACE = "eth2"
ZERO = "0.00"

class EthstatsParser:
    def __init__(self, filename):
        self.f = filename
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
            if d["iface"] == IFACE and d["out"] != ZERO:
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
    def __init__(self, filename, max_lines=10000, ignore_first=100, ignore_last=100):
        self.filename = filename
        self.max_lines = max_lines
        self.ignore_first = ignore_first
        self.ignore_last = ignore_last

        self.lines = open(filename).xreadlines()
        # Ignore first line
        self.lines.next()
        self.parse()

    def parse_line(self, line):
        nsec, _, _, packet_len, port = line.strip().split(' ')
        nsec = nsec.split('.')[0]
        return int(nsec), int(packet_len)

    def parse(self):
        line_num = 0
        data = []
        prev_nsec = 0
        for line in self.lines:
            line_num += 1
            d = self.parse_line(line)
            if line_num == 1:
                prev_nsec = d[0]
            else:
                nsec, packet_len = d
                delta = nsec - prev_nsec
                prev_nsec = nsec
                data.append((delta, packet_len))
        self.data = data[self.ignore_first:-self.ignore_last]
        self.ipt = map(lambda e: e[0], self.data)
        self.ipt.sort()

    def get_ipt(self):
        return self.ipt

    def summary(self):
        avg = mean(self.ipt)
        L = len(self.ipt)
        pc99 = self.ipt[int(0.99 * L)]
        return avg, pc99

