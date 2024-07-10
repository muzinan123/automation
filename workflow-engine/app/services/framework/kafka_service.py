# -*- coding:utf8 -*-

import re
import json
import datetime
from bson.objectid import ObjectId
from pymongo import DESCENDING, ASCENDING

from app.mongodb import message_collection, app_branch_collection
from app.models.Project import Project
from app.services.project.sql_scripts_project_service import SQLScriptsProjectService
from app.kafka import Kafka
from app import app, celery, root_logger
from app.services.framework.user_service import UserService


class KafkaService(object):

    @staticmethod
    def produce(data):
        try:
            if app.config.get('SEND_KAFKA_MSG'):
                result = Kafka.produce(data)
                message = dict(data=json.dumps(data), data_type=type(data).__name__, produce_at=datetime.datetime.utcnow(),
                               retry=0, partition_id=result.partition_id, offset=result.offset)
                message_collection.insert_one(message)
                return True
        except Exception, e:
            root_logger.exception("produce error: %s", e)

    @staticmethod
    def reproduce(message_id):
        try:
            if app.config.get('SEND_KAFKA_MSG'):
                message = message_collection.find_one({'_id': ObjectId(message_id)})
                data = json.loads(message.get('data'))
                Kafka.produce(data)
                message_collection.update_one({'_id': ObjectId(message_id)}, {'$inc': {'retry': 1}})
                return True
        except Exception, e:
            root_logger.exception("reproduce error: %s", e)

    @staticmethod
    def list_message(query, data_type=None, order_by='produce_at', order_desc=None):
        regx = re.compile(query, re.IGNORECASE)
        pipeline = [
            {'$match': {
                '$or': [
                    {'data': regx}
                ]
            }}
        ]
        if data_type:
            pipeline.append({'$match': {'data_type': data_type}})
        if order_desc:
            pipeline.append({'$sort': {order_by: DESCENDING}})
        else:
            pipeline.append({'$sort': {order_by: ASCENDING}})
        return pipeline, message_collection

    @staticmethod
    def get_kafka_info():
        ret = dict()
        try:
            main_partition_info = Kafka.get_partition_info()
            main = list()
            for k, v in main_partition_info.items():
                main.append({'id': k, 'latest_available_offset': v.latest_available_offset(),
                             'earliest_available_offset': v.earliest_available_offset(),
                             'leader': '{}:{}'.format(v.leader.host, v.leader.port),
                             'replicas': ['{}:{}'.format(r.host, r.port) for r in v.replicas]})
            ret['main_partition'] = main
        except Exception, e:
            root_logger.exception("get_consumer_info error: %s", e)
        return ret

    @staticmethod
    def assemble_kafka_json(project_id, action, env, publish_id):
        # 组装kafka json
        data = dict()
        project = Project.query.get(project_id)
        if project:
            data['action'] = action
            data['project_id'] = project_id
            project_detail = project.serialize()
            data['creator'] = project_detail.get('owner')
            data['testers'] = project_detail.get('qa_list')
            status = project_detail.get('test_status')
            if status == 0:
                test_status = u'待提交'
            elif status == 1:
                test_status = u'测试中'
            elif status == 2:
                test_status = u'测试通过'
            else:
                test_status = u'状态错误'
            data['status'] = test_status
            data['begin_date'] = project_detail.get('begin_date')
            data['publish_date'] = project_detail.get('expect_publish_date')
            sql_scripts_project = SQLScriptsProjectService.get_sql_scripts_project(project_id)
            if sql_scripts_project:
                data['sql_script_url'] = sql_scripts_project.get('vcs_full_url')
            else:
                data['sql_script_url'] = ''
            participants = dict()
            participants['dev_list'] = project_detail.get('dev_list')
            participants['ba'] = project_detail.get('ba')
            participants['code_review_list'] = project_detail.get('code_review_list')
            participants['owner'] = project_detail.get('owner')
            participants['test_list'] = project_detail.get('qa_list')
            data['participants'] = participants
            data['company'] = project_detail.get('company_label')
            data['department'] = project_detail.get('dept_label')
            app_list = list()
            packages = dict()
            codes = dict()
            for one_app in app_branch_collection.find({"project_id": project_id, "enabled": True}, {"_id": False}):
                app_list.append(one_app.get('app_name'))
                if publish_id and one_app.get('app_id') in app.config['AUT_APP_ID_LIST']:
                    packages[one_app.get('app_name')] = "{}/release/app/{}/aut/{}/".format(app.config['PACKAGE_URL'], one_app.get('app_id'), publish_id)
                codes[one_app.get('app_name')] = "{}/branch/{}".format(one_app.get('vcs_full_url'), one_app.get('branch'))
            data['packages'] = packages
            data['code'] = codes
            data['apps'] = app_list
        return data

    @staticmethod
    def assemble_aut_kafka_json(project_id, publish_id, **kwargs):
        creator = UserService.get_user(kwargs.get('creator'))
        # 组装kafka json
        data = dict()
        data['action'] = "packaging_test"
        data['project_id'] = project_id
        data['company'] = kwargs.get('company')
        data['department'] = kwargs.get('department')
        data['last_build_time'] = kwargs.get('last_build_time')
        # data['begin_date'] = kwargs.get('create_at')
        creator = {'email': creator.email, 'real_name': creator.real_name, 'id': creator.id, 'name': creator.name}
        data['creator'] = creator
        data['status'] = kwargs.get('status')
        data['apps'] = [kwargs.get('app_name')]
        packages = dict()
        packages[kwargs.get('app_name')] = "{}/release/app/{}/aut/{}/".format(app.config['PACKAGE_URL'],
                                                                              kwargs.get('app_id'),
                                                                               publish_id)
        data['packages'] = packages
        return data

    @staticmethod
    def assemble_jira_sync_duang_kafka_json(project_id, project_name, jira_issue_id=None, jira_issue_key=None, jira_version_id=None, regulator_id=None):
        # 组装kafka json
        data = dict()
        data['project_id'] = project_id
        data['project_name'] = project_name
        data['action'] = "jira_sync_duang"
        project = Project.query.get(project_id)
        if project:
            project_detail = project.serialize()
            data['creator'] = project_detail.get('owner')
            data['testers'] = project_detail.get('qa_list')
            data['status'] = project_detail.get('test_status')
            data['begin_date'] = project_detail.get('begin_date')
            data['publish_date'] = project_detail.get('expect_publish_date')
            data['sql_script_url'] = project_detail.get('sql_script_url')
            participants = dict()
            participants['dev_list'] = project_detail.get('dev_list')
            participants['ba'] = project_detail.get('ba')
            participants['code_review_list'] = project_detail.get('code_review_list')
            participants['owner'] = project_detail.get('owner')
            participants['test_list'] = project_detail.get('qa_list')
            data['participants'] = participants
            data['company'] = project_detail.get('company_label')
            data['department'] = project_detail.get('dept_label')
            if jira_issue_id and jira_issue_key:
                data['jira_issue_id'] = jira_issue_id
                data['jira_issue_key'] = jira_issue_key
                data['jira_url'] = "{}/browse/{}".format(app.config['JIRA_SERVER_URL'], jira_issue_key)
            elif jira_version_id:
                data['jira_version_id'] = jira_version_id
                data['jira_url'] = "{}/projects/{}/versions/{}".format(app.config['JIRA_SERVER_URL'], project_detail.get('jira_project_key'), jira_version_id)
            elif regulator_id:
                data['regulator_id'] = regulator_id
        return data