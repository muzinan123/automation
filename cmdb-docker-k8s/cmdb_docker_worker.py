# -*- coding:utf-8 -*-

from __future__ import absolute_import, unicode_literals

from app import celery
from celery.bin import worker

if __name__ == '__main__':
    worker = worker.worker(app=celery)
    options = {
        'loglevel': 'INFO'
    }
    worker.run(**options)