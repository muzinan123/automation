# -*- coding:utf-8 -*-

from flask import Blueprint
import datetime
from app import app

filterProfile = Blueprint('filterProfile', __name__)


@app.template_filter('adjustnum_k')
def adjustnum_filter(s):
    if s < 1000:
        return str(s)+' K'
    elif s < 1000000:
        return str(round(s/1024.0, 2))+' M'
    elif s < 1000000000:
        return str(round(s/1024.0/1024.0, 2))+' G'
    else:
        return str(round(s / 1024.0 / 1024.0 / 1024.0, 2)) + ' T'


@app.template_filter('adjustnum')
def adjustnum_filter(s):
    s /= 1024
    if s < 1024:
        return str(s)+' K'
    elif s < 1048576:
        return str(round(s/1024.0, 2))+' M'
    elif s < 1073741824:
        return str(round(s/1024.0/1024.0, 2))+' G'
    else:
        return str(round(s / 1024.0 / 1024.0 / 1024.0, 2)) + ' T'


@app.template_filter('percentage')
def percentage_filter(s):
    return str(round(s*100, 2))


@app.template_filter('average')
def average_filter(s):
    if len(s) > 0:
        return round(sum(s) / float(len(s)), 2)
    else:
        return 0


@app.template_filter('max')
def max_filter(s):
    if s:
        return max(s)
    else:
        return 0


@app.template_filter('notnone')
def notnone_filter(s):
    if s:
        return s
    else:
        return '-'


@app.template_filter('timestamp2str')
def timestamp_to_str(s):
    if s:
        if s > 20000000000:
            return datetime.datetime.fromtimestamp(s/1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            return datetime.datetime.fromtimestamp(s).strftime('%Y-%m-%d %H:%M:%S')
    else:
        return '-'


@app.template_filter('get_env_name')
def get_env_name(s):
    if s == 'prd':
        return u'生产'
    elif s == 'pre':
        return u'预发'
    elif s == 'test':
        return u'测试'


@app.template_filter('get_org_name')
def get_org_name(s):
    if s == 'ZA':
        return u'众安保险'
    elif s == 'ZATECH':
        return u'众安科技'
