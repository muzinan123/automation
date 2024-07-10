# -*- coding:utf-8 -*-

from __future__ import absolute_import, unicode_literals

from app import celery
from celery.bin import beat

if __name__ == '__main__':
    beat = beat.beat(app=celery)
    options = {
        'loglevel': 'INFO',
        'scheduler_cls': 'app.services.framework.scheduler.DatabaseScheduler'
    }
    beat.run(**options)
