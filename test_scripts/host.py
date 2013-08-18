
import paramiko
from subprocess import Popen
import termcolor as T
import os
import socket
from time import sleep
from site_config import *
import pexpect
import math


class HostList(object):
    def __init__(self, *lst):
        self.lst = list(lst)

    def append(self, host):
        self.lst.append(host)

    def __getattribute__(self, name, *args):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            ret = lambda *args: map(lambda h: h.__getattribute__(name)(*args), self.lst)
            return ret

    def __iter__(self):
        return self.lst

def local_cmd(c):
    print T.colored(c, "green")
    p = Popen(c, shell=True)
    p.wait()

def controladdr(addr):
    # TODO: this is a simple mapping scheme from the 10GbE
    # interface hostname to the control interface hostname.
    # e10 -> l10.  We may want a general mapping here.
    return 'dcswitch' + addr.split('.')[3]

class ShellWrapper:
    def __init__(self, chan):
        self.chan = chan

    def cmd_async(self, cmd):
        self.chan.send("(%s;) &\n" % cmd)

    def cmd(self, c):
        self.chan.send(c)
        self.chan.recv_ready()
        return self.chan.recv(10**6)

class SSHWrapper:
    def __init__(self, ssh):
        self.ssh = ssh

    def cmd_async(self, cmd):
        cmd = " (%s;) &" % cmd
        self.ssh.sendline(cmd)
        self.ssh.expect(config['PEXPECT_PROMPT'])

    def cmd(self, c):
        c = " %s" % c
        self.ssh.sendline(c)
        self.ssh.expect(config['PEXPECT_PROMPT'])

