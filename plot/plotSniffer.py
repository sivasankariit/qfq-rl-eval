#!/usr/bin/env python

import sys
import os
import boomslang
import sys

from SnifferParser import SnifferParser
from pickleExptLogs import readPickledFile


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


def main(argv):

    if len(argv) != 3:
        print 'Usage: ', argv[0], 'expt_dir output_filename_prefix'
        sys.exit(-1)

    expt_dir = argv[1]
    plotfile_prefix = argv[2]

    # Plot burstlen in packets
    burstlen_pkt_plot = plotBurstlenPkt(expt_dir)
    burstlen_pkt_plot.save(plotfile_prefix + 'burstlen_pkt.png')

    # Plot burstlen in microseconds
    burstlen_usec_plot = plotBurstlenUsec(expt_dir)
    burstlen_usec_plot.save(plotfile_prefix + 'burstlen_usec.png')


if __name__ == '__main__':
    main(sys.argv)
