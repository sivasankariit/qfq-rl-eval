#! /bin/sh

# Documentation here: http://www.linuxfoundation.org/collaborate/workgroups/networking/pktgen
rmmod pktgen
modprobe pktgen
dev=eth2

function pgset() {
    local result

    echo $1 > $PGDEV

    result=`cat $PGDEV | fgrep "Result: OK:"`
    if [ "$result" = "" ]; then
         cat $PGDEV | fgrep Result:
    fi
}

function pg() {
    echo inject > $PGDEV
    cat $PGDEV
}

# Config Start Here -----------------------------------------------------------

# thread config
PGDEV=/proc/net/pktgen/kpktgend_2
  echo "Removing all devices"
 pgset "rem_device_all" 
  echo "Adding $dev"
 pgset "add_device $dev" 


# device config
# delay 0 means maximum speed.

CLONE_SKB="clone_skb 100"
# NIC adds 4 bytes CRC
PKT_SIZE="pkt_size 1000"

# COUNT 0 means forever
#COUNT="count 0"
COUNT="count 10000000"
DELAY="delay 0"

PGDEV=/proc/net/pktgen/$dev
  echo "Configuring $PGDEV"
 pgset "$COUNT"
 pgset "$CLONE_SKB"
 pgset "$PKT_SIZE"
 pgset "$DELAY"
 pgset "dst 192.168.2.2"
 pgset "dst_mac  00:00:c9:bc:44:be"

# Time to run
PGDEV=/proc/net/pktgen/pgctrl

 echo "Running... ctrl^C to stop"
 pgset "start" 
 echo "Done"

echo Result can be vieved in /proc/net/pktgen/$dev
