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
