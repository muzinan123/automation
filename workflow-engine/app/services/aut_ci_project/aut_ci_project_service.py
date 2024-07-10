# -*- coding: utf8 -*-

import re
import datetime
import hashlib
from pymongo import ASCENDING, DESCENDING
from bson.objectid import ObjectId

from app.services.operation.operation_service import OperationService
from app.services.framework.recycle_service import RecycleService
from app.mongodb import aut_ci_project_collection
from app import root_logger

class AutCiProjectService(object):

    @staticmethod
    def add_aut_ci_project(app_id, app_name, app_type, vcs_type, vcs_full_url, company, department, production,
                           branch_name, jdk_version, creator):
        try:
            result = aut_ci_project_collection.insert_one(
                {'app_id': app_id, 'app_name': app_name, 'app_type': app_type, 'vcs_type': vcs_type,
                 'vcs_full_url': vcs_full_url, 'company': company, 'department': department,
                 'production': production, 'branch': branch_name, 'jdk_version': jdk_version, 'creator': creator,
                 'create_at': datetime.datetime.utcnow(), 'build_count': 0, 'last_build_time': None, 'status': 'ready'})
            return str(result.inserted_id)
        except Exception, e:
            root_logger.exception("add_aut_ci_project error: %s", e)

    @staticmethod
    def del_aut_ci_project(project_id, delete_by):
        try:
            cp = aut_ci_project_collection.find_one({'_id': ObjectId(project_id)})
            RecycleService.recycle_mongo(cp, "aut_ci_project_collection", delete_by=delete_by)
            aut_ci_project_collection.delete_one({'_id': ObjectId(project_id)})
            return True
        except Exception, e:
            root_logger.exception("del_aut_ci_project error: %s", e)

    @staticmethod
    def mod_aut_ci_project(project_id, branch_name=None, jdk_version=None, build_count=None, last_build_time=None, status=None):
        try:
            change = dict()
            if branch_name:
                change['branch'] = branch_name
            if jdk_version:
                change['jdk_version'] = jdk_version
            if build_count:
                change['build_count'] = build_count
            if last_build_time:
                change['last_build_time'] = last_build_time
            if status:
                change['status'] = status
            aut_ci_project_collection.update_one({'_id': ObjectId(project_id)}, {'$set': change})
            return True, u'更新成功'
        except Exception, e:
            root_logger.exception("mod_ci_project error: %s", e)
        return False, u'更新失败'

    @staticmethod
    def list_aut_ci_project(query, asc=True, order_by='create_at'):
        regx = re.compile(query, re.IGNORECASE)
        pipeline = [
            {'$match': {
                '$or': [{'app_name': regx}, {'branch': regx}]
            }}
        ]
        if asc:
            pipeline.append({'$sort': {order_by: ASCENDING}})
        else:
            pipeline.append({'$sort': {order_by: DESCENDING}})
        return pipeline, aut_ci_project_collection

    @staticmethod
    def build_aut_ci_project(project_id, operator_id='system'):
        cp = aut_ci_project_collection.find_one({'_id': ObjectId(project_id)})
        if cp:
            build_count = cp.get('build_count', 0)
            aut_ci_project_collection.update_one({'_id': ObjectId(project_id)},
                                                 {'$set': {
                                                     'build_count': build_count + 1,
                                                     'last_build_time': datetime.datetime.utcnow(),
                                                     'status': 'running'
                                                 }})
            app_name = cp.get('app_name')
            flow_id = 'ci-{}'.format(project_id)
            kwargs = dict()
            kwargs['env'] = 'aut'
            kwargs['project_id'] = project_id
            kwargs['publish_id'] = flow_id
            kwargs['app_id'] = cp.get('app_id')
            if cp.get('vcs_type') == 'svn' and cp.get('branch') not in ['trunk', 'tag']:
                kwargs['branch_name'] = "branch/{}".format(cp.get('branch'))
            else:
                kwargs['branch_name'] = cp.get('branch')
            kwargs['jdk_version'] = cp.get('jdk_version')
            kwargs['vcs_type'] = cp.get('vcs_type')
            kwargs['vcs_full_url'] = cp.get('vcs_full_url')
            kwargs['company'] = cp.get('company').get('name')
            kwargs['department'] = cp.get('department').get('name')
            kwargs['creator'] = cp.get('creator')
            kwargs['app_name'] = app_name
            if cp.get('last_build_time'):
                kwargs['last_build_time'] = cp.get('last_build_time').strftime('%Y-%m-%d %H:%M:%S')
            else:
                kwargs['last_build_time'] = cp.get('create_at').strftime('%Y-%m-%d %H:%M:%S')
            kwargs['status'] = cp.get('status')
            OperationService.run_operation.delay('aut_ci_build', 'jenkins', app_name, operator_id, _flow_id=flow_id, **kwargs)
            return True
