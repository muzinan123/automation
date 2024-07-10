# -*- coding:utf-8 -*-

from datetime import datetime

from app.services.publish.hot_pool_service import HotPoolService
from app.services.project.sql_scripts_project_service import SQLScriptsProjectService
from app.services.project.project_record_service import ProjectRecordService
from app.services.framework.user_service import UserService
from app.mongodb import flow_data_collection
from app import root_logger


class GoAction(object):

    @staticmethod
    def run(flow_type, action, flow_id, operator_id):
        result = None
        flow_data = flow_data_collection.find_one({'flow_id': flow_id}, {"_id": False})
        if flow_data:
            flow_data = flow_data.get('data')
            if flow_type == 'default':
                if action == 'pre_sql':
                    result = GoAction.pre_sql(**flow_data)
                if action == 'prd_sql':
                    result = GoAction.prd_sql(**flow_data)
                if action == 'pre_sql_before_executed':
                    result = GoAction.pre_sql_before_executed(flow_id, operator_id=operator_id, **flow_data)
                elif action == 'pre_sql_after_executed':
                    result = GoAction.pre_sql_after_executed(flow_id, operator_id=operator_id, **flow_data)
                elif action == 'prd_sql_before_executed':
                    result = GoAction.prd_sql_before_executed(flow_id, operator_id=operator_id, **flow_data)
                elif action == 'prd_sql_after_executed':
                    result = GoAction.prd_sql_after_executed(flow_id, operator_id=operator_id, **flow_data)
                elif action == 'prd_build':
                    result = GoAction.prd_build(flow_id, operator_id=operator_id, **flow_data)
                elif action == 'pre_pass':
                    # 点击发布至生产触发该行为
                    result = GoAction.pre_pass(flow_id, operator_id=operator_id, **flow_data)
                elif action == 'pre_not_pass':
                    # 验证回退 只有pre环境才存在验证回退，生产环境不存在
                    result = GoAction.pre_not_pass(flow_id, operator_id=operator_id, **flow_data)
                elif action == 'pre_roll_back':
                    result = GoAction.pre_roll_back(flow_id, operator_id=operator_id, **flow_data)
                elif action == 'local_not_pass':
                    # owner回退
                    result = GoAction.local_not_pass(flow_id, operator_id=operator_id, **flow_data)
                elif action == 'prd_rebuild':
                    # 生产重新打包
                    result = GoAction.prd_rebuild(flow_id, operator_id=operator_id, **flow_data)
            elif flow_type == 'nopre':
                if action == 'prd_sql_before_executed':
                    result = GoAction.prd_sql_before_executed(flow_id, operator_id=operator_id, **flow_data)
                elif action == 'local_not_pass':
                    # owner回退
                    result = GoAction.local_not_pass(flow_id, operator_id=operator_id, **flow_data)
                elif action == 'prd_sql_after_executed':
                    result = GoAction.prd_sql_after_executed(flow_id, operator_id=operator_id, **flow_data)
                elif action == 'prd_build':
                    result = GoAction.prd_build(flow_id, operator_id=operator_id, **flow_data)
                elif action == 'prd_rebuild':
                    # 生产重新打包
                    result = GoAction.prd_rebuild(flow_id, operator_id=operator_id, **flow_data)
            return result

    @staticmethod
    def pre_sql(**kwargs):
        project = SQLScriptsProjectService.get_sql_scripts_project(kwargs.get('project_id'))
        if project.get('status').get('pre') == 'pass' and not project.get('manual').get('pre'):
            return True

    @staticmethod
    def prd_sql(**kwargs):
        project = SQLScriptsProjectService.get_sql_scripts_project(kwargs.get('project_id'))
        if project.get('status').get('prd') == 'pass' and not project.get('manual').get('prd'):
            return True


    @staticmethod
    def pre_sql_before_executed(flow_id, operator_id='system', **kwargs):
        try:
            project_id = kwargs.get('project_id')
            flow_data_collection.update_one({'flow_id': flow_id, 'data.sql_execute_config.pre.sql_before': True},
                                            {'$set': {'data.pre_sql_before_executed': True}})
            SQLScriptsProjectService.mod_sql_status(project_id, 'pre', 'success', publish_id=flow_id)
            ProjectRecordService.add_project_record(project_id, operator_id, 'dba', 'PUBLISH', 'PRE_SQL_BEFORE_EXECUTED', None, datetime.now())
            return True
        except Exception, e:
            root_logger.exception("pre_sql_before_executed error: %s", e)

    @staticmethod
    def pre_sql_after_executed(flow_id, operator_id='system', **kwargs):
        try:
            project_id = kwargs.get('project_id')
            flow_data_collection.update_one({'flow_id': flow_id, 'data.sql_execute_config.pre.sql_after': True},
                                            {'$set': {'data.pre_sql_after_executed': True}})
            SQLScriptsProjectService.mod_sql_status(project_id, 'pre', 'success', publish_id=flow_id)
            ProjectRecordService.add_project_record(project_id, operator_id, 'dba', 'PUBLISH', 'PRE_SQL_AFTER_EXECUTED', None, datetime.now())
            return True
        except Exception, e:
            root_logger.exception("pre_sql_after_executed error: %s", e)

    @staticmethod
    def prd_sql_before_executed(flow_id, operator_id='system', **kwargs):
        try:
            project_id = kwargs.get('project_id')
            flow_data_collection.update_one({'flow_id': flow_id, 'data.sql_execute_config.prd.sql_before': True},
                                            {'$set': {'data.prd_sql_before_executed': True}})
            SQLScriptsProjectService.mod_sql_status(project_id, 'prd', 'success', publish_id=flow_id)
            HotPoolService.set_hot_prd_app_ready(flow_id)
            ProjectRecordService.add_project_record(project_id, operator_id, 'dba', 'PUBLISH', 'PRD_SQL_BEFORE_EXECUTED', None, datetime.now())
            return True
        except Exception, e:
            root_logger.exception("prd_sql_before_executed error: %s", e)

    @staticmethod
    def prd_sql_after_executed(flow_id, operator_id='system', **kwargs):
        try:
            project_id = kwargs.get('project_id')
            flow_data_collection.update_one({'flow_id': flow_id, 'data.sql_execute_config.prd.sql_after': True},
                                            {'$set': {'data.prd_sql_after_executed': True}})
            SQLScriptsProjectService.mod_sql_status(project_id, 'prd', 'success', publish_id=flow_id)
            ProjectRecordService.add_project_record(project_id, operator_id, 'dba', 'PUBLISH', 'PRD_SQL_AFTER_EXECUTED',None, datetime.now())
            return True
        except Exception, e:
            root_logger.exception("prd_sql_after_executed error: %s", e)

    @staticmethod
    def prd_build(flow_id, operator_id='system', **kwargs):
        try:
            HotPoolService.start_run_prd_app(flow_id)
            return True
        except Exception, e:
            root_logger.exception("prd_build error: %s", e)

    @staticmethod
    def pre_not_pass(flow_id, operator_id='system', **kwargs):
        project_id = kwargs.get('project_id')
        reason_code = kwargs.get('pre_not_pass_reason')
        pre_not_pass_comment = kwargs.get("pre_not_pass_comment")
        bad_man = kwargs.get('bad_man')
        reason = ProjectRecordService.get_reason_name(reason_code)
        remark = u"预发验证回退: <span>" + reason + u"</span>"
        remark += u"<div>退回原因: {}</div>".format(pre_not_pass_comment)
        if bad_man:
            remark += u"<div>责任人: <a class='am-badge am-badge-danger' onclick='change_bad_man(this, \"{}\", \"{}\", \"{}\", \"{}\")'>{}</a></div>".format(
                flow_id, operator_id, reason, 'pre_not_pass', bad_man)
        result = ProjectRecordService.add_project_record(project_id, operator_id, '', 'PUBLISH', 'PRE_NOT_PASS', remark, datetime.now())
        return result

    @staticmethod
    def local_not_pass(flow_id, operator_id='system', **kwargs):
        project_id = kwargs.get('project_id')
        reason_code = kwargs.get('owner_rollback_reason')
        owner_rollback_comment = kwargs.get("owner_rollback_comment")
        bad_man = kwargs.get('bad_man')
        reason = ProjectRecordService.get_reason_name(reason_code)
        remark = u"项目owner自主回退: <span>" + reason + u"</span>"
        remark += u"<div>退回原因: {}</div>".format(owner_rollback_comment)
        if bad_man:
            remark += u"<div>责任人: <a class='am-badge am-badge-danger' onclick='change_bad_man(this, \"{}\", \"{}\", \"{}\", \"{}\")'>{}</a></div>".format(
                flow_id, operator_id, reason, 'local_not_pass', bad_man)
        result = ProjectRecordService.add_project_record(project_id, operator_id, 'owner', 'PUBLISH', 'LOCAL_NOT_PASS', remark, datetime.now())
        return result

    @staticmethod
    def pre_roll_back(flow_id, operator_id='system', **kwargs):
        project_id = kwargs.get('project_id')
        result = ProjectRecordService.add_project_record(project_id, operator_id, '', 'PUBLISH', 'PRE_ROLL_BACK', None, datetime.now())
        return result

    @staticmethod
    def pre_pass(flow_id, operator_id='system', **kwargs):
        project_id = kwargs.get('project_id')
        result = ProjectRecordService.add_project_record(project_id, operator_id, 'qa', 'PUBLISH', 'PRE_PASS', None, datetime.now())
        operator = UserService.get_user(operator_id)
        flow_data_collection.update_one({'flow_id': flow_id}, {'$set': {'data.qa': operator.real_name}})
        return result

    @staticmethod
    def prd_rebuild(flow_id, operator_id='system', **kwargs):
        HotPoolService.stop_run_prd_app(flow_id)
        return True