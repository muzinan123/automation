# -*- coding:utf-8 -*-

from flask import current_app
from celery.signals import task_postrun, worker_process_init

from app.services.framework.staff_sync import StaffSync
from app.models import db
from app import app, celery


class TaskPool(object):

    @staticmethod
    @celery.task
    def sync_staff():
        StaffSync.sync_department()
        StaffSync.sync_user()
        return "sync staff success"

    @task_postrun.connect
    def close_session(*args, **kwargs):
        # Flask SQLAlchemy will automatically create new sessions for you from
        # a scoped session factory, given that we are maintaining the same app
        # context, this ensures tasks have a fresh session (e.g. session errors
        # won't propagate across tasks)
        db.session.remove()

    @worker_process_init.connect
    def celery_worker_init_db(*args, **kwargs):
        with app.app_context():
            db.init_app(current_app)
