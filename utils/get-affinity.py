import sys, os

dev = sys.argv[1]
mask = 1
count = 0

for line in open('/proc/interrupts').xreadlines():
    if dev not in line:
        continue
    nr = line.split(':')[0]
    nr = nr.strip()

    name = line.split(' ')[-1].strip()
    fname = '/proc/irq/%s/smp_affinity' % (nr)
    print nr, open(fname).read(),

