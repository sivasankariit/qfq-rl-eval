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
        pat_reqsize = re.compile(r'Request size \[B\]: avg ([0-9\.]+) min')
        pat_rspsize = re.compile(r'Response size \[B\]: avg ([0-9\.]+) min')
        pat_reqrsp = re.compile(r'Total: connections ([0-9\.]+) requests ([0-9\.]+) responses ([0-9\.]+) test-duration')
        self.reqr = 0       # request rate
        self.rspr = 0       # response rate
        self.reqsize = 0    # average request size
        self.rspsize = 0    # average response size
        self.reqs = 0       # number of requests
        self.rsps = 0       # number of responses
        for l in self.lines:
            # reqr
            m = pat_reqr.search(l)
            if m:
                self.reqr = float(m.group(1))
            # rspr
            m = pat_rspr.search(l)
            if m:
                self.rspr = float(m.group(1))
            # reqsize
            m = pat_reqsize.search(l)
            if m:
                self.reqsize = float(m.group(1))
            # rspsize
            m = pat_rspsize.search(l)
            if m:
                self.rspsize = float(m.group(1))
            # reqs, rsps
            m = pat_reqrsp.search(l)
            if m:
                self.reqs = int(m.group(2))
                self.rsps = int(m.group(3))

        return (self.reqr, self.rspr,
                self.reqsize, self.rspsize,
                self.reqs, self.rsps)


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


    def get_reqsize(self):
        return self.reqsize


    def get_rspsize(self):
        return self.rspsize


    def get_reqs(self):
        return self.reqs


    def get_rsps(self):
        return self.rsps
