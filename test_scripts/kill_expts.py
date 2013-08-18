#!/usr/bin/python
import sys
import argparse
import termcolor as T
from time import sleep
from host import *
from site_config import *
import os

parser = argparse.ArgumentParser(description="Kill rate limiting expts")

parser.add_argument('--servers',
                    dest="servers",
                    metavar='SERVER',
                    help="Memcached servers to run tests",
                    nargs="+", default=config['DEFAULT_MC_SERVERS'])

parser.add_argument('--clients',
                    dest="clients",
                    metavar='CLIENT',
                    help="Memcached clients to run tests",
                    nargs="+", default=config['DEFAULT_MC_CLIENTS'])

args = parser.parse_args()


hlist = HostList()

print T.colored("Servers:---", "green")
for ip in args.servers:
    h = Host(ip)
    hlist.append(h)
    print T.colored(ip, "green")

print T.colored("Clients:---", "yellow")
for ip in args.clients:
    h = Host(ip)
    hlist.append(h)
    print T.colored(ip, "yellow")

hlist.remove_qdiscs()
hlist.stop_mpstat()
hlist.killall("memcached mcperf")
hlist.stop_trafgen()
hlist.rmmod_qfq()
hlist.rmmod_eyeq()
hlist.clear_intel_hw_rate_limits(config['NIC_HW_QUEUES'])
hlist.clear_mellanox_hw_rate_limits()
