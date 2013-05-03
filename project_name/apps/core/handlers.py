# -*- coding: utf-8 -*-
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import logging
logger = logging.getLogger('{{ project_name }}')
