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
    config['DEFAULT_HOSTS'] = ["192.168.2.80", "192.168.2.66"]
