import re
from helper import *
from collections import defaultdict


IFACE = "eth1"
ZERO = "0.00"


# Class for parsing ethstats output
#
# Gives the mean and stdev of network utilization
class EthstatsParser:

    def __init__(self, filename, iface=IFACE):
        self.f = filename
        self.iface = iface
        self.lines = open(filename).readlines()
        self.parse()

    def parse_line(self, line):
        re_spaces = re.compile(r'\s+')
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
        # NOTE: Ignore first few seconds of output
        util = util[15:]
        self.util = util
        return util

    def summary(self):
        return dict(mean=mean(self.util), stdev=stdev(self.util))
