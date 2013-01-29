#!/usr/bin/python
import sys
import argparse
import multiprocessing
import termcolor as T
from expt import Expt
from time import sleep
from host import *
import os

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

parser.add_argument('--rate',
                    dest="rate",
                    type=int,
                    help="rate per rate limiter",
                    default=1000)

parser.add_argument('--startport',
                    dest="startport",
                    type=int,
                    default=1000)

args = parser.parse_args()

def e(s):
    return "/tmp/%s/%s" % (args.exptid, s)

class UDP(Expt):
    def start(self):
        # num servers, num clients
        ns = self.opts("ns")
        nc = self.opts("nrr")
        dir = self.opts("exptid")
        #server = self.opts("hosts")[0]
        client = self.opts("hosts")[1]
        startport = self.opts("startport")

        #self.server = Host(client)
        self.client = Host(client)
        self.hlist = HostList()
        #self.hlist.append(self.server)
        self.hlist.append(self.client)

        self.hlist.rmmod()
        self.hlist.killall()
        self.hlist.remove_qdiscs()
        self.hlist.insmod_qfq()
        if self.opts("rl") == "htb":
            self.client.add_htb_qdisc("5Gbit", args.htb_mtu)
	elif self.opts("rl") == "qfq":
	    self.client.add_qfq_qdisc(str(args.rate), args.htb_mtu, nclass=args.nrls, startport=startport)

        self.hlist.rmrf(e(""))
        self.hlist.mkdir(e(""))

        self.client.start_cpu_monitor(e(''))
        self.client.start_bw_monitor(e(''))
        sleep(1)
        nprogs = self.opts("ns")
        if self.opts("ns") == 1:
            nprogs = 4
        self.client.start_n_udp(self.opts("ns"), nprogs, "192.168.2.2", startport)
        return

    def stop(self):
        self.client.qfq_stats(e(''))
        print 'waiting...'
        sleep(2)
        self.hlist.killall("iperf netperf netserver ethstats udp")
        self.client.copy_local(e(''), self.opts("exptid"))
        return

UDP(vars(args)).run()
os.system("killall -9 ssh")
