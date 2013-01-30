
import argparse
import time
import subprocess
from collections import defaultdict
import sys

parser = argparse.ArgumentParser("Print tc-class rates in real time.")
parser.add_argument('-i', '--iface', '--dev',
                    required=True)
parser.add_argument('-n', '--num-sec',
                    type=float,
                    default=1.0,
                    help="Number of seconds between successive reads.")

args = parser.parse_args()

def tc():
    cmd = "tc -s class show dev %s" % args.iface
    out = subprocess.check_output(cmd.split(' '))
    return out

def parse(out):
    lines = iter(out.split('\n'))
    ret = defaultdict(int)
    for line in lines:
        if line.startswith('class qfq'):
            klass = line.split(' ')[2]
            data = lines.next().strip()
            sent = data.split(' ')[1]
            ret[klass] = int(sent)
    return ret

def rates(old, new, dt):
    rate = defaultdict()
    for k, v in new.iteritems():
        rate[k] = (v - old[k]) * 1.0 / dt
    return rate

def main():
    prev = parse(tc())
    tprev = time.time()
    time.sleep(args.num_sec)
    while True:
        curr = parse(tc())
        tcurr = time.time()
        R = rates(prev, curr, (tcurr - tprev))
        prev = curr
        for k in sorted(R.keys()):
            print "%s: %.3f" % (k, R[k] * 8.0 / 1e6)
        tprev = time.time()
        time.sleep(args.num_sec)
    return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)