class Host(object):
    _ssh_cache = {}
    _shell_cache = {}
    def __init__(self, addr):
        self.addr = addr
        self.sshaddr = controladdr(addr)
        # List of processes spawned async on this host
        self.procs = []
        self.delay = False
        self.delayed_cmds = []
        self.dryrun = False

    def set_dryrun(self, state=True):
        self.dryrun = state

    def get(self):
        global config
        ssh = Host._ssh_cache.get(self.sshaddr, None)
        if ssh is None:
            ssh = pexpect.spawn("ssh %s" % self.sshaddr, timeout=120)
            ssh.expect(config['SHELL_PROMPT'])
            config['PEXPECT_PROMPT'] = '\[PEXPECT\]\$ '
            ssh.sendline('PS1="[PEXPECT]\$ "')
            ssh.expect(config['PEXPECT_PROMPT'])
            Host._ssh_cache[self.sshaddr] = ssh
        return ssh

    def get_shell(self):
        shell = Host._shell_cache.get(self.addr, None)
        if shell is None:
            client = self.get()
            shell = SSHWrapper(client)
            Host._shell_cache[self.addr] = shell
        return shell

    def cmd(self, c, dryrun=False):
        self.log(c)
        if not self.delay:
            if dryrun or self.dryrun:
                return (self.addr, c)
            ssh = self.get()
            self.get_shell().cmd(c)
            return (self.addr, c)
        else:
            self.delayed_cmds.append(c)
        return (self.addr, c)

    def delayed_cmds_execute(self):
        if len(self.delayed_cmds) == 0:
            return None
        self.delay = False
        ssh = self.get()
        cmds = ';'.join(self.delayed_cmds)
        out = ssh.exec_command(cmds)[1].read()
        self.delayed_cmds = []
        return out

    def cmd_async(self, c, dryrun=False):
        self.log(c)
        if not self.delay:
            if dryrun or self.dryrun:
                return (self.addr, c)
            #ssh = self.get()
            #out = ssh.exec_command(c)
            sh = self.get_shell()
            sh.cmd_async(c)
        else:
            self.delayed_cmds.append(c)
        return (self.addr, c)

    def delayed_async_cmds_execute(self):
        if len(self.delayed_cmds) == 0:
            return None
        self.delay = False
        ssh = self.get()
        cmds = ';'.join(self.delayed_cmds)
        out = ssh.exec_command(cmds)[1]
        self.delayed_cmds = []
        return out

    def log(self, c):
        addr = T.colored(self.sshaddr, "magenta")
        c = T.colored(c, "grey", attrs=["bold"])
        print "%s: %s" % (addr, c)

    def get_10g_dev(self):
        return config['DEFAULT_DEV'][self.addr]

    def mkdir(self, dir):
        self.cmd("mkdir -p %s" % dir)

    def rmrf(self, dir):
        print T.colored("removing %s" % dir, "red", attrs=["bold"])
        if dir == "/tmp" or dir == "~" or dir == "/":
            # useless
            return
        self.cmd("rm -rf %s" % dir)

    def rmmod(self, mod=config['RL_MODULE_NAME']):
        self.cmd("rmmod %s" % mod)

    def insmod(self, mod=config['RL_MODULE'], rmmod=True, rate=5000, nrls=1):
        dev = self.get_10g_dev()
        params="dev=%s ntestrls=%s rate=%s" % (dev, nrls, rate)
        cmd = "insmod %s %s" % (mod, params)
        if rmmod:
            cmd = "rmmod %s; " % mod + cmd
        self.cmd(cmd)

    def disable_ipv6(self):
        dev = self.get_10g_dev()
        self.cmd("sudo sysctl -w net.ipv6.conf.%s.disable_ipv6=1;" % dev)

    def rmmod_qfq(self):
        self.cmd("sudo rmmod sch_qfq")

    def insmod_qfq(self):
        self.cmd("sudo rmmod sch_qfq; sudo insmod %s" % config['QFQ_PATH'])
        self.disable_ipv6()

    def insmod_eyeq(self):
        self.cmd("sudo rmmod sch_htb; sudo rmmod sch_eyeq; sudo insmod %s" % config['EYEQ_PATH'])
        self.disable_ipv6()

    def rmmod_eyeq(self):
        self.cmd("sudo rmmod sch_eyeq")

    def remove_qdiscs(self):
        iface = self.get_10g_dev()
        self.cmd("sudo %s qdisc del dev %s root" % (config['TC'], iface))

    def add_htb_qdisc(self, rate='5Gbit', mtu=1500):
        iface = self.get_10g_dev()
        self.remove_qdiscs()
        self.rmmod()
        c  = ("sudo %s qdisc add dev %s root handle 1: " "htb default 1;"
              % (config['TC'], iface))
        c += ("sudo %s class add dev %s classid 1:1 parent 1: "
              % (config['TC'], iface))
        c += "htb rate %s mtu %s burst 15k;" % (rate, mtu)
        self.cmd(c)

    def add_htb_hash(self, num_hash_bits=4):
        num_hash_bits = min(8, num_hash_bits)
        num_hash = 1 << num_hash_bits
        self.num_hash = num_hash
        self.hash_mask = hex((1 << num_hash_bits) - 1)
        dev = self.get_10g_dev()
        c  = "sudo %s filter add dev %s parent 1: prio 1 protocol all u32; " % (config['TC'], dev)
        c += "sudo %s filter add dev %s parent 1: prio 1 handle 2: protocol all u32 divisor %s; " % (config['TC'], dev, num_hash)
        c += "sudo %s filter add dev %s protocol all parent 1: prio 1 u32 ht 800::  match ip protocol 0 0 hashkey mask %s at 20  link 2:; " % (config['TC'], dev, self.hash_mask)
        self.cmd(c)

    def add_one_htb_class(self, rate='5Gbit', ceil='5Gbit', port=1000, klass=1):
        dev = self.get_10g_dev()
        c  = "sudo %s class add dev %s classid 1:%d parent 1: htb rate %s ceil %s; " % (config['TC'], dev, klass, rate, ceil)
        c += "sudo %s filter add dev %s protocol all parent 1: prio 1 u32 ht 2:%d: match ip dport %d %d flowid 1:%d" % (config['TC'], dev, hash, port, self.hash_mask, klass)
        self.cmd(c)

    def add_n_htb_class(self, rate='5Gbit', ceil='5Gbit', start_port=1000, num_class=8):
        num_hash = self.num_hash
        dev = self.get_10g_dev()
        c  = "for klass in `seq %s %s`; do " % (start_port, start_port + num_class)
        c += "  hexclass=`perl -e \"printf('%%x', $klass %% %s)\"`; " % (num_hash)
        c += "  sudo %s filter add dev %s protocol all parent 1: prio 1 u32 ht 2:$hexclass: match ip dport $klass %s flowid 1:%s; " % (config['TC'], dev, "0xffff", "$klass")
        c += "  sudo %s class add dev %s classid 1:%s parent 1: htb rate %s ceil %s; " % (config['TC'], dev, "$klass", rate, ceil)
        c += "done;"
        self.cmd(c)

    def htb_class_filter_output(self, dir):
        dev = self.get_10g_dev()
        c  = "sudo %s -s class show dev %s > %s/htb-class.txt" % (config['TC'], dev, dir)
        self.cmd(c)
        c  = "sudo %s -s filter show dev %s > %s/htb-filter.txt" % (config['TC'], dev, dir)
        self.cmd(c)

    def mc_add_htb_qdisc(self, mtu=1500, eyeq_mode=False):
        # Default qdisc class has rate limit of 100Mbit
        iface = self.get_10g_dev()
        self.remove_qdiscs()
        self.rmmod_qfq()
        if eyeq_mode:
            self.insmod_eyeq()
        c  = ("sudo %s qdisc add dev %s root handle 1: htb default 1;"
              % (config['TC'], iface))
        c += ("sudo %s class add dev %s classid 1:1 parent 1: "
              % (config['TC'], iface))
        c += "htb rate 100Mbit mtu %s burst 15k;" % mtu
        self.cmd(c)

    def mc_add_qfq_qdisc(self, mtu=1500):
        # Default qdisc class has rate limit of 100Mbit
        iface = self.get_10g_dev()
        self.remove_qdiscs()
        self.insmod_qfq()
        # 1. Add QFQ root qdisc
        # 2. Create default class
        # 3. Add pfifo qdisc to default class
        # 4. Create default filter
        c  = ("sudo %s qdisc add dev %s root handle 1: qfq;"
              % (config['TC'], iface))

        c += ("sudo %s class add dev %s classid 1:1 parent 1: "
              % (config['TC'], iface))
        c += "qfq weight 100 maxpkt %s;" % mtu

        c += ("sudo %s qdisc add dev %s parent 1:1 pfifo limit 200;"
              % (config['TC'], iface))

        c += ("sudo %s filter add dev %s parent 1: "
              % (config['TC'], iface))
        c += "protocol all prio 2 u32 match u32 0 0 flowid 1:1"
        self.cmd(c)

    def mc_add_qdisc_filter(self, dst_ip, sport=5000, dport=5000, klass=5000):
        dev = self.get_10g_dev()
        c  = ("sudo %s filter add dev %s parent 1: protocol ip prio 1 "
              % (config['TC'], dev))
        c += "u32 match ip dst %s match ip " % dst_ip
        if sport:
            c += "sport %d 0xffff flowid 1:%x" % (sport, klass)
        elif dport:
            c += "dport %d 0xffff flowid 1:%x" % (dport, klass)
        self.cmd(c)

    def mc_add_htb_class(self, rate='5Gbit', ceil='5Gbit', klass=5000, htb_mtu=1500):
        dev = self.get_10g_dev()
        c  = ("sudo %s class add dev %s classid 1:%x parent 1: "
             % (config['TC'], dev, klass))
        c += "htb rate %s ceil %s mtu %s burst 15k;" % (rate, ceil, htb_mtu)
        self.cmd(c)

    def mc_add_qfq_class(self, rate='5Gbit', klass=5000, mtu=1500):
        dev = self.get_10g_dev()
        c  = ("sudo %s class add dev %s classid 1:%x parent 1: "
              % (config['TC'], dev, klass))
        c += "qfq weight %s maxpkt %s;" % (int(rate), mtu)
        c += ("sudo %s qdisc add dev %s parent 1:%x pfifo limit 200;"
              % (config['TC'], dev, klass))
        self.cmd(c)

    def add_intel_hw_rate_limit(self, rate='5000', queue=2):
        # rate in Mbps
        iface = self.get_10g_dev()
        c  = "echo %s | sudo tee " % rate
        c += "/sys/class/net/%s/queues/tx-%d/tx_rate_limit > " % (iface, queue)
        c += "/dev/null"
        self.cmd(c)

    def clear_intel_hw_rate_limits(self, numqueues=16):
        iface = self.get_10g_dev()
        c  = "maxqueue=`echo $[%d - 1]`; " % numqueues
        c += "for queue in `seq 0 $maxqueue`; do "
        c += "  echo 0 | sudo tee /sys/class/net/%s/queues/tx-$queue/tx_rate_limit > /dev/null; " % iface
        c += "  sleep 0.1;"
        c += "done;"
        self.cmd(c)

    def add_mellanox_hw_rate_limit(self, rates=[0,0,0,0,0,0,0,0]):
        # sk_prio 0-7 mapped to TC 0-7 respectively
        # sk_prio 8-15 all mapped to TC 7
        # rate in Mbps for each of the 8 classes.
        # rate = 0 => unlimited
        iface = self.get_10g_dev()
        c = "sudo python %s -i %s -u 0,1,2,3,4,5,6,7,7,7,7,7,7,7,7,7; "
        c = c % (config['TC_WRAP'], iface)
        c += "%s -i %s -p 0,1,2,3,4,5,6,7 -r %s;"
        c = c % (config['MLNX_QOS'], iface, ','.join(str(x) for x in rates))
        self.cmd(c)

    def clear_mellanox_hw_rate_limits(self):
        # Qdiscs should be removed first to configure the mappings
        # Map all sk_priorities to UP 0
        # Map all UPs to TC 0
        # Remove rate limits for all TCs
        self.remove_qdiscs()
        iface = self.get_10g_dev()
        c = "sudo python %s -i %s -u 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0; "
        c = c % (config['TC_WRAP'], iface)
        c += "%s -i %s -p 0,0,0,0,0,0,0,0 -r 0,0,0,0,0,0,0,0;"
        c = c % (config['MLNX_QOS'], iface)
        self.cmd(c)
        self.remove_qdiscs()

    def set_mtu(self, mtu=1500):
        iface = self.get_10g_dev()
        c = "sudo ifconfig %s mtu %s" % (iface, mtu)
        self.cmd(c)

    def add_tbf_qdisc(self, rate='5Gbit'):
        iface = self.get_10g_dev()
        self.remove_qdiscs()
        self.rmmod()
        c  = "sudo %s qdisc add dev %s root handle 1: tbf limit 150000 rate %s burst 3000" % (config['TC'], iface, rate)
        self.cmd(c)

    def ifdown(self):
        self.cmd("sudo ifconfig %s down" % self.get_10g_dev())
    def ifup(self):
        self.cmd("sudo ifconfig %s up; sleep 5" % self.get_10g_dev())

    def qfq_stats(self, dir):
        iface = self.get_10g_dev()
        c = "%s -s class show dev %s > %s/qfq-stats.txt" % (config['TC'], iface, dir)
        self.cmd(c)

    def add_qfq_qdisc(self, rate='5000', mtu=1500, nclass=8, startport=1000):
        iface = self.get_10g_dev()
        self.remove_qdiscs()
        self.rmmod()
        self.ifdown()
        c  = "sudo %s qdisc add dev %s root handle 1: qfq;" % (config['TC'], iface)
        self.cmd(c)
        c = "for klass in {%d..%d}; do " % (startport, startport+nclass-1)
        c += "  sudo %s class add dev %s parent 1: classid 1:$klass qfq weight %s maxpkt 2048; " % (config['TC'], iface, rate)
        c += "  sudo %s filter add dev %s parent 1: protocol all prio 1 u32 match ip dport $klass 0xffff flowid 1:$klass; " % (config['TC'], iface)
        c += "done;"
        """
        for klass in xrange((1 << bits) +1):
            classid = klass + 1
            c += "tc class add dev %s parent 1: classid 1:%d qfq weight %s maxpkt 2048; " % (iface, classid, rate)
            c += "tc filter add dev %s parent 1: protocol all prio 1 u32 match ip sport %d %s flowid 1:%d; " % (iface, klass, mask, classid)
            if klass % 50 == 0:
                self.cmd(c)
                c = ''
        """
        self.cmd(c)
        c = ''
        # Default class
        c += "sudo %s class add dev %s parent 1: classid 1:1 qfq weight %s maxpkt 2048; " % (config['TC'], iface, rate)
        c += "sudo %s filter add dev %s parent 1: protocol all prio 2 u32 match u32 0 0 flowid 1:1; " % (config['TC'], iface)
        self.cmd(c)
        self.ifup()
        self.disable_tso_gso()

    def disable_tso_gso(self):
        # Disable tso/gso
        iface = self.get_10g_dev()
        c = "sudo ethtool -K %s gso off; ethtool -K %s tso off" % (iface, iface)
        self.cmd(c)

    def qfq_add_root(self, rate_default=100):
        iface = self.get_10g_dev()
        self.remove_qdiscs()
        self.ifdown()
        c = "sudo %s qdisc add dev %s root handle 1: qfq;" % (config['TC'], iface)
        self.cmd(c)
        self.disable_tso_gso()
        c += "sudo %s class add dev %s parent 1: classid 1:1 qfq weight %s maxpkt 2048; " % (config['TC'], iface, rate_default)
        c += "sudo %s filter add dev %s parent 1: protocol all prio 2 u32 match u32 0 0 flowid 1:1; " % (config['TC'], iface)
        self.cmd(c)
        self.ifup()

    def qfq_add_class(self, rate, dport):
        dev = self.get_10g_dev()
        c = "sudo %s class add dev %s parent 1: classid 1:%d qfq weight %s maxpkt 2048; " % (config['TC'], dev, dport, rate)
        self.cmd(c)
        c = "sudo %s filter add dev %s parent 1: protocol all prio 1 u32 match ip dport %d 0xffff flowid 1:%d; " % (config['TC'], dev, dport, dport)
        self.cmd(c)

    def killall(self, extra=""):
        for p in self.procs:
            try:
                p.kill()
            except:
                pass
        self.cmd("killall -9 iperf top bwm-ng netperf netserver ethstats %s" % extra)

    def configure_tx_interrupt_affinity(self):
        dev = self.get_10g_dev()
        c = "n=`grep '%s-tx' /proc/interrupts | awk -F ':' '{print $1}' | tr -d '\\n '`; " % dev
        c += " echo 0 > /proc/irq/$n/smp_affinity; "
        self.cmd(c)

    def configure_iface_interrupt_affinity(self, cpus=[0]):
        dev = self.get_10g_dev()
        self.stop_irqbalance()
        c  = "irqs=`grep '%s' /proc/interrupts | awk -F ':' '{print $1}'`; " % dev
        c += "cpus=(%s); cnt=0;" % ' '.join(map(lambda x: str(x), cpus))
        c += "for irq in $irqs; do"
        c += "  ind=$(($cnt %% %d));" % len(cpus)
        c += "  cpu=$((1 << ${cpus[ind]}));"
        c += '  mask=`echo "obase=16; $cpu" | bc`;'
        c += "  echo $mask | sudo tee /proc/irq/$irq/smp_affinity > /dev/null;"
        c += "  cnt=$(($cnt+1));"
        c += "done;"
        self.cmd(c)

    def stop_irqbalance(self):
        c = "sudo service irqbalance stop"
        self.cmd(c)

    def configure_tcp_limit_output_bytes(self):
        c = "sudo sysctl -w net.ipv4.tcp_limit_output_bytes=13107200"
        self.cmd(c)

    # starting common apps
    def start_netserver(self):
        self.cmd_async("%s/netserver" % config['NETPERF_DIR'])

    def start_iperfserver(self):
        self.cmd_async("iperf -s")

    def start_netperf(self, args, outfile):
        self.cmd_async("%s/netperf %s 2>&1 > %s" % (config['NETPERF_DIR'], args, outfile))

    def start_n_netperfs(self, n, args, dir, outfile_prefix, pin=False):
        cmd = "for i in `seq 1 %s`; do (" % n
        if pin:
            cmd += "taskset -c $((i %% %d)) " % 24
        cmd += " %s/netperf -s 10 %s 2>&1" % (config['NETPERF_DIR'], args)
        cmd += " > %s/%s-$i.txt &);" % (dir, outfile_prefix)
        cmd += " done;"
        self.cmd(cmd)
        return

    def start_n_iperfs(self, n, args, dir):
        batchsize = 100
        times = n/batchsize
        while times:
            cmd = "iperf %s -P %s > %s/iperf-%d.txt" % (args, batchsize, dir, times)
            times -= 1
            n -= batchsize
            self.cmd_async(cmd)
        cmd = "iperf %s -P %s > %s/iperf.txt " % (args, n, dir)
        self.cmd_async(cmd)
        return

    def stop_trafgen(self):
        self.cmd("sudo killall -9 %s" % config["TRAFGEN"])

    def start_trafgen_server(self, mode, startport, numports):
        cmd = "%s -s -%s -start_port %s -num_ports %s > /dev/null 2>&1"
        cmd = cmd % (config["TRAFGEN"], mode, startport, numports)
        self.cmd_async(cmd)

    def start_n_trafgen(self, mode, nclass, nprogs, dest, startport,
                        rate=0, send_size=65536, mtu=1500, dir=None, pin=True):
        # Start nprogs traffic sources (tcp or udp), nclass per each program,
        # starting with @startport.  I assume each destination port is
        # one class.
        # mode should be tcp or udp
        # rate is ignored in case of tcp (no app level rate limiting)
        self.cmd("sudo ulimit -n 1024000")
        cpu = 0

        # Default case: each program is responsible for its fraction
        # of all classes.
        nclass_per_prog = nclass / nprogs
        if nclass % nprogs != 0:
            print "Warning: nclass % nprogs is not zero."
        if nclass_per_prog == 0:
            print "Warning: nclass per prog is 0. No traffic will be generated"


        while nprogs:
            nprogs -= 1
            prio = nprogs  # Set socket priority to the program number
            outfile = '%s/trafgen-%d.txt' % (dir, nprogs)
            if dir is None:
                outfile = '/dev/null'

            # Setting sk_priority to 7 requires root permissions
            if (mode == "tcp"):
                cmd = "sudo %s -c %s -tcp -start_port %s -num_ports %s -send_size %s -sk_prio %s -mtu %s > %s 2>&1"
                cmd = cmd % (config["TRAFGEN"], dest, startport, nclass_per_prog, send_size, prio, mtu, outfile)
            elif (mode == "udp"):
                cmd = "sudo %s -c %s -udp -start_port %s -num_ports %s -rate_mbps %s -send_size %s -sk_prio %s -mtu %s > %s 2>&1"
                cmd = cmd % (config["TRAFGEN"], dest, startport, nclass_per_prog, rate, send_size, prio, mtu, outfile)

            startport += nclass_per_prog

            if pin:
                cmd = "taskset -c %d %s" % (cpu, cmd)
            self.cmd_async(cmd)
            cpu += 1
            while cpu in config["EXCLUDE_CPUS"]:
                cpu += 1
                cpu %= config["NUM_CPUS"]
            cpu %= config["NUM_CPUS"]
        return

    # Monitoring scripts
    def start_cpu_monitor(self, dir="/tmp"):
        dir = os.path.abspath(dir)
        path = os.path.join(dir, "cpu.txt")
        self.cmd("mkdir -p %s" % dir)
        cmd = "(top -b -p1 -d1 | grep --line-buffered '^Cpu') > %s" % path
        return self.cmd_async(cmd)

    def start_bw_monitor(self, dir="/tmp", interval_sec=2):
        dir = os.path.abspath(dir)
        path = os.path.join(dir, "net.txt")
        self.cmd("mkdir -p %s" % dir)
        #cmd = "bwm-ng -t %s -o csv -u bits -T rate -C ',' > %s" % (interval_sec * 1000, path)
        cmd = "ethstats -n1 > %s" % (path)
        return self.cmd_async(cmd)

    def start_perf_monitor(self, dir="/tmp", time=30):
        dir = os.path.abspath(dir)
        path = os.path.join(dir, "perf.txt")
        events = [
            "cycles",
            "instructions",
            "cache-references",
            "cache-misses",
            "branch-instructions",
            "branch-misses",
            "L1-dcache-loads",
            "L1-dcache-load-misses",
            "L1-dcache-stores",
            "L1-dcache-store-misses",
            "L1-dcache-prefetches",
            "L1-dcache-prefetch-misses",
            "L1-icache-loads",
            "L1-icache-load-misses",
            "context-switches",
            "cpu-migrations",
            "page-faults",
            ]
        # This command will use debug counters, so you can't run it when
        # running oprofile
        events = ','.join(events)
        cmd = "(sudo perf stat -e %s -a -A sleep %d) > %s 2>&1" % (events, time, path)
        return self.cmd_async(cmd)

    def start_qfq_monitor(self, dir):
        cmd = "python %s -i %s > %s/class-stats.txt"
        cmd = cmd % (config['CLASS_RATE'], self.get_10g_dev(), dir)
        self.cmd_async(cmd)

    def start_mpstat(self, dir):
        cmd = "mpstat 1 > %s/mpstat.txt" % dir
        self.cmd_async(cmd)

        cmd = "mpstat 1 -A > %s/mpstat-all.txt" % dir
        self.cmd_async(cmd)

    def start_sniffer(self, dir="/tmp", board=0):
        # board 0 = captures Tx, board 1 = captures Rx
        dir = os.path.abspath(dir)
        path = os.path.join(dir, "pkt_snf.txt")
        self.cmd("mkdir -p %s" % dir)
        cmd = "taskset -c %d %s -b %d -f %s" % (config['SNIFFER_CPU'],
              config['SNIFFER'], board, path)
        return self.cmd_async(cmd)

    def stop_sniffer(self, dir="/tmp"):
        self.cmd("killall -s INT %s" % config['SNIFFER'])
        print 'waiting for sniffer to flush data...'
        self.cmd("while (pidof -s %s > /dev/null); do sleep 1; done" % config['SNIFFER'])
        snf_file = os.path.join(dir, "pkt_snf.txt")
        self.cmd("tar czf %s/pkt_snf.tar.gz %s --transform='s|%s/||'" % (dir,
                 snf_file, dir.lstrip('/')))
        self.cmd("rm -f %s" % snf_file)

    def start_sniffer_delayed(self, dir="/tmp", board=0, delay=15, duration=10):
        # board 0 = captures Tx, board 1 = captures Rx
        dir = os.path.abspath(dir)
        path = os.path.join(dir, "pkt_snf.txt")
        self.cmd("mkdir -p %s" % dir)
        # Start the sniffer after an initial delay
        cmd = "sleep %s" % delay
        cmd = "%s; taskset -c %d %s -b %d -f %s" % (cmd, config['SNIFFER_CPU'],
                config['SNIFFER'], board, path)
        self.cmd_async(cmd)
        # Kill sniffer after appropriate duration
        cmd = "sleep %s; killall -s INT %s" % (delay + duration,
              config['SNIFFER'])
        return self.cmd_async(cmd)

    def stop_mpstat(self):
        self.cmd("killall -9 mpstat")

    def stop_qfq_monitor(self):
        cmd = "pgrep -f class-rate.py | xargs kill -9"
        self.cmd_async(cmd)

    def start_monitors(self, dir='/tmp', interval=1e8):
        return [self.start_cpu_monitor(dir),
                self.start_bw_monitor(dir)]

    def copy_local(self, src_dir="/tmp", exptid=None, tmpdir="/tmp"):
        """Copy remote experiment output to a local directory for analysis"""
        src_dir = src_dir.rstrip('/')
        tmpdir = tmpdir.rstrip('/')
        if src_dir == tmpdir:
            return
        if exptid is None:
            print "Please supply experiment id"
            return

        # First compress output
        self.cmd("tar czf %s/%s.tar.gz %s --transform='s|%s/||'" % (tmpdir,
                 exptid, src_dir, tmpdir.lstrip('/')))
        opts = "-o StrictHostKeyChecking=no"
        c = "scp %s -r %s:%s/%s.tar.gz ." % (opts, self.hostname(), tmpdir, exptid)
        print "Copying experiment output"
        local_cmd(c)

    def copy_by_host(self, src_dir="/tmp", out_dir="/tmp", exptid=None):
        """
        Collect experiment output from different hosts to central directory
        for analysis
        """
        if exptid is None:
            print "Please supply experiment id"
            return

        src_dir = os.path.abspath(src_dir)
        out_dir = os.path.abspath(out_dir)

        dst_dir = "%s/%s" % (out_dir, self.hostname())
        self.mkdir(dst_dir)
        cmd = "cp -r %s/* %s" % (src_dir, dst_dir)
        self.cmd(cmd)
        print "Copying experiment output from %s" % self.hostname()

    def hostname(self):
        try:
            return socket.gethostbyaddr(self.addr)[0]
        except:
            return self.addr

    def start_profile(self, dir="/tmp"):
        dir = os.path.join(os.path.abspath(dir), "profile")
        c = "mkdir -p %s; export SESSION_DIR=%s;" % (dir, dir)
        c += "opcontrol --reset; opcontrol --start-daemon; opcontrol --start;"
        self.cmd(c)

    def stop_profile(self, dir="/tmp"):
        dir = os.path.join(os.path.abspath(dir), "profile")
        c = "export SESSION_DIR=%s; opcontrol --stop; opcontrol --dump;" % dir
        c += "opcontrol --save profile;"
        c += "opcontrol --deinit; killall -9 oprofiled; opcontrol --deinit;"
        self.cmd(c)
