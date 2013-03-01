import sys, os
sys.path.insert(0, os.path.abspath('../tests'))
from site_config import *

dev = sys.argv[1]
mask = 1
count = 0

"""
CPU numbering on lancelots:

(0 4)  (Core 0, two hyperthreads)
(1 5)
(2 6)
(3 7)

So, we set TX interrupt on CPU 0
RX-0 on CPU 1
RX-1 on CPU 2
RX-2 on CPU 3
RX-3 on CPU 5
RX-4 on CPU 6
"""

mappings = config['INTR_MAPPING']

for line in open('/proc/interrupts').xreadlines():
    if dev not in line:
        continue
    nr = line.split(':')[0]
    nr = nr.strip()

    name = line.split(' ')[-1].strip()
    if count == len(mappings):
        count = 0
        print 'Wrapped around interrupt mappings'
    mask = 1 << mappings[count]
    cmd = 'echo %x > /proc/irq/%s/smp_affinity' % (mask, nr)
    print name, cmd
    os.system(cmd)
    count += 1
