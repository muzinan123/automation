# -*- coding:utf-8 -*-

from flask import current_app
from celery.signals import task_postrun, worker_process_init

from app.services.framework.staff_sync import StaffSync
from app.services.docker_engine_service import DockerEngineService
from app.services.docker_cluster_service import DockerClusterService
from app.services.k8s_node_service import K8SNodeService
from app.services.k8s_cluster_service import K8SClusterService
from app.models import db
from app import app, celery


class TaskPool(object):

    @staticmethod
    @celery.task
    def sync_department_and_user():
        StaffSync.sync_department()
        StaffSync.sync_user()
        return "department and user sync success"

    @staticmethod
    @celery.task
    def sync_docker_engine():
        DockerEngineService.sync_engine()
        return "docker engine sync success"

    @staticmethod
    @celery.task
    def sync_docker_cluster():
        DockerClusterService.sync_cluster()
        return "docker cluster sync success"

    @staticmethod
    @celery.task
    def sync_k8s_node():
        K8SNodeService.sync_node()
        return "k8s node sync success"

    @staticmethod
    @celery.task
    def sync_k8s_cluster():
        K8SClusterService.sync_cluster()
        return "k8s cluster sync success"

    @staticmethod
    @celery.task
    def sync_k8s_node_info_from_ecs():
        K8SNodeService.sync_info_from_ecs()
        return "k8s node sync info from ecs success"

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
