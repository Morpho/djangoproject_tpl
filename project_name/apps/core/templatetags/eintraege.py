# -*- coding: utf-8 -*-
from django import template
register = template.Library()
from ..redishelper import get_redis

redis = get_redis()

@register.filter
def friendname(value):
    return redis.hget('fbuser:%s' % value, 'name')

@register.filter
def friendfirstname(value):
    return redis.hget('fbuser:%s' % value, 'first_name')
    
@register.filter
def friendlastname(value):
    return redis.hget('fbuser:%s' % value, 'last_name')
    
@register.filter
def floattoint(value):
    return int(value)
    