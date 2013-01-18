#!/usr/bin/python
import sys
import argparse
import multiprocessing
import termcolor as T
from expt import Expt
from time import sleep
from host import *

parser = argparse.ArgumentParser(description="Netperf Test for various rate limiters.")
parser.add_argument('--proto',
                    dest="proto",
                    choices=["tcp","udp"],
                    default="tcp")

parser.add_argument('--nstream',
                    dest="ns",
                    type=int,
                    help="Number of TCP_STREAM flows.",
                    default=4)

parser.add_argument('--ssize',
                    dest="ssize",
                    type=int,
                    help="Size for stream flows.",
                    default=4)

parser.add_argument('--nrr',
                    dest="nrr",
                    type=int,
                    help="Number of TCP_RR flows.",
                    default=512)

parser.add_argument('--rrsize',
                    dest="rrsize",
                    type=int,
                    help="Req and resp size for RR.",
                    default=1)

parser.add_argument('--htb-mtu',
                    dest="htb_mtu",
                    help="HTB MTU parameter.",
                    default=1500)

parser.add_argument('--pin',
                    dest="pin",
                    help="Pin netperf to CPUs in round robin fashion.",
                    action="store_true",
                    default=False)

parser.add_argument('--exptid',
                    dest="exptid",
                    help="Experiment ID",
                    default=None)

parser.add_argument('--rl',
                    dest="rl",
                    help="Which rate limiter to use",
                    choices=["htb", "qfq", 'none'],
                    default="")

parser.add_argument('--time', '-t',
                    dest="t",
                    type=int,
                    help="Time to run the experiment",
                    default=10)

parser.add_argument('--nrls',
                    dest="nrls",
                    type=int,
                    help="number of rate limiters (newrl)",
                    default=1)

parser.add_argument('--dryrun',
                    dest="dryrun",
                    help="Don't execute experiment commands.",
                    action="store_true",
                    default=False)

parser.add_argument('--hosts',
                    dest="hosts",
                    help="The two hosts (server/client) to run tests",
                    nargs="+",
                    default=["e2","e1"])

args = parser.parse_args()

def e(s):
    return "/tmp/%s/%s" % (args.exptid, s)

class Netperf(Expt):
    def start(self):
        # num servers, num clients
        ns = self.opts("ns")
        nc = self.opts("nrr")
        dir = self.opts("exptid")
        server = self.opts("hosts")[0]
        client = self.opts("hosts")[1]

        self.server = Host(server)
        self.client = Host(client)
        self.hlist = HostList()
        self.hlist.append(self.server)
        self.hlist.append(self.client)

        self.hlist.rmmod()
        self.hlist.killall()
        self.hlist.remove_qdiscs()
        if self.opts("rl") == "htb":
            self.client.add_htb_qdisc("5Gbit", args.htb_mtu)
	elif self.opts("rl") == "qfq":
	    self.client.add_qfq_qdisc("5000", args.htb_mtu)

        self.hlist.rmrf(e(""))
        self.hlist.mkdir(e(""))

        self.server.start_netserver()
        self.client.start_cpu_monitor(e(''))
        T = self.opts("t") - 10

        sleep(1)
        # Start the connections
        if self.opts("nrr"):
            opts = "-t %s_RR" % self.opts("proto").upper()
            opts += " -v 2 -H %s -l %s -c -C" % (self.server.hostname(), T)
            opts += " -- -r %s,%s " % (self.opts("rrsize"), self.opts("rrsize"))
            self.client.start_n_netperfs(self.opts("nrr"), opts, e(''), "rr", args.pin)

        if self.opts("ns"):
            opts = "-t %s_STREAM" % (self.opts("proto").upper())
            opts += " -v 2 -H %s -l %s -c -C" % (self.server.hostname(), T)
            opts += " -- -s %s " % self.opts("ssize")
            if self.opts("proto") == "tcp":
                opts += " -D " # disable nagle's
            self.client.start_n_netperfs(self.opts("ns"), opts, e(''), "stream", args.pin)
        return

    def stop(self):
        print 'waiting...'
        sleep(10)
        self.hlist.killall("iperf netperf netserver")
        self.client.copy_local(e(''), self.opts("exptid"))
        return

Netperf(vars(args)).run()
