# -*- coding:utf-8 -*-

from datetime import datetime

from app.services.project.project_service import ProjectService
from app.services.publish.hot_pool_service import HotPoolService
from app.services.framework.kafka_service import KafkaService
from app.services.framework.message_service import MessageService
from app.services.project.project_record_service import ProjectRecordService
from app.services.app_branch_service import AppBranchService
from app.services.jira_service import JiraService
from app.mongodb import flow_data_collection, publish_switch_collection
from app import app, root_logger


class AutoTrigger(object):

    @staticmethod
    def pull_trigger(flow_type, trigger_type, flow_id, operator_id):
        flow_data = flow_data_collection.find_one({'flow_id': flow_id})
        result = None
        if flow_data:
            flow_data = flow_data.get('data')
            flow_data['flow_id'] = flow_id
            if flow_type == 'default':
                if trigger_type == 'abandon':
                    result = AutoTrigger.default_abandon(operator_id=operator_id,  **flow_data)
                elif trigger_type == 'pre_sql_before':
                    result = AutoTrigger.default_pre_sql_before(operator_id=operator_id, **flow_data)
                elif trigger_type == 'auto_local':
                    result = AutoTrigger.default_auto_local(operator_id=operator_id, **flow_data)
                elif trigger_type == 'auto_pre_build':
                    result = AutoTrigger.default_auto_pre_build(operator_id=operator_id, **flow_data)
                elif trigger_type == 'auto_pre_publish':
                    result = AutoTrigger.default_auto_pre_publish(operator_id=operator_id, **flow_data)
                elif trigger_type == 'pre_sql_after':
                    result = AutoTrigger.default_pre_sql_after(operator_id=operator_id, **flow_data)
                elif trigger_type == 'check_new':
                    result = AutoTrigger.default_check_new(operator_id=operator_id, **flow_data)
                elif trigger_type == 'prd_wait_build':
                    result = AutoTrigger.default_prd_wait_build(operator_id=operator_id, **flow_data)
                elif trigger_type == 'prd_sql_before':
                    result = AutoTrigger.default_prd_sql_before(operator_id=operator_id, **flow_data)
                elif trigger_type == 'prd_sql_after':
                    result = AutoTrigger.default_prd_sql_after(operator_id=operator_id, **flow_data)
                elif trigger_type == 'prd_complete':
                    result = AutoTrigger.default_prd_complete(operator_id=operator_id, **flow_data)
            elif flow_type == 'nopre':
                if trigger_type == 'abandon':
                    result = AutoTrigger.default_abandon(operator_id=operator_id, **flow_data)
                elif trigger_type == 'auto_local':
                    result = AutoTrigger.default_auto_local(operator_id=operator_id, **flow_data)
                elif trigger_type == 'prd_wait_build':
                    result = AutoTrigger.default_prd_wait_build(operator_id=operator_id, **flow_data)
                elif trigger_type == 'prd_sql_before':
                    result = AutoTrigger.default_prd_sql_before(operator_id=operator_id, **flow_data)
                elif trigger_type == 'prd_sql_after':
                    result = AutoTrigger.default_prd_sql_after(operator_id=operator_id, **flow_data)
                elif trigger_type == 'prd_complete':
                    result = AutoTrigger.default_prd_complete(operator_id=operator_id, **flow_data)
        return result

    @staticmethod
    def default_pre_sql_before(operator_id='system', **kwargs):
        """在SQL执行节点时进行判断，是否有需要执行的SQL，没有就跳过"""
        if kwargs.get('pre_sql_before_executed'):
            # 已经执行过SQL了直接跳过
            return 'skip'
        else:
            if kwargs.get('sql_execute_config') and kwargs.get('sql_execute_config').get('pre').get('sql_before') and kwargs.get('sql_status').get('pre') != 'init':
                return
            else:
                return 'skip'

    @staticmethod
    def default_pre_sql_after(operator_id='system', **kwargs):
        """在SQL执行节点时进行判断，是否有需要执行的SQL，没有就跳过"""
        if kwargs.get('pre_sql_after_executed'):
            # 已经执行过SQL了直接跳过
            return 'skip'
        else:
            if kwargs.get('sql_execute_config') and kwargs.get('sql_execute_config').get('pre').get('sql_after') and kwargs.get('sql_status').get('pre') != 'init':
                return
            else:
                return 'skip'

    @staticmethod
    def default_prd_sql_before(operator_id='system', **kwargs):
        """在SQL执行节点时进行判断，是否有需要执行的SQL，没有就跳过"""
        if kwargs.get('prd_sql_before_executed'):
            # 已经执行过SQL了直接跳过
            HotPoolService.set_hot_prd_app_ready(kwargs.get('flow_id'))
            return 'skip'
        else:
            if kwargs.get('sql_execute_config') and kwargs.get('sql_execute_config').get('prd').get('sql_before') and kwargs.get('sql_status').get('prd') != 'init':
                return
            else:
                return 'skip'

    @staticmethod
    def default_prd_sql_after(operator_id='system', **kwargs):
        """在SQL执行节点时进行判断，是否有需要执行的SQL，没有就跳过"""
        if kwargs.get('prd_sql_after_executed'):
            # 已经执行过SQL了直接跳过
            return 'skip'
        else:
            if kwargs.get('sql_execute_config') and kwargs.get('sql_execute_config').get('prd').get('sql_after') and kwargs.get('sql_status').get('prd') != 'init':
                return
            else:
                return 'skip'

    @staticmethod
    def default_auto_local(operator_id='system', **kwargs):
        """待预发环境自动上预发"""
        project_id = kwargs.get('project_id')
        flow_id = kwargs.get('flow_id')
        switch = publish_switch_collection.find_one({})
        if switch.get('auto_local'):
            # Record LOCAL_TO_PRE:自动待预发上预发
            ProjectRecordService.add_project_record(project_id, 'system', 'auto', 'PUBLISH', 'LOCAL_TO_PRE', None, datetime.now())
            data = KafkaService.assemble_kafka_json(project_id, 'local_to_pre', 'local', flow_id)
            KafkaService.produce(data)
            root_logger.info("kafka project_id:{} publish_id:{} action:{} at {}".format(project_id, flow_id, 'local_to_pre', datetime.now()))
            return 'local_pass'
        else:
            return

    @staticmethod
    def default_auto_pre_build(operator_id='system', **kwargs):
        """预发环境自动打包"""
        switch = publish_switch_collection.find_one({})
        if switch.get('auto_pre'):
            return 'pre_build'
        else:
            return

    @staticmethod
    def default_auto_pre_publish(operator_id='system', **kwargs):
        """预发环境自动发布"""
        switch = publish_switch_collection.find_one({})
        if switch.get('auto_pre'):
            return 'pre_publish'
        else:
            return

    @staticmethod
    def default_check_new(operator_id='system', **kwargs):
        """检查是否是新应用，新应用就进行应用监控验证"""
        project_id = kwargs.get('project_id')
        info = kwargs.get('app_info')
        if info:
            for one_app in info.values():
                if one_app.get('type') == 'app' and one_app.get('first_time'):
                    ProjectRecordService.add_project_record(project_id, 'system', 'auto', 'PUBLISH', 'NEW_APP_MONITOR', None, datetime.now())
                    return
        return "pre_pass"

    @staticmethod
    def default_abandon(operator_id='system', **kwargs):
        project_id = kwargs.get('project_id')
        flow_id = kwargs.get('flow_id')
        # Record PUBLISH_ABANDON:发布废弃
        ProjectRecordService.add_project_record(project_id, 'system', 'auto', 'PUBLISH', 'ABANDON', None, datetime.now())
        data = KafkaService.assemble_kafka_json(project_id, 'abandon', 'local', flow_id)
        KafkaService.produce(data)
        root_logger.info("kafka project_id:{} publish_id:{} action:{} at {}".format(project_id, flow_id, 'abandon', datetime.now()))
        ProjectService.reset_project(project_id)
        project = ProjectService.get_project(project_id)
        datas = dict()
        url = app.config['SERVER_URL'] + '/project/detail/' + str(project.id)
        datas['url'] = url
        datas['project_name'] = project.name
        datas['project_id'] = str(project.id)
        MessageService.publish_abandon(datas, [project.owner])
        return

    @staticmethod
    def default_prd_wait_build(operator_id='system', **kwargs):
        project_id = kwargs.get('project_id')
        flow_id = kwargs.get('flow_id')
        # Record PUBLISH_TO_PRD:发布至生产
        ProjectRecordService.add_project_record(project_id, operator_id, 'auto', 'PUBLISH', 'PRE_TO_PRD', None, datetime.now())
        data = KafkaService.assemble_kafka_json(project_id, 'pre_to_prd', 'pre', flow_id)
        data['app_info'] = AppBranchService.list_app_branch(str(project_id), ['app', 'module', 'open'])
        KafkaService.produce(data)
        root_logger.info("kafka project_id:{} publish_id:{} action:{} at {}".format(project_id, flow_id, 'pre_to_prd', datetime.now()))
        return

    @staticmethod
    def default_prd_complete(**kwargs):
        project_id = kwargs.get('project_id')
        flow_id = kwargs.get('flow_id')
        HotPoolService.stop_run_prd_app(flow_id)
        # Record PRD_COMPLETE:生产发布完成
        ProjectRecordService.add_project_record(project_id, 'system', 'auto', 'PUBLISH', 'PRD_COMPLETE', None, datetime.now())
        data = KafkaService.assemble_kafka_json(project_id, 'prd_complete', 'prd', flow_id)
        KafkaService.produce(data)
        root_logger.info("kafka project_id:{} publish_id:{} action:{} at {}".format(project_id, flow_id, 'prd_complete', datetime.now()))
        ProjectService.complete_publish_project(project_id)
        project = ProjectService.get_project(project_id)
        if project:
            JiraService.close_jira_project(project_id)
            user = project.owner
            datas = dict()
            datas['url'] = app.config.get('SERVER_URL') + '/project/detail/' + str(project_id)
            datas['project_id'] = str(project_id)
            datas['project_name'] = project.name
            to_list = {'real_name': user.real_name, 'email': user.email}
            MessageService.release_success(datas, to_list)
        return
