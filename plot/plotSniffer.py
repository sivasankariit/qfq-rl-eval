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


# Plot CDF of inter-packet arrival times for each traffic class
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
                              "Burst length in packets",
                              "Fractiles",
                              "CDF of burst length in packets")


def main(argv):

    if len(argv) != 3:
        print 'Usage: ', argv[0], 'expt_dir output_filename_prefix'
        sys.exit(-1)

    expt_dir = argv[1]
    plotfile_prefix = argv[2]

    # Plot burstlen in packets
    burstlen_pkt_plot = plotBurstlenPkt(expt_dir)
    burstlen_pkt_plot.save(plotfile_prefix + 'burstlen_pkt.png')


if __name__ == '__main__':
    main(sys.argv)
