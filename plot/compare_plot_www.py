# Author(s): Sivasankar Radhakrishnan (sivasankar@cs.ucsd.edu)

from __future__ import division
import base64
import django
import imp
import os
import sys
import StringIO
from datetime import datetime
from datetime import timedelta
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.utils import http

from expsiftUtils import getCommonAndUniqueProperties
from plotCPUCompare import plotCPUComparisonDirs
from plotBurstCompare import plotAvgBurstLenPktComparisonDirs
from plotBurstCompare import plotBurstLenUsecComparisonDirs


def getTimeDeltaSeconds(delta = timedelta(0)):
    if sys.version_info < (2, 7):
        td = delta
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
    else:
        return delta.total_seconds()


# This function returns the response comparing multiple experiment directories,
# as a Django HttpResponse object
def summaryPlot(dir2props_dict = {}):

    if not dir2props_dict:
        return django.http.HttpResponse('No experiment directories selected.')

    start_time = datetime.now()

    # Generate the CPU comparison plot
    (subplot_titles,
     majorgroup_labels,
     cluster_labels,
     clusterdir_dict,
     plot_cpu) = plotCPUComparisonDirs(dir2props_dict)

    # Generate the burst length in packets comparison plot
    (_, _, _, _,
     plot_burstlen_pkt) = plotAvgBurstLenPktComparisonDirs(dir2props_dict)

    # Generate the burst length in usecs comparison plot
    (_, _, _, _,
     plot_burstlen_usec) = plotBurstLenUsecComparisonDirs(dir2props_dict)

    end_time_plot = datetime.now()

    # Save the plots as base64 strings
    imgdata_cpu = StringIO.StringIO()
    plot_cpu.save(imgdata_cpu, format='png')
    imgdata_cpu.seek(0)  # rewind the data

    imgdata_burstlen_pkt = StringIO.StringIO()
    plot_burstlen_pkt.save(imgdata_burstlen_pkt, format='png')
    imgdata_burstlen_pkt.seek(0)  # rewind the data

    imgdata_burstlen_usec = StringIO.StringIO()
    plot_burstlen_usec.save(imgdata_burstlen_usec, format='png')
    imgdata_burstlen_usec.seek(0)  # rewind the data

    end_time_plot_save = datetime.now()

    uri_cpu = ('data:image/png;base64,' +
               http.urlquote(base64.b64encode(imgdata_cpu.buf)))
    uri_burstlen_pkt = ('data:image/png;base64,' +
               http.urlquote(base64.b64encode(imgdata_burstlen_pkt.buf)))
    uri_burstlen_usec = ('data:image/png;base64,' +
               http.urlquote(base64.b64encode(imgdata_burstlen_usec.buf)))

    end_time_img_encode = datetime.now()

    # Find all common and unique properties among all experiment directories
    common_props, unique_props = getCommonAndUniqueProperties(dir2props_dict)
    common_props_sorted = sorted(common_props)
    max_prop_len = 0
    for prop in common_props_sorted:
        if max_prop_len < len(prop):
            max_prop_len = len(prop)
    common_props_cols = 3
    if max_prop_len <= 40:
        common_props_cols = 3
    elif max_prop_len <= 60:
        common_props_cols = 2
    else:
        common_props_cols = 1

    def directoryActualUrl(directory):
        expt_logs_conf = getattr(settings, 'EXPT_LOGS', {})
        expt_logs_dir = expt_logs_conf['directory']
        return (reverse('expsift.views.home') +
                'expt-logs/' +  directory[len(expt_logs_dir):])

    def directoryExptPageUrl(directory):
        return (reverse('expsift.views.individual_expt_base') + '?' +
                http.urlencode({'directory' : directory}, True))

    def directoryUrl(directory):
        if getattr(settings, 'ENABLE_INDIVIDUAL_EXPT_PAGE', False):
            return directoryExptPageUrl(directory)
        else:
            return directoryActualUrl(directory)

    # Compute the URLs for experiment directories
    clusterdir_url_dict = {}
    for s_title, subplot_dict in clusterdir_dict.iteritems():
        clusterdir_url_dict[s_title] = {}
        for m_label, majorgroup_dict in subplot_dict.iteritems():
            clusterdir_url_dict[s_title][m_label] = {}
            for c_label, directories in majorgroup_dict.iteritems():
                clusterdir_url_dict[s_title][m_label][c_label] = (
                        [ (dir, directoryUrl(dir)) for dir in directories ])

    # Render plots to HttpResponse and return it
    templateQDict = {'uri_cpu' : uri_cpu}
    templateQDict['uri_burstlen_pkt'] = uri_burstlen_pkt
    templateQDict['uri_burstlen_usec'] = uri_burstlen_usec

    templateQDict['common_props'] = common_props_sorted
    templateQDict['common_props_cols'] = common_props_cols

    templateQDict['subplot_titles'] = subplot_titles
    templateQDict['majorgroup_labels'] = majorgroup_labels
    templateQDict['cluster_labels'] = cluster_labels
    templateQDict['clusterdir_url_dict'] = clusterdir_url_dict

    end_time = datetime.now()

    templateQDict['time_total'] = getTimeDeltaSeconds(end_time - start_time)
    templateQDict['time_plot'] = getTimeDeltaSeconds(end_time_plot - start_time)
    templateQDict['time_plot_save'] = getTimeDeltaSeconds(end_time_plot_save -
                                                          end_time_plot)
    templateQDict['time_img_encode'] = getTimeDeltaSeconds(end_time_img_encode -
                                                           end_time_plot_save)

    return render_to_response('plot/summary_plots.html', templateQDict)
