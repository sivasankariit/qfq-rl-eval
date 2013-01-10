
"""
Module to configure QFQ qdisc.  Also configures flows to classes using
hash tables for fast classification.  Only supports one field (ip
dport) as hashkey but you can modify it for ip dst as well.

Arbitrary classification: not now.
"""
import pprint
from collections import defaultdict

class QFQ:
    DEFAULT_RATE = 100
    DEFAULT_CLASSID = 1000

    def __init__(self, iface):
        self.iface = iface
        self.classid = 1
        self.filter = {}
        self.cmds = []

    def add_qdisc(self):
        cmd = "tc qdisc add dev %s root handle 1: qfq" % self.iface
        self.cmds.append(cmd)
        self.add_one_class(self.default_classid(), None, QFQ.DEFAULT_RATE)

    def default_classid(self):
        return QFQ.DEFAULT_CLASSID

    def add_one_class(self, classid, filter, rate):
        cmd = "tc class add dev %s parent 1: classid 1:%d qfq weight %s maxpkt 2048"
        cmd = cmd % (self.iface, classid, rate)
        if filter is not None:
            self.filter[filter] = classid
        self.cmds.append(cmd)
        return

    def add_class(self, filter, rate):
        self.add_one_class(self.classid, filter, rate)
        self.classid += 1

    def add_linear_filters(self, parent="1:", filter_dict={}, hashentry=""):
        for filter, classid in filter_dict.iteritems():
            cmd = "tc filter add dev %s protocol all parent %s prio 1 u32 %s match " % (self.iface, parent, hashentry)
            cmd += "ip dport %s 0xffff flowid 1:%d" % (filter, classid)
            self.cmds.append(cmd)
        return

    def add_default_filter(self, parent="1:", hashentry=""):
        cmd = "tc filter add dev %s parent %s protocol all prio 2 u32 %s match u32 0 0 at 0 flowid 1:%s"
        cmd = cmd % (self.iface, parent, hashentry, self.default_classid())
        self.cmds.append(cmd)

    def add_hash_filters(self, buckets=256, hashfn=None):
        if hashfn is None:
            hashfn = lambda x: x % buckets
        CHAINID = "2:"
        # First create the filter root
        cmd = "tc filter add dev %s parent 1: prio 1 protocol all u32" % self.iface
        self.cmds.append(cmd)

        cmd = "tc filter add dev %s parent 1: prio 1 handle %s protocol all u32 divisor %s" % (self.iface, CHAINID, buckets)
        self.cmds.append(cmd)

        # Add rules to the created table using a hash of the filter
        filter_chains = defaultdict(list)
        for filter, classid in self.filter.iteritems():
            filter = int(filter)
            hsh = hashfn(filter)
            filter_chains[hsh].append(filter)

        for hsh in filter_chains.keys():
            lineardict = {}
            for filter in filter_chains[hsh]:
                lineardict[filter] = self.filter[filter]
            hentry = hex(hsh).replace("0x", '')
            hashentry = "ht 2:%s:" % hentry
            self.add_linear_filters(parent="1:", filter_dict=lineardict, hashentry=hashentry)

        # Add the root filter
        cmd = "tc filter add dev %s protocol all parent 1: prio 1 u32 ht 800:: " % self.iface
        cmd += " match ip protocol 6 0xff "
        cmd += " hashkey mask 000000ff at %s " % (20) # IP header 20 bytes, dest port +2 bytes from TCP header
        cmd += " link %s " % (CHAINID)

        self.cmds.append(cmd)
        return

if __name__ == "__main__":
    q = QFQ("eth2")
    q.add_qdisc()
    for i in xrange(2):
        q.add_class(5001+i, rate=1000)
    #q.add_linear_filters()
    q.add_hash_filters()
    q.add_default_filter()

    print '\n'.join(q.cmds)
