import re
from helper import *


# Class for parsing trafgen output
#
# Goodput is recorded (Tx or Rx)
class TrafgenParser:

    def __init__(self, filename):
        self.f = filename
        self.lines = open(filename).readlines()
        self.parse()

    def parse_line(self, line):
        re_spaces = re.compile(r'\s+')
        if ("Tx" not in line and "Rx" not in line):
            return None
        data = re_spaces.split(line)
        return float(data[2])

    def parse(self):
        rate_mbps = []
        for line in self.lines:
            data = self.parse_line(line)
            if data is not None:
                rate_mbps.append(data)
        # Ignore first and last few seconds of data
        rate_mbps = rate_mbps[30:-30]
        self.rate_mbps = rate_mbps
        return rate_mbps

    def get_avg_rate(self):
        return mean(self.rate_mbps)
