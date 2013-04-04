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

    # Render plots to HttpResponse and return it
    return render_to_response('plot/individual.html', templateQDict)
