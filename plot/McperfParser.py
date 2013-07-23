import re
from helper import *


def parseHostsFile(filename):
    lines = open(filename).readlines()
    category = 0    # 0=none/1=servers/2=clients
    servers = []
    clients = []
    for line in lines:
        # Ignore Comment lines
        if line[0] == '#':
            continue
        line = line.strip()
        if category == 0 and 'Servers:' in line:
            category = 1
        elif category == 1:
            if 'Clients:' in line:
                category = 2
            else:
                servers.append(line)
        elif category == 2:
            clients.append(line)
    return (servers, clients)


# Class for parsing ethstats output
#
# Gives the mean and stdev of network utilization
class McperfParser:

    def __init__(self, filename):
        self.f = filename
        self.lines = open(filename).readlines()
        self.parse_ops_mcperf()
        self.parse_latency_mcperf()


    def parse_ops_mcperf(self):
        pat_reqr = re.compile(r'Request rate: ([0-9\.]+) req/s')
        pat_rspr = re.compile(r'Response rate: ([0-9\.]+) rsp/s')
        self.reqr = 0
        self.rspr = 0
        for l in self.lines:
            # req
            m = pat_reqr.search(l)
            if m:
                self.reqr = float(m.group(1))
            # resp
            m = pat_rspr.search(l)
            if m:
                self.rspr = float(m.group(1))
        return (self.reqr, self.rspr)


    def parse_latency_mcperf(self):
        pat_mcperf = re.compile(r'([\d\.]+) (\d+)')
        hist = dict()
        skip = 0

        for l in self.lines:
            if skip == 0 and "Response time histogram [ms]" in l:
                skip = 1
                continue

            # Parse
            l = l.strip()
            if l == ":":
                continue
            if "Response time [ms]: p25" in l:
                break

            m = pat_mcperf.search(l)
            if m:
                lo, num = m.group(1), m.group(2)
                lo = float(lo)
                hist[int(lo * 1e3)] = int(num)
        self.hist = hist
        return hist


    def get_hist(self):
        return self.hist


    def get_reqr(self):
        return self.reqr


    def get_rspr(self):
        return self.rspr
