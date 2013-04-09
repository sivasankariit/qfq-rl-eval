import boomslang
import numpy

from MPStatParser import MPStatParser
from pickleExptLogs import readPickledFile
from expsiftUtils import *


# Returns a boomslang ClusteredBars() object to which the specified Bars have
# been added.
def clusteredBarsGraph(bars, xTickLabels, spacing=0.5):
    clusteredBars = boomslang.ClusteredBars()
    clusteredBars.spacing = spacing
    for bar in bars:
        clusteredBars.add(bar)
    clusteredBars.xTickLabels = xTickLabels
    return clusteredBars


# Returns a boomslang Bar() object with the specified parameters
def barGraph(xValues, yValues, yErrors,
             label='Bar', color='red', errorBarColor='black'):
    bar = boomslang.Bar()
    bar.xValues = xValues
    bar.yValues = yValues
    bar.yErrors = yErrors
    bar.color = color
    bar.errorBarColor = errorBarColor
    bar.label = label
    return bar


# Plot comparison graph across different configurations.
#
# Hierarchy:
# - subplot_props: Separate clusterbar subplot for each unique combination of
#                  values for properties in subplot_props [provided as argument
#                  to the function]
# - majorgroup: Separate bargraph for each major group
#               [computed based on the properties specified in
#               subplot_props, cluster_props, and trial_props]
# - cluster_props: Separate xTickLocation or cluster for each unique combination
#                  of values for properties in cluster_props (provided as
#                  argument to the function)
# - trial_props: For each (subplot, majorgroup and cluster) combination, we
#                plot along y-axis, the average and stddev across all
#                directories which only different in the values of properties
#                specified in trial_props and which match the particular
#                (subplot, majorgroup and cluster) combination
#                [provided as argument to the function]
#
# majorgroup of a directory: Ignore the properties in subplot_props,
# cluster_props, and trial_props. The other properties constitute the
# majorgroup. Each majorgroup is denoted by a frozenset of prop=val strings that
# are unique to the majorgroup.
#
# Returns a PlotLayout with multiple subplots
def plotComparisonDirs(dir2props_dict, # dict
                       subplot_props,  # list
                       cluster_props,  # list
                       trial_props,    # list
                       fn_sort_subplots,
                       fn_sort_clusters,
                       fn_sort_majorgroups,
                       fn_get_subplot_title,
                       fn_get_cluster_label,
                       fn_get_majorgroup_label,
                       fn_get_datapoint,
                       xLabel,
                       yLabel):

    # 1. Turn each directory's set of prop=val strings into a dictionary to
    #     easily look up the value of a particular property for the directory
    dir2prop2val_dict = getDir2Prop2ValDict(dir2props_dict)


    # 2. Find all the common and unique properties among all directories
    common_props, unique_props = getCommonAndUniqueProperties(dir2props_dict)


    # 3A. Find all unique values of the subplot properties
    subplot2dir_dict = getDirGroupsByProperty(dir2props_dict, subplot_props,
                                              ignore = False)
    unique_subplots = subplot2dir_dict.keys()
    # 3B. Sort the subplots
    fn_sort_subplots(unique_subplots)


    # 4. Find all unique values of the cluster properties
    cluster2dir_dict = getDirGroupsByProperty(dir2props_dict, cluster_props,
                                              ignore = False)
    unique_clusters = cluster2dir_dict.keys()
    # 3B. Sort the clusters
    fn_sort_clusters(unique_clusters)


    # 5. Find all unique major groupings or configurations:
    #    Ignore the properties in subplot_props, cluster_props, and
    #    trial_props. The other properties constitute the majorgroup.
    #    Each majorgroup is denoted by a frozenset of prop=val strings that
    #    are unique to the majorgroup.
    majorgroup2dir_dict = getDirGroupsByProperty(
            dir2props_dict,
            subplot_props + cluster_props + trial_props,
            ignore = True)
    unique_majorgroups = majorgroup2dir_dict.keys()


    # 6A. Allocate a separate xValue in the graphs for each cluster
    cluster2xValue_dict = {}
    for xValue in xrange(len(unique_clusters)):
        cluster2xValue_dict[unique_clusters[xValue]] = xValue


    # 6B. Compute a list of labels for the clusters (in the same order as
    #     unique_clusters)
    unique_cluster_labels = [ fn_get_cluster_label(cluster)
                              for cluster in unique_clusters ]


    # 6C. Allocate a color for bar graphs of each major group
    colors = ('y', 'g', 'c', 'r', 'm', 'b')
    majorgroup2color_dict = {}
    for index, majorgroup in enumerate(unique_majorgroups):
        majorgroup2color_dict[majorgroup] = colors[index % len(colors)]


    # 7. Create an individual datapoints list:
    #    for each unique subplot,
    #    for each unique majorgroup,
    #    for each unique cluster.
    datapoints_dict = {}
    for subplot in unique_subplots:
        datapoints_dict[subplot] = {}
        for majorgroup in unique_majorgroups:
            datapoints_dict[subplot][majorgroup] = {}
            for cluster in unique_clusters:
                datapoints_dict[subplot][majorgroup][cluster] = []


    # 8. Visit each directory and populate the corresponding datapoints list for
    #    that directory
    for directory, prop_vals in dir2props_dict.iteritems():
        # Find the subplot, majorgroup, and cluster of the directory
        subplot = onlyIncludeProps(prop_vals, subplot_props)
        majorgroup = removeIgnoredProps(
                prop_vals, subplot_props + cluster_props + trial_props)
        cluster = onlyIncludeProps(prop_vals, cluster_props)

        # Compute the datapoint for the directory
        datapoint = fn_get_datapoint(directory)

        # Add the data point
        datapoints_dict[subplot][majorgroup][cluster].append(datapoint)


    # 9. For each (subplot, majorgroup) combo, create a bar graph
    all_bars_dict = {}
    for subplot, subplot_dict in datapoints_dict.iteritems():
        all_bars_dict[subplot] = {}

        for majorgroup, majorgroup_dict in subplot_dict.iteritems():
            majorgroup_label = fn_get_majorgroup_label(majorgroup, common_props)

            bar = barGraph([], [], [], color=majorgroup2color_dict[majorgroup],
                           label=majorgroup_label)
            all_bars_dict[subplot][majorgroup] = bar


    # 10. Compute average and stddev for each (subplot, majorgroup, cluster)
    #     combination. This represents the avg and stddev across multiple
    #     trials. Add these to the corresponding bar graphs.
    for subplot, subplot_dict in datapoints_dict.iteritems():
        for majorgroup, majorgroup_dict in subplot_dict.iteritems():
            bar_values = []
            for cluster, datapoints in majorgroup_dict.iteritems():
                avg = numpy.average(datapoints)
                stddev = numpy.std(datapoints)

                # Append an (xValue, yValue, yError) tuple
                bar_values.append((cluster2xValue_dict[cluster], avg, stddev))

            # Sort the tuples by xValue and assign it to the bar graph.
            # (Boomslang requires the values to be sorted)
            bar = all_bars_dict[subplot][majorgroup]
            bar_values.sort(key=lambda tup: tup[0])
            # Unzip bar_values into individual lists
            (bar.xValues, bar.yValues, bar.yErrors) = zip(*bar_values)


    # 11. Create a clusteredBars Plot for each subplot.
    #     Place all the Plots in a single PlotLayout
    layout = boomslang.PlotLayout()
    for subplot in unique_subplots:
        title = fn_get_subplot_title(subplot)

        subplot_bars = [ all_bars_dict[subplot][majorgroup]
                         for majorgroup in unique_majorgroups ]

        clusteredBars = clusteredBarsGraph(subplot_bars, unique_cluster_labels)

        plot = boomslang.Plot()

        # Add the clusteredbars for the particular subplot
        plot.add(clusteredBars)

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

        # Add the plot to the layout
        layout.addPlot(plot)


    # 12. Return the final PlotLayout with all the graphs
    return layout
