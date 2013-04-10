#!/usr/bin/env python

import argparse
import matplotlib
matplotlib.rcParams['backend'] = 'Agg'
import boomslang
import os
import sys

from SnifferParser import SnifferParser
from pickleExptLogs import readPickledFile
from expsiftUtils import readDirTagFileProperty


parser = argparse.ArgumentParser(description='Plot sniffer data')
parser.add_argument('expt_dir', help='Experiment directory')
parser.add_argument('plotfile_prefix',
                    help='Filename prefix for output graphs')
parser.add_argument('--force_replot', '-f', dest='force_replot',
                    help='Replot graphs even if they already exist ',
                    action="store_true")


def idealIptNsec(packet_len, rate_gbps):
    # 24 bytes framing overhead per packet in Ethernet
    FRAMING_OVERHEAD = 24
    return (packet_len + FRAMING_OVERHEAD) * 8 / (rate_gbps)


# Plot a CDF graph with 3 kinds of lines
# 1. CDF Line   : varying colors for each individual cdf line
# 2. Avg VLine  : Average in green color
# 3. pc99 VLine : (99th percentile) in red color
def plotCDFGraphSimple(cdf_data, avg_data, pc99_data,
                       xLabel, yLabel, title):

    colors = ('b', 'g', 'r', 'c', 'm', 'y')

    # We must have same number of lines for CDF, avg and pc99
    assert(len(cdf_data) == len(avg_data))
    assert(len(avg_data) == len(pc99_data))

    plot = boomslang.Plot()

    # Plot all CDF lines
    for index in xrange(len(cdf_data)):
        data = cdf_data[index]

        cdf_line = boomslang.Utils.getCDF(data)
        cdf_line.lineWidth = 2
        cdf_line.color = colors[index % len(colors)]
        plot.add(cdf_line)

    # Plot VLines for avg
    avg_vline = boomslang.VLine(color="green", lineStyle="--")
    avg_vline.xValues = avg_data
    avg_vline.label = "Avg."
    plot.add(avg_vline)

    # Plot VLines for pc99
    pc99_vline = boomslang.VLine(color="red", lineStyle="--")
    pc99_vline.xValues = pc99_data
    pc99_vline.label = "99th perc."
    plot.add(pc99_vline)

    # Set title and axes labels
    plot.setXLabel(xLabel)
    plot.setYLabel(yLabel)
    plot.setTitle(title)
    plot.hasLegend()

    # Font size
    plot.setLegendLabelSize("small")
    plot.setTitleSize("small")
    plot.setAxesLabelSize("small")
    plot.setXTickLabelSize("small")
    plot.setYTickLabelSize("small")

    # Grid
    plot.grid.color = "lightgray"
    plot.grid.style = "dotted"
    plot.grid.lineWidth = 0.8
    plot.grid.visible = True

    return plot


# Plot CDF of burst lengths in packets for each traffic class
def plotBurstlenPkt(directory):
    # Read burst lengths from the sniffer pickled files
    burstlen_pkt_pfile = os.path.join(directory, 'pickled/burstlen_pkt.txt')
    (burstlen_pkt, summary) = readPickledFile(burstlen_pkt_pfile)
    ports = summary.keys()

    cdf_data = []
    avg_data = []
    pc99_data = []

    for port in ports:
        cdf_data.append(burstlen_pkt[port])
        avg, pc99 = summary[port]
        avg_data.append(avg)
        pc99_data.append(pc99)

    return plotCDFGraphSimple(cdf_data, avg_data, pc99_data,
                              "Burst length (in packets)",
                              "Fractiles",
                              "CDF of burst length in packets")


# Plot CDF of burst lengths in microseconds for each traffic class
def plotBurstlenUsec(directory):
    # Read burst lengths from the sniffer pickled files
    burstlen_nsec_pfile = os.path.join(directory, 'pickled/burstlen_nsec.txt')
    (burstlen_nsec, summary) = readPickledFile(burstlen_nsec_pfile)
    ports = summary.keys()

    cdf_data = []
    avg_data = []
    pc99_data = []

    for port in ports:
        # Convert from nanoseconds to microseconds for plotting
        cdf_data.append(map(lambda x: x / 1000.0, burstlen_nsec[port]))
        avg, pc99 = summary[port]
        avg_data.append(avg / 1000.0)
        pc99_data.append(pc99 / 1000.0)

    return plotCDFGraphSimple(cdf_data, avg_data, pc99_data,
                              "Burst length (in microseconds)",
                              "Fractiles",
                              "CDF of burst length in microseconds")


# Plot CDF of inter-packet arrival times microseconds for each traffic class
def plotIpt(directory):
    # Read inter-packet arrival times from the sniffer pickled files
    ipt_pfile = os.path.join(directory, 'pickled/ipt.txt')
    (ipt, summary) = readPickledFile(ipt_pfile)
    ports = summary.keys()

    # Read packet lengths from sniffer pickled files
    pkt_len_freq_pfile = os.path.join(directory, 'pickled/pkt_len_freq.txt')
    (most_freq_pkt_len, pkt_len_freq) = readPickledFile(pkt_len_freq_pfile)

    cdf_data = []
    avg_data = []
    pc99_data = []

    for port in ports:
        # Convert from nanoseconds to microseconds for plotting
        cdf_data.append(map(lambda x: x / 1000.0, ipt[port]))
        avg, pc99 = summary[port]
        avg_data.append(avg / 1000.0)
        pc99_data.append(pc99 / 1000.0)

    # Generate CDF plot
    plot = plotCDFGraphSimple(cdf_data, avg_data, pc99_data,
                              "Inter-packet time (in microseconds)",
                              "Fractiles",
                              "CDF of inter-packet time (not inter-packet gap) "
                              "in microseconds")

    # Compute ideal inter-packet arrival time for most frequently seen packet
    # length in the trace
    rate_mbps = float(readDirTagFileProperty(directory, "rate_mbps"))
    nclasses = int(readDirTagFileProperty(directory, "nclasses"))
    rate_per_class_gbps = rate_mbps / (1000.0 * nclasses)
    ideal_nsec = idealIptNsec(most_freq_pkt_len, rate_per_class_gbps)

    # Add VLine for the ideal inter-packet time
    # Also convert from nanoseconds to microseconds for plotting
    ideal_vline = boomslang.VLine(color="magenta", lineStyle="-.", width=2)
    ideal_vline.xValues = [ ideal_nsec / 1000.0 ]
    ideal_vline.label = "Ideal"
    plot.add(ideal_vline)

    return plot


def main(argv):
    # Parse flags
    args = parser.parse_args()

    # Plot inter-packet arrival time in microseconds
    if (args.force_replot or
        not os.path.exists(args.plotfile_prefix + 'ipt.png')):
        ipt_plot = plotIpt(args.expt_dir)
        ipt_plot.save(args.plotfile_prefix + 'ipt.png')

    # Plot burstlen in packets
    if (args.force_replot or
        not os.path.exists(args.plotfile_prefix + 'burstlen_pkt.png')):
        burstlen_pkt_plot = plotBurstlenPkt(args.expt_dir)
        burstlen_pkt_plot.save(args.plotfile_prefix + 'burstlen_pkt.png')

    # Plot burstlen in microseconds
    if (args.force_replot or
        not os.path.exists(args.plotfile_prefix + 'burstlen_usec.png')):
        burstlen_usec_plot = plotBurstlenUsec(args.expt_dir)
        burstlen_usec_plot.save(args.plotfile_prefix + 'burstlen_usec.png')


if __name__ == '__main__':
    main(sys.argv)
