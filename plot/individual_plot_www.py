# Author(s): Sivasankar Radhakrishnan (sivasankar@cs.ucsd.edu)

from __future__ import division
import base64
import django
import imp
import os
import sys
import StringIO
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.utils import http


# This function returns the response for an individual experiment directory as a
# Django HttpResponse object
def individual_plot(expt_dir = '', properties = set(), templateQDict = {}):

    expt_logs_conf = getattr(settings, 'EXPT_LOGS', {})
    expt_logs_dir = expt_logs_conf['directory']

    if not expt_dir:
        return django.http.HttpResponse('No experiment directory specified.')

    # URLs of plots
    uri_ipt = (reverse('expsift.views.home') + 'expt-logs/' +
            expt_dir[len(expt_logs_dir):] + '/plot/ipt.png')
    uri_burstlen_pkt = (reverse('expsift.views.home') + 'expt-logs/' +
            expt_dir[len(expt_logs_dir):] + '/plot/burstlen_pkt.png')
    uri_burstlen_usec = (reverse('expsift.views.home') + 'expt-logs/' +
            expt_dir[len(expt_logs_dir):] + '/plot/burstlen_usec.png')

    templateQDict["uri_ipt"] = uri_ipt
    templateQDict["uri_burstlen_pkt"] = uri_burstlen_pkt
    templateQDict["uri_burstlen_usec"] = uri_burstlen_usec

    # Render plots to HttpResponse and return it
    return render_to_response('plot/individual.html', templateQDict)
