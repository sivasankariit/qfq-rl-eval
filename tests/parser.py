
class ESParser:
    def __init__(self, filename):
        self.f = filename
        self.lines = open(filename).readlines()
        self.parse()

    def parse_line(self, line):
        iface, rest = line.split(":")
        iface = iface.strip()
        data = rspaces.split(rest.strip())
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
