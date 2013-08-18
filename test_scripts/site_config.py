# Config file with locations of various binaries, hostnames etc
#
# Change the SITE variable to run the experiments on different testbed setup

import argparse
import sys
import types

site_config_parser = argparse.ArgumentParser(description='Site config variables')

site_config_parser.add_argument('--var', dest='var',
                                help='Config variable to read', default='')

#############

SITE = 'Siva-MC'

config = {}

if SITE == 'Vimal':

    config['RL_MODULE_NAME'] = ''
    config['RL_MODULE'] = ''
    config['NETPERF_DIR'] = '/root/vimal/exports/netperf'
    config['SHELL_PROMPT'] = '#'
    config['UDP'] = '/root/vimal/rl-qfq/utils/udp'
    config['TC'] = '/root/vimal/rl-qfq/iproute2/tc/tc'
    config['QFQ_PATH'] = '/root/vimal/rl-qfq/sch_qfq.ko'
    config['CLASS_RATE'] = '/root/vimal/rl-qfq/utils/class-rate.py'

    # Server/client nodes
    config['DEFAULT_HOSTS'] = ['e2', 'e1']

    # Interface details for each node
    config['DEFAULT_DEV'] = { 'e2' : 'eth2', 'e1' : 'eth2' }

    # NIC details
    config['NIC_VENDOR'] = 'Emulex'
    config['NIC_HW_QUEUES'] = 4

    # Taskset CPU for UDP program
    config['UDP_CPU'] = 2
    config['NUM_CPUS'] = 8
    config['EXCLUDE_CPUS'] = []

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
    config['SNIFFER_DELAY'] = 15 # Seconds to delay sniffer initially
    config['SNIFFER_DURATION'] = 10 # Seconds to sniff traffic

    # Experiment script configuration
    config['EXPT_RATES'] = '1000 3000 5000 7000 9000'
    config['EXPT_NCLASSES'] = '1 8 16 512 2048'  # Number of traffic classes
    config['EXPT_RL'] = 'none htb hwrl'
    config['EXPT_RUN'] = '1 2 3'

    # tmp directory for plotting sniffer graphs
    config['PLOT_TMPDIR'] = '/tmp/'

elif SITE == 'Siva':

    config['RL_MODULE_NAME'] = ''
    config['RL_MODULE'] = ''
    config['NETPERF_DIR'] = '/home/ssradhak/src/software/netperf/bin'
    config['SHELL_PROMPT'] = '$'
    config['UDP'] = '/home/ssradhak/src/rate_limiting/qfq-rl-eval/utils/udp'
    config['TC'] = '/home/ssradhak/src/rate_limiting/iproute2/tc/tc'
    config['QFQ_PATH'] = '/home/ssradhak/src/rate_limiting/qfq-rl/sch_qfq.ko'
    config['CLASS_RATE'] = '/home/ssradhak/src/rate_limiting/qfq-rl-eval/utils/class-rate.py'
    config['TRAFGEN'] = '/home/ssradhak/src/rate_limiting/trafgen/trafgen'
    config['PLOT_SCRIPTS_DIR'] = '/home/ssradhak/src/rate_limiting/qfq-rl-eval/plot'

    # Server/client nodes
    config['DEFAULT_HOSTS'] = ['192.168.2.80', '192.168.2.64']

    # Interface details for each node
    config['DEFAULT_DEV'] = { '192.168.2.64' : 'eth1',
                              '192.168.2.80' : 'eth2' }

    # NIC details
    config['NIC_VENDOR'] = 'Intel'
    config['NIC_HW_QUEUES'] = 16

    # Mellanox NIC QOS scripts
    config['TC_WRAP'] = '/home/ssradhak/src/rate_limiting/mellanox/QoS_upstream/tc_wrap.py'
    config['MLNX_QOS'] = '/home/ssradhak/src/rate_limiting/mellanox/QoS_upstream/mlnx_qos'

    # Taskset CPU for single UDP program
    config['UDP_CPU'] = 2
    config['NUM_CPUS'] = 16
    config['EXCLUDE_CPUS'] = []

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
    config['SNIFFER_TMPDIR'] = '/mnt/disks/cciss/c0d0p1/ssradhak/sniffer/'
    config['SNIFFER_CPU'] = 2
    config['SNIFFER_DELAY'] = 25 # Seconds to delay sniffer initially
    config['SNIFFER_DURATION'] = 10 # Seconds to sniff traffic

    # Experiment script configuration
    config['EXPT_RATES'] = '1000 5000 9000'
    config['EXPT_NCLASSES'] = '8 16 32 64 256 512'  # Number of traffic classes
    config['EXPT_RL'] = 'htb hwrl'
    config['EXPT_RUN'] = '1 2 3'

    # tmp directory for plotting sniffer graphs
    #config['PLOT_TMPDIR'] = '/home/ssradhak/tmp/plot/'
    config['PLOT_TMPDIR'] = '/mnt/disks/cciss/c1d1p1/ssradhak/tmp/plot/'

