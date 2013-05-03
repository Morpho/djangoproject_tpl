# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render, redirect
from django.conf import settings
from .models import *
from .forms import *
from .tasks import *

import logging
logger = logging.getLogger('{{ project_name }}')

def index(request):
    return render(request, 'base.html', {
        
    })
