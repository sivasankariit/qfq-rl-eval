#!/usr/bin/python
import sys
import argparse
import multiprocessing
import termcolor as T
from expt import Expt
from time import sleep
from host import *
from site_config import *
import os

parser = argparse.ArgumentParser(description="Netperf Test for various rate limiters.")
parser.add_argument('--proto',
                    dest="proto",
                    choices=["tcp","udp"],
                    default="tcp")

parser.add_argument('--nstream',
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
                    default=1)

parser.add_argument('--num-senders', '--ns',
                    type=int,
                    help="Number of sender programs spawned to send flows.",
                    default=config['NUM_CPUS'])

parser.add_argument('--mtu',
                    help="MTU parameter.",
                    default=1500)

parser.add_argument('--pin',
                    dest="pin",
                    help="Pin programs to CPUs in round robin fashion.",
                    action="store_true",
                    default=True)

parser.add_argument('--exptid',
                    dest="exptid",
                    help="Experiment ID",
                    default=None)

parser.add_argument('--rl',
                    dest="rl",
                    help="Which rate limiter to use",
                    choices=["htb", "qfq", 'none', "tbf", "eyeq", "hwrl"],
                    default="")

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
                    nargs="+", default=config['DEFAULT_HOSTS'])

parser.add_argument('--sniffer',
                    dest="sniffer",
                    help="The sniffer machine to capture packet timings",
                    default=config['SNIFFER_HOST'])

parser.add_argument('--rate',
                    dest="rate",
                    type=int,
                    help="total rate limit",
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
elif args.rl == "hwrl":
    if not config["NIC_VENDOR"] == "Intel":
        print "Hardware rate limiting only available on Intel NICs"
        sys.exit(-1)
    print "Using Intel hardware rate limiting"
if (args.rl == "none" or args.rl == "hwrl"):
    if (args.num_class < 2 * args.num_senders):
        args.num_senders = args.num_class / 2
        print "RL = %s and number of classes < 2*number of sender programs." % args.rl
        print "So, I am setting #programs = #classes / 2"
else:
    if args.num_class < args.num_senders:
        args.num_senders = args.num_class
        print "Number of classes is less than number of sender programs."
        print "So, I am setting #programs = #classes"
if args.num_class == 1 and args.rate > 5000:
    print "With Intel NIC, 1 sender program cannot push more than 5Gbps with 1500 byte packets."
    print "Using 2 sender programs and 4 classes instead"
    args.num_senders = 2
    args.num_class = 4

def e(s, tmpdir="/tmp"):
    return "%s/%s/%s" % (tmpdir, args.exptid, s)

class UDP(Expt):
    def start(self):
        # num servers, num clients
        ns = self.opts("ns")
        nc = self.opts("nrr")
        dir = self.opts("exptid")
        server = self.opts("hosts")[0]
        client = self.opts("hosts")[1]
        sniffer = self.opts("sniffer")
        startport = self.opts("startport")

        #self.server = Host(client)
        self.client = Host(client)
        self.sniffer = Host(sniffer)
        self.hlist = HostList()
        #self.hlist.append(self.server)
        self.hlist.append(self.client)

        self.hlist.rmrf(e(""))
        self.hlist.mkdir(e(""))

        if sniffer:
            self.sniffer.rmrf(e("", tmpdir=config['SNIFFER_TMPDIR']))
            self.sniffer.mkdir(e("", tmpdir=config['SNIFFER_TMPDIR']))
            self.sniffer.cmd("killall -9 %s" % config['SNIFFER'])

        self.hlist.rmmod()
        self.hlist.killall("udp")
        self.hlist.remove_qdiscs()
        if config["NIC_VENDOR"] == "Intel":
            self.client.clear_hw_rate_limits(numqueues=config['NIC_HW_QUEUES'])
        #self.hlist.insmod_qfq()

        if self.opts("rl") == "htb":
            self.client.add_htb_qdisc(str(args.rate) + "Mbit", args.htb_mtu)
            rate_str = '%.3fMbit' % (self.opts("rate") * 1.0 / self.opts("num_class"))
            if self.opts("num_class") is not None:
                num_hash_bits = int(math.log(self.opts("num_class"), 2))
                self.client.add_htb_hash(num_hash_bits=num_hash_bits)
                self.client.add_n_htb_class(rate=rate_str, num_class=self.opts("num_class"))
                # Just verify that we have created all classes correctly.
                self.client.htb_class_filter_output(e(''))
        elif self.opts("rl") == "tbf":
            self.client.add_tbf_qdisc(str(args.rate) + "Mbit")
        elif self.opts("rl") == "qfq":
            self.client.add_qfq_qdisc(str(args.rate), args.htb_mtu, nclass=self.opts("num_class"), startport=startport)
        elif self.opts("rl") == "eyeq":
            self.client.insmod(rate=args.rate)
        elif self.opts("rl") == "hwrl":
            num_hw_rl = min(config['NIC_HW_QUEUES'], self.opts("num_senders"))
            hw_rate = self.opts("rate") / num_hw_rl
            for q in xrange(0, num_hw_rl):
                # First queue will account for remainder in rate limit
                delta = 1 if (q < self.opts("rate") % num_hw_rl) else 0
                self.client.add_hw_rate_limit(rate=hw_rate + delta, queue=q)

        self.client.start_cpu_monitor(e(''))
        self.client.start_bw_monitor(e(''))
        if self.opts("rl") == "qfq":
            self.client.start_qfq_monitor(e(''))
        self.client.start_mpstat(e(''))
        self.client.set_mtu(self.opts("mtu"))
        if sniffer:
            self.sniffer.start_sniffer_delayed(e('', tmpdir=config['SNIFFER_TMPDIR']),
                    board=0, delay=config['SNIFFER_DELAY'],
                    duration=config['SNIFFER_DURATION'])
        sleep(1)

        num_senders = self.opts("num_senders")
        num_class = self.opts("num_class")
        # Vimal: Initially I kept this rate = 10000, so the kernel
        # module will do all rate limiting.  But it seems like the
        # function __ip_route_output_key seems to consume a lot of CPU
        # usage at high packet rates, so I thought I better keep the
        # packet rate the same.
        # Siva: We won't be rate limiting in application unless we are measuring
        # user level rate limiting. So it doesn't really matter.
        ## rate = self.opts("rate") / num_senders

        # If we want userspace rate limiting
        if self.opts("user") == True:
            rate = self.opts("rate") / num_senders
        else:
            rate = 0

        self.client.start_n_udp(num_class, num_senders,
                                socket.gethostbyname(server), startport,
                                rate, burst=1472, dir=e(''), pin=self.opts("pin"),
                                totalrate = self.opts("rate"))
        return

    def stop(self):
        self.client.qfq_stats(e(''))
        print 'waiting...'
        sleep(10)
        self.hlist.stop_qfq_monitor()
        self.hlist.killall("iperf netperf netserver ethstats udp")
        if self.opts("sniffer"):
            self.sniffer.stop_sniffer()
            self.sniffer.copy_local(e('', tmpdir=config['SNIFFER_TMPDIR']),
                                    self.opts("exptid") + "-snf",
                                    tmpdir=config['SNIFFER_TMPDIR'])
        self.client.copy_local(e(''), self.opts("exptid"))
        if config["NIC_VENDOR"] == "Intel":
            self.client.clear_hw_rate_limits(numqueues=config['NIC_HW_QUEUES'])
        return

UDP(vars(args)).run()
os.system("killall -9 ssh")