elif SITE == 'Siva-MC':

    config['RL_MODULE_NAME'] = ''
    config['RL_MODULE'] = ''
    config['SHELL_PROMPT'] = '$'
    config['TC'] = '/home/ssradhak/src/rate_limiting/iproute2/tc/tc'
    config['QFQ_PATH'] = '/home/ssradhak/src/rate_limiting/qfq-rl/sch_qfq.ko'
    config['EYEQ_PATH'] = '/home/ssradhak/src/rate_limiting/eyeq++/sch_eyeq.ko'
    config['TRAFGEN'] = '/home/ssradhak/src/rate_limiting/trafgen/trafgen'
    config['PLOT_SCRIPTS_DIR'] = '/home/ssradhak/src/rate_limiting/qfq-rl-eval/plot'

    # Server/client nodes
    config['DEFAULT_MC_SERVERS'] = ['192.168.2.64']
    config['DEFAULT_MC_CLIENTS'] = ['192.168.2.80',
                                    '192.168.2.63',
                                    '192.168.2.65',
                                    '192.168.2.67',
                                    '192.168.2.108',
                                    '192.168.2.109',
                                    '192.168.2.110']

    # Interface details for each node
    config['DEFAULT_DEV'] = { '192.168.2.64'  : 'eth1',
                              '192.168.2.80'  : 'eth2',
                              '192.168.2.63'  : 'eth1',
                              '192.168.2.65'  : 'eth1',
                              '192.168.2.67'  : 'eth1',
                              '192.168.2.108' : 'eth1',
                              '192.168.2.109' : 'eth1',
                              '192.168.2.110' : 'eth1' }

    # NIC details
    config['NIC_VENDOR'] = 'Intel'
    config['NIC_HW_QUEUES'] = 16

    # Mellanox NIC QOS scripts
    config['TC_WRAP'] = '/home/ssradhak/src/rate_limiting/mellanox/QoS_upstream/tc_wrap.py'
    config['MLNX_QOS'] = '/home/ssradhak/src/rate_limiting/mellanox/QoS_upstream/mlnx_qos'

    # CPUs available for tenants
    config['NUM_CPUS'] = 16
    config['EXCLUDE_CPUS'] = [2, 10]

    # Sniffer host with Myri10G sniffer
    config['SNIFFER_HOST'] = ''
    config['SNIFFER'] = '/home/ssradhak/src/rate_limiting/sniffer/tcpdump_tool/snf_simple_tcpdump'
    config['SNIFFER_TMPDIR'] = '/mnt/disks/cciss/c0d0p1/ssradhak/sniffer/'
    config['SNIFFER_CPU'] = 2
    config['SNIFFER_DELAY'] = 25 # Seconds to delay sniffer initially
    config['SNIFFER_DURATION'] = 10 # Seconds to sniff traffic

    # Experiment script configuration
    config['EXPT_RATES'] = '1000 5000 9000'
    config['EXPT_RL'] = 'htb hwrl'
    config['EXPT_RUN'] = '1 2 3'

    # tmp directory for plotting sniffer graphs
    config['PLOT_TMPDIR'] = '/mnt/disks/cciss/c1d1p1/ssradhak/tmp/plot/'

##########################################################################
# Use this as a script that returns value of a variable to be used in bash
# scripts etc.
##########################################################################

def main(argv):
    # Parse flags
    args = site_config_parser.parse_args()
    if args.var == '' or args.var not in config:
        return

    print config[args.var]


if __name__ == '__main__':
    main(sys.argv)
