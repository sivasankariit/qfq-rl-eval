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

parser.add_argument('--nclass',
                    dest="nc",
                    type=int,
                    help="Number of classes.",
                    default=1)

parser.add_argument('--exptid',
                    dest="exptid",
                    help="Experiment ID",
                    default=None)

parser.add_argument('--time', '-t',
                    dest="t",
                    type=int,
                    help="Time to run the experiment",
                    default=10)

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

parser.add_argument('--divisor',
                    type=int,
                    help="rate, rate/divisor, rate/divisor/divisor/, etc...",
                    default=2)

parser.add_argument('--startport',
                    dest="startport",
                    type=int,
                    default=1000)

args = parser.parse_args()

def e(s):
    return "/tmp/%s/%s" % (args.exptid, s)

class Oversub(Expt):
    def start(self):
        # num servers, num clients
        dir = self.opts("exptid")
        client = self.opts("hosts")[1]
        startport = self.opts("startport")

        self.client = Host(client)
        self.hlist = HostList()
        self.hlist.append(self.client)

        self.hlist.rmmod()
        self.hlist.killall()
        self.hlist.remove_qdiscs()
        self.hlist.insmod_qfq()

        self.client.qfq_add_root()
        divisor = self.opts("divisor")
        rate = self.opts("rate")
        for klass in xrange(args.nc):
            self.client.qfq_add_class(rate, startport+klass)
            rate /= divisor

        self.hlist.rmrf(e(""))
        self.hlist.mkdir(e(""))

        self.client.start_cpu_monitor(e(''))
        self.client.start_bw_monitor(e(''))
        self.client.start_qfq_monitor(e(''))
        sleep(1)
        nprogs = 10
        self.client.start_n_udp(args.nc, nprogs, "192.168.2.2", startport)
        return

    def stop(self):
        self.client.qfq_stats(e(''))
        print 'waiting...'
        sleep(10)
        self.hlist.stop_qfq_monitor()
        self.hlist.killall("iperf netperf netserver ethstats udp")
        self.client.copy_local(e(''), self.opts("exptid"))
        return

Oversub(vars(args)).run()
os.system("killall -9 ssh")
