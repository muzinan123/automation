# -*- coding:utf-8 -*-

import re
import pytz
import redis as redispy
from redis.sentinel import Sentinel
from flask import request
from celery import Celery
from app import app


class Util(object):

    if app.config.get('REDIS_CLUSTER'):
        sentinel = Sentinel(app.config['REDIS_SENTINEL_LIST'], socket_timeout=0.1)
        redis = sentinel.master_for(app.config['REDIS_CLUSTER_NAME'], db=app.config['REDIS_DB'], socket_timeout=2)
    else:
        redis = redispy.StrictRedis(app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DB'],
                                    password=app.config['REDIS_PASS'])

    @staticmethod
    def can_tune_to(v, t):
        try:
            t(v)
            return True
        except ValueError:
            return False

    @staticmethod
    def check_date_str(s):
        try:
            if re.match('\d\d\d\d-\d\d-\d\d', s):
                return s
        except:
            return None
        return None

    @staticmethod
    def utc2local(d):
        local_tz = pytz.timezone(app.config.get('TIMEZONE'))
        local_dt = d.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_tz.normalize(local_dt)

    @staticmethod
    def get_ip_addr():
        ip1 = request.headers.get('X-Forwarded-For')
        ip2 = request.headers.get('X-Real-Ip')
        ip3 = request.remote_addr
        if ip1:
            return ip1.split(',')[0]
        elif ip2:
            return ip2.split(',')[0]
        else:
            return ip3

    @staticmethod
    def jsbool2pybool(val):
        if val == 'true':
            return True
        elif val == 'false':
            return False

    @staticmethod
    def make_celery(app):
        celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
        celery.conf.update(app.config)
        TaskBase = celery.Task

        class ContextTask(TaskBase):
            abstract = True

            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)

        celery.Task = ContextTask
        return celery
