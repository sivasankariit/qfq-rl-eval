import re
from helper import *
from collections import defaultdict


# Class for parsing mpstat output
#
# CPU utilization in following categories is recorded
# user = User level
# sys = System
# sirq = Soft IRQs
#
# Kernel usage is the sum of sys and sirq usage
class MPStatParser:

    def __init__(self, filename):
        self.f = filename
        self.lines = open(filename).readlines()
        self.parse()

    def parse_line(self, line):
        re_spaces = re.compile(r'\s+')
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

    def kernel_usage(self):
        msys = mean(self.usage["sys"])
        msirq = mean(self.usage["sirq"])
        return msys + msirq
