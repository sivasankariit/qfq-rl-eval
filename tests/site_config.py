# Config file with locations of various binaries, hostnames etc
#
# Change the SITE variable to run the experiments on different testbed setup

SITE = 'Siva'

config = {}

if SITE == 'Vimal':

    config['RL_MODULE_NAME'] = ''
    config['RL_MODULE'] = ''
    config['DEFAULT_DEV'] = 'eth2'
    config['NETPERF_DIR'] = '/root/vimal/exports/netperf'
    config['SHELL_PROMPT'] = '#'
    config['UDP'] = '/root/vimal/rl-qfq/utils/udp'
    config['TC'] = '/root/vimal/rl-qfq/iproute2/tc/tc'
    config['QFQ_PATH'] = '/root/vimal/rl-qfq/sch_qfq.ko'
    config['CLASS_RATE'] = '/root/vimal/rl-qfq/utils/class-rate.py'

    # Server/client nodes
    config['DEFAULT_HOSTS'] = ["e2", "e1"]

    # NIC details
    config['NIC_VENDOR'] = 'Emulex'
    config['NIC_HW_QUEUES'] = 4

    # Taskset CPU for UDP program
    config['UDP_CPU'] = 2

    '''
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
    '''
    config['INTR_MAPPING'] = [0, 1, 3, 5, 6]

    # Sniffer host with Myri10G sniffer
    config['SNIFFER_HOST'] = ''
    config['SNIFFER'] = ''
    config['SNIFFER_TMPDIR'] = ''
    config['SNIFFER_CPU'] = 2

elif SITE == 'Siva':

    config['RL_MODULE_NAME'] = ''
    config['RL_MODULE'] = ''
    config['DEFAULT_DEV'] = 'eth1'
    config['NETPERF_DIR'] = '/home/ssradhak/src/software/netperf/bin'
    config['SHELL_PROMPT'] = '$'
    config['UDP'] = '/home/ssradhak/src/rate_limiting/qfq-rl-eval/utils/udp'
    config['TC'] = '/home/ssradhak/src/rate_limiting/iproute2/tc/tc'
    config['QFQ_PATH'] = '/home/ssradhak/src/rate_limiting/qfq-rl/sch_qfq.ko'
    config['CLASS_RATE'] = '/home/ssradhak/src/rate_limiting/qfq-rl-eval/utils/class-rate.py'

    # Server/client nodes
    config['DEFAULT_HOSTS'] = ['192.168.2.80', '192.168.2.81']

    # NIC details
    config['NIC_VENDOR'] = 'Intel'
    config['NIC_HW_QUEUES'] = 16

    # Taskset CPU for single UDP program
    config['UDP_CPU'] = 2

    '''
    CPU numbering on SEED testbed (dcswitch81):

    (0  8)  (Socket 0, Core 0, two hyperthreads)
    (4 12)  (Socket 0, Core 1, two hyperthreads)
    (2 10)  (Socket 0, Core 2, two hyperthreads)
    (6 14)  (Socket 0, Core 3, two hyperthreads)

    (1  9)  (Socket 1, Core 0, two hyperthreads)
    (5 13)  (Socket 1, Core 1, two hyperthreads)
    (3 11)  (Socket 1, Core 2, two hyperthreads)
    (7 15)  (Socket 1, Core 3, two hyperthreads)
    '''
    config['INTR_MAPPING'] = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]

    # Sniffer host with Myri10G sniffer
    config['SNIFFER_HOST'] = ''
    config['SNIFFER'] = '/home/ssradhak/src/rate_limiting/sniffer/tcpdump_tool/snf_simple_tcpdump'
    config['SNIFFER_TMPDIR'] = '/home/ssradhak/tmp'
    config['SNIFFER_CPU'] = 2
