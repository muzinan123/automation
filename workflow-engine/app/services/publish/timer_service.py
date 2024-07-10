# -*- coding: utf8 -*-

import datetime

from app.services.flow.workflow import Workflow
from app.services.publish.hot_pool_service import HotPoolService
from app.models.WorkFlow import WorkFlowInstance
from app.mongodb import flow_data_collection
from app import root_logger


class TimerService(object):

    @staticmethod
    def list_timed_build():
        # 列出状态为prd_wait_build的发布单
        wait_build_list = WorkFlowInstance.query.filter(WorkFlowInstance.current_task_type == 'prd_wait_build')
        timed_build_id_list = list()
        now = datetime.datetime.now()
        for one in wait_build_list:
            flow_id = one.id
            flow_data = flow_data_collection.find_one({'flow_id': flow_id})
            if flow_data and flow_data.get('data') and flow_data.get('data').get('scheduled_time'):
                # 定时发布的项目，提前先把包打好
                app_id_list = flow_data.get('data').get('share_order')
                app_id_list.extend(flow_data.get('data').get('app_order'))
                if flow_data.get('data').get('dzbd'):
                    app_id_list.append(flow_data.get('data').get('dzbd').get('app_id'))
                timed_build_id_list.append({'publish_id': flow_id, 'scheduled_time': flow_data.get('data').get('scheduled_time'), 'app_id_list': app_id_list})
        return sorted(timed_build_id_list, key=lambda s: s.get('scheduled_time'))

    @staticmethod
    def list_timed_publish():
        # 列出状态为prd_wait_publish的发布单
        wait_publish_list = WorkFlowInstance.query.filter(WorkFlowInstance.current_task_type == 'prd_wait_publish')
        timed_publish_id_list = list()
        now = datetime.datetime.now()
        for one in wait_publish_list:
            flow_id = one.id
            flow_data = flow_data_collection.find_one({'flow_id': flow_id})
            if flow_data and flow_data.get('data') and flow_data.get('data').get('scheduled_time'):
                if flow_data.get('data').get('scheduled_time') <= now:
                    timed_publish_id_list.append({'publish_id': flow_id, 'scheduled_time': flow_data.get('data').get('scheduled_time')})
        return sorted(timed_publish_id_list, key=lambda s: s.get('scheduled_time'))

    @staticmethod
    def start_timed_build():
        publish_list = TimerService.list_timed_build()
        for publish in publish_list:
            publish_id = publish.get('publish_id')
            app_id_list = publish.get('app_id_list')
            scheduled_time = publish.get('scheduled_time')
            running_data = list()
            before_data = list()
            for app_id in app_id_list:
                if HotPoolService.has_before_scheduled_prd_app(app_id, scheduled_time):
                    before_data.append(app_id)
                running_one = HotPoolService.get_running_hot_prd_app(app_id)
                if running_one:
                    running_data.append(running_one)
            if before_data or running_data:
                continue
            HotPoolService.start_run_prd_app(publish_id)
            root_logger.info("it's time to build {}!".format(publish_id))
            Workflow.go(publish_id, 'prd_build', 'system')

    @staticmethod
    def start_timed_publish():
        publish_list = TimerService.list_timed_publish()
        for publish in publish_list:
            publish_id = publish.get('publish_id')
            root_logger.info("it's time to publish {}!".format(publish_id))
            Workflow.go(publish_id, 'prd_publish', 'system')
