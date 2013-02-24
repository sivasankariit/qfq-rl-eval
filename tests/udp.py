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

parser.add_argument('--num-class',
                    help="Number of classes of traffic.",
                    type=int,
                    default=None)

parser.add_argument('--mtu',
                    help="MTU parameter.",
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
                    choices=["htb", "qfq", 'none', "tbf"],
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

parser.add_argument('--user',
                    action="store_true",
                    default=False,
                    help="App-level rate limiting")

parser.add_argument('--startport',
                    dest="startport",
                    type=int,
                    default=1000)

args = parser.parse_args()
if args.rl == "none":
    print "Using userspace rate limiting"
    args.user = True

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

        self.hlist.rmrf(e(""))
        self.hlist.mkdir(e(""))

        #self.server = Host(client)
        self.client = Host(client)
        self.hlist = HostList()
        #self.hlist.append(self.server)
        self.hlist.append(self.client)

        self.hlist.rmmod()
        self.hlist.killall("udp")
        self.hlist.remove_qdiscs()
        #self.hlist.insmod_qfq()
        num_senders = self.opts("ns")
        if self.opts("rl") == "htb":
            self.client.add_htb_qdisc(str(args.rate) + "Mbit", args.htb_mtu)
            if self.opts("num_class") is not None:
                num_hash_bits = int(math.log(self.opts("num_class"), 2))
                self.client.add_htb_hash(num_hash_bits=num_hash_bits)
                self.client.add_n_htb_class(num_hash=self.opts("num_class"))
                num_senders = self.opts("num_class")

                # Just verify that we have created all classes correctly.
                self.client.htb_class_filter_output(e(''))
        elif self.opts("rl") == "tbf":
            self.client.add_tbf_qdisc(str(args.rate) + "Mbit")
	elif self.opts("rl") == "qfq":
	    self.client.add_qfq_qdisc(str(args.rate), args.htb_mtu, nclass=args.nrls, startport=startport)

        self.client.start_cpu_monitor(e(''))
        self.client.start_bw_monitor(e(''))
        if self.opts("rl") == "qfq":
            self.client.start_qfq_monitor(e(''))
        self.client.start_mpstat(e(''))
        self.client.set_mtu(self.opts("mtu"))
        sleep(1)
        nprogs = 16
        # Vimal: Initially I kept this rate = 10000, so the kernel
        # module will do all rate limiting.  But it seems like the
        # function __ip_route_output_key seems to consume a lot of CPU
        # usage at high packet rates, so I thought I better keep the
        # packet rate the same.
        rate = self.opts("rate") / nprogs
        # If we want userspace rate limiting
        if self.opts("user") == True:
            rate = self.opts("rate") / nprogs

        self.client.start_n_udp(num_senders, nprogs, "192.168.2.2", startport, rate)
        return

    def stop(self):
        self.client.qfq_stats(e(''))
        print 'waiting...'
        sleep(10)
        self.hlist.stop_qfq_monitor()
        self.hlist.killall("iperf netperf netserver ethstats udp")
        self.client.copy_local(e(''), self.opts("exptid"))
        return

UDP(vars(args)).run()
os.system("killall -9 ssh")
