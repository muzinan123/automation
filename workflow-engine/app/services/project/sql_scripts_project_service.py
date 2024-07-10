# -*- coding: utf8 -*-

from datetime import datetime
from pymongo import DESCENDING

from app.out.idb import iDB
from app.services.framework.message_service import MessageService
from app.mongodb import sql_scripts_project_collection, flow_data_collection
from app import app, root_logger


class SQLScriptsProjectService(object):

    @staticmethod
    def add_sql_scripts_project(project_id, svn_project_id, env_execution_config, vcs_full_url, submited_test_version):
        try:
            sql_scripts_project_collection.insert_one({"project_id": project_id, "svn_project_id": svn_project_id, "sql_execution_config": env_execution_config, "vcs_full_url": vcs_full_url,
                                                       "submited_test_version": submited_test_version, "status": {"pre":"init", "prd": "init"}, "manual": {'pre': False, 'prd': False},  "enabled": True})
            return True, "ok"
        except Exception, e:
            root_logger.exception("add_sql_scripts_project error: %s", e)
            return False, u"sql_scripts_project添加失败"

    @staticmethod
    def mod_sql_scripts_project(project_id, publish_id=None, submited_test_version=None, sql_execution_config=None, env=None, enabled=None, manual=None):
        try:
            change = dict()
            if publish_id:
                change['publish_id'] = publish_id
            if submited_test_version:
                change["submited_test_version.{}".format(env)] = submited_test_version
            if sql_execution_config:
                change["sql_execution_config"] = sql_execution_config
            if enabled is not None:
                change["enabled"] = enabled
            if manual is not None:
                change['manual.{}'.format(env)] = manual

            sql_scripts_project_collection.update_one({"project_id": project_id}, {"$set": change})
            return True
        except Exception, e:
            root_logger.exception("mod_sql_scripts_project error: %s", e)
            return False

    @staticmethod
    def mod_sql_status(project_id, env, status, publish_id=None, review_time=None, execute_time=None, manual=None):
        try:
            change = dict()
            change["status.{}".format(env)] = status
            if review_time:
                change["review_time.{}".format(env)] = review_time
            if execute_time:
                change["execute_time.{}".format(env)] = execute_time
            if manual is not None:
                change['manual.{}'.format(env)] = manual
            sql_scripts_project_collection.update_one({"project_id": project_id}, {"$set": change})
            if publish_id:
                flow_data_collection.update_one({'flow_id': publish_id}, {'$set': {'data.sql_status.{}'.format(env): status}})
            return True
        except Exception, e:
            root_logger.exception("mod_sql_status error: %s", e)
            return False

    @staticmethod
    def del_sql_scripts_project(project_id):
        try:
            sql_scripts_project_collection.update_one({"project_id": project_id, "enabled": True}, {"$set": {"enabled": False}})
            return True
        except Exception, e:
            root_logger.exception("del_sql_scripts_project error: %s", e)
            return False

    @staticmethod
    def get_sql_scripts_project(project_id, all=False):
        if all:
            query = {"project_id": project_id}
        else:
            query = {"project_id": project_id, "enabled": True}
        try:
            result = sql_scripts_project_collection.find_one(query, {"_id": False})
            return result
        except Exception, e:
            root_logger.exception("add_sql_scripts_project error: %s", e)
            return False

    @staticmethod
    def list_sql_scripts_project(status_list):
        data = sql_scripts_project_collection.find({'$or': [{'status.pre': {'$in': status_list}}, {'status.prd': {'$in': status_list}}], "enabled": True})
        return data

    @staticmethod
    def check_sql_scripts_project_status():
        # 若提交审核时间超过15分钟，则发送邮件给DBA;
        # 若执行脚本时间超过30分钟，则发送邮件给DBA;
        try:
            now_time = datetime.now()
            project_list = sql_scripts_project_collection.find({'$or':[{"status.pre": {'$in': ['review', 'execute']}}, {"status.prd": {'$in': ['review', 'execute']}}], "enabled": True}, {"_id": False})
            publish_ids = list()
            for project in project_list:
                project_id = project.get("project_id")
                datas = dict()
                datas['project_id'] = project_id
                datas['url'] = app.config.get('SERVER_URL') + '/project/detail/' + project.get("project_id")
                for env, status in project.get("status").items():
                    if status == 'review' and (now_time-project['review_time'][env]).total_seconds() >= 900:
                        MessageService.sql_review_timeout(datas)
                    elif status == 'execute' and (now_time-project['execute_time'][env]).total_seconds() >= 1800:
                        SQLScriptsProjectService.change_to_manual(project_id, env)
                        MessageService.sql_execute_timeout(datas)
                        publish_ids.append(project.get('publish_id'))
            return True, publish_ids
        except Exception, e:
            root_logger.exception("check_sql_scripts_project_status error: %s", e)
            return False

    @staticmethod
    def change_to_manual(project_id, env):
        try:
            sql_scripts_project_collection.update_one({"project_id": project_id, "enabled": True}, {"$set": {'manual.{}'.format(env): True}})
            return True
        except Exception, e:
            root_logger.exception("mod_sql_scripts_project error: %s", e)
            return False

    @staticmethod
    def get_sql_review_detail(sql_svn_path, revision):
        return iDB.get_sql_review_detail(sql_svn_path, revision)

    @staticmethod
    def get_sql_execute_detail(sql_svn_path, revision):
        return iDB.get_sql_execute_detail(sql_svn_path, revision)

