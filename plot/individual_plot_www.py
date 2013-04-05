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

    if not expt_dir:
        return django.http.HttpResponse('No experiment directory specified.')

    # URLs of plots
    directory_url = templateQDict["directory_url"]
    uri_ipt = directory_url + '/plot/ipt.png'
    uri_burstlen_pkt = directory_url + '/plot/burstlen_pkt.png'
    uri_burstlen_usec = directory_url + '/plot/burstlen_usec.png'

    templateQDict["uri_ipt"] = uri_ipt
    templateQDict["uri_burstlen_pkt"] = uri_burstlen_pkt
    templateQDict["uri_burstlen_usec"] = uri_burstlen_usec

    # Render plots to HttpResponse and return it
    return render_to_response('plot/individual.html', templateQDict)
