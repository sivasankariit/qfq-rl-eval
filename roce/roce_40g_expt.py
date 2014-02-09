import argparse
import subprocess
import time
import signal
import sys
import os
import re

parser = argparse.ArgumentParser()
parser.add_argument('-n', default=10000, type=int, help="Number of iterations")
parser.add_argument('-p', default=1, type=int, help="Number of processes")
parser.add_argument('-s', default=False, action="store_true", help="Server mode?")
parser.add_argument('-c', default="10.0.0.2", help="client mode connect to server IP")
parser.add_argument('-i', default=1, type=float, help="interval")
parser.add_argument('-q', default=1, type=float, help="number of queue pairs")
parser.add_argument('-T', default=64, type=int, help="size of TX queue")
parser.add_argument('--msize', default=64, type=int, help="message size")
parser.add_argument('--quiet', default=False)

FLAGS = parser.parse_args()

START_PORT = 18000
COUNTER_FILE = '/sys/class/infiniband/mlx4_0/ports/1/counters/port_xmit_data'
U32_MAX = (1 << 32) - 1
OUTPUT = ""
NUM_CPUS = 8
pat_spaces = re.compile(r'\s+')

if FLAGS.quiet:
    OUTPUT = "> /dev/null 2>&1"

def start_servers():
    procs = []
    for i in xrange(FLAGS.p):
        cmd = "taskset -c %d ib_write_bw -x 0 -p %d -n %d -s %d -q %d -t %d %s" % \
            (i % NUM_CPUS, START_PORT + i, FLAGS.n, FLAGS.msize, FLAGS.q, FLAGS.T, OUTPUT)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, bufsize=65536)
        procs.append(proc)
    return procs

def start_clients():
    procs = []
    for i in xrange(FLAGS.p):
        cmd = "taskset -c %d ib_write_bw -x 0 -p %d -n %d -s %d -q %d -t %d %s %s" % \
            (i % NUM_CPUS, START_PORT + i, FLAGS.n, FLAGS.msize, FLAGS.q, FLAGS.T, FLAGS.c, OUTPUT)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, bufsize=65536)
        procs.append(proc)
    return procs

def cleanup():
    os.system("killall -9 ib_write_bw > /dev/null 2>&1")

def sigint_handler(*args):
    cleanup()
    sys.exit(-1)

def read_counter(f):
    f.seek(0)
    return int(f.read())

def main():
    signal.signal(signal.SIGINT, sigint_handler)
    cleanup()
    time.sleep(3)
    procs = []
    if FLAGS.s:
        procs = start_servers()
    else:
        procs = start_clients()

    prev = None
    prev_t = time.time()
    """
    with open(COUNTER_FILE, 'r') as f:
        while True:
            t = time.time()
            dt = t - prev_t
            curr = read_counter(f)
            if prev is None:
                prev = curr

            diff = curr - prev
            if diff < 0:
                diff += U32_MAX # Wrapped around.  It can happen at most once as long as FLAGS.i <= 1s.

            # http://community.mellanox.com/thread/1124
            diff *= 4.0
            print "%.3f %d %.3f" % (t, curr, diff * 8.0 / dt / 1e9)
            time.sleep(FLAGS.i)
            prev = curr
            prev_t = t
    """
    avges = []
    for p in procs:
        p.wait()
        data = p.stdout.read()
        #print data
        try:
            lastline = data.split('\n')[-3]
            data = pat_spaces.split(lastline.strip())
            #print '*******************', data[-1]
            avges.append(float(data[-1]) * 8.0)
        except:
            continue
    print "Averages from each process in Mb/s: ", avges
    print "Total of averages in Gb/s:          ", sum(avges)/1e3
    cleanup()

if __name__ == "__main__":
    main()
