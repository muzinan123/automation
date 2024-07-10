# -*- coding: utf8 -*-

from app.services.nexus_service import NexusService
from app.services.publish.timer_service import TimerService
from app.services.user_credit_service import UserCreditService
from app.services.publish.publish_statistics_service import PublishStatisticsService
from app.services.project.sql_scripts_project_service import SQLScriptsProjectService
from app.services.flow.workflow import Workflow
import datetime
from app import celery, task_logger


class TaskPool(object):

    @staticmethod
    @celery.task
    def sync_nexus_parent_version():
        NexusService.sync_dependency_from_svn_pom()
        return "sync nexus ok"

    @staticmethod
    @celery.task
    def auto_build():
        try:
            TimerService.start_timed_build()
            return "success"
        except Exception, e:
            task_logger.exception("auto_build error: %s", e)
            return "fail"

    @staticmethod
    @celery.task
    def auto_publish():
        try:
            TimerService.start_timed_publish()
            return "success"
        except Exception, e:
            task_logger.exception("auto_publish error: %s", e)
            return "fail"

    @staticmethod
    @celery.task
    def cal_credit(day):
        if not day:
            end = datetime.date.today()
            start = end - datetime.timedelta(days=1)
        else:
            start = datetime.datetime.strptime(day, "%Y-%m-%d")
            end = start + datetime.timedelta(days=1)
        UserCreditService.cal_credit(start, end)
        return "cal credit ok"

    @staticmethod
    @celery.task
    def add_product_publish_statistics():
        end_date = datetime.datetime.today()
        begin_date = end_date + datetime.timedelta(days=-1)
        begin = datetime.datetime.strftime(begin_date, '%Y-%m-%d %H:%M:%S')
        end = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        print begin, end
        try:
            PublishStatisticsService.add_product_publish_statistics(begin, end)
            return "success"
        except Exception, e:
            task_logger.exception("add_product_publish_statistics error: %s", e)
            return "fail"

    @staticmethod
    @celery.task
    def add_publish_abandon_statistics():
        end_date = datetime.datetime.today()
        begin_date = end_date + datetime.timedelta(days=-1)
        begin = datetime.datetime.strftime(begin_date, '%Y-%m-%d %H:%M:%S')
        end = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        try:
            PublishStatisticsService.add_publish_abandon_statistics(begin, end)
            return "success"
        except Exception, e:
            task_logger.exception("add_publish_abandon_statistics error: %s", e)
            return "fail"

    @staticmethod
    @celery.task
    def add_project_publish_statistics():
        end_date = datetime.datetime.today()
        begin_date = end_date + datetime.timedelta(days=-1)
        begin = datetime.datetime.strftime(begin_date, '%Y-%m-%d %H:%M:%S')
        end = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        try:
            PublishStatisticsService.add_project_publish_statistics(begin, end)
            return "success"
        except Exception, e:
            task_logger.exception("add_project_publish_statistics error: %s", e)
            return "fail"

    @staticmethod
    @celery.task
    def add_product_publish_statistics_on_fixed_day(day):
        try:
            begin_date = datetime.datetime.strptime(day, "%Y-%m-%d")
            end_date = begin_date + datetime.timedelta(days=1)
            begin = datetime.datetime.strftime(begin_date, '%Y-%m-%d %H:%M:%S')
            end = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
            PublishStatisticsService.add_product_publish_statistics(begin, end)
            return "success"
        except Exception, e:
            task_logger.exception("add_product_publish_statistics error: %s", e)
            return "fail"

    @staticmethod
    @celery.task
    def add_publish_abandon_statistics_on_fixed_day(day):
        try:
            begin_date = datetime.datetime.strptime(day, "%Y-%m-%d")
            end_date = begin_date + datetime.timedelta(days=1)
            begin = datetime.datetime.strftime(begin_date, '%Y-%m-%d %H:%M:%S')
            end = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
            PublishStatisticsService.add_publish_abandon_statistics(begin, end)
            return "success"
        except Exception, e:
            task_logger.exception("add_publish_abandon_statistics error: %s", e)
            return "fail"

    @staticmethod
    @celery.task
    def add_project_publish_statistics_on_fixed_day(day):
        try:
            begin_date = datetime.datetime.strptime(day, "%Y-%m-%d")
            end_date = begin_date + datetime.timedelta(days=1)
            begin = datetime.datetime.strftime(begin_date, '%Y-%m-%d %H:%M:%S')
            end = datetime.datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
            PublishStatisticsService.add_project_publish_statistics(begin, end)
            return "success"
        except Exception, e:
            task_logger.exception("add_project_publish_statistics error: %s", e)
            return "fail"

    @staticmethod
    @celery.task
    def check_sql_scripts_project_status():
        result, publish_ids = SQLScriptsProjectService.check_sql_scripts_project_status()
        if result and len(publish_ids):
            for publish_id in publish_ids:
                Workflow.go(publish_id, 'timeout')
        return "success"

