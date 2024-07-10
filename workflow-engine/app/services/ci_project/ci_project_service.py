# -*- coding: utf8 -*-

import re
import datetime
import hashlib
from pymongo import ASCENDING, DESCENDING

from app.services.operation.operation_service import OperationService
from app.services.apprepo_service import ApprepoService
from app.services.framework.recycle_service import RecycleService
from app.mongodb import ci_project_collection
from app import root_logger


class CiProjectService(object):

    @staticmethod
    def add_ci_project(app_id, app_name, vcs_type, vcs_full_url, company, department, production, branch_name, jdk_version, creator):
        try:
            pom_info = ApprepoService.get_info_from_pom(app_id, branch_name=branch_name)
            if pom_info:
                version = pom_info.get('version')
                if len(version) < 9 or version[-9:] != '-SNAPSHOT':
                    return False, u'创建项目失败，非SNAPSHOT版本'
                ci_project_collection.insert_one({'app_id': app_id, 'app_name': app_name, 'vcs_type': vcs_type,
                                                  'vcs_full_url': vcs_full_url, 'company': company, 'department': department,
                                                  'production': production, 'branch': branch_name, 'version': version,
                                                  'jdk_version': jdk_version, 'creator': creator,
                                                  'create_at': datetime.datetime.utcnow(), 'build_count': 0,
                                                  'last_build_time': None, 'status': 'ready'})
                return True, u'创建成功'
        except Exception, e:
            root_logger.exception("add_ci_project error: %s", e)
        return False, u'创建失败，请检查相同应用相同分支是否已经创建过持续集成项目'

    @staticmethod
    def del_ci_project(app_id, branch_name, delete_by):
        try:
            cp = ci_project_collection.find_one({'app_id': app_id, 'branch': branch_name})
            RecycleService.recycle_mongo(cp, "ci_project_collection", delete_by=delete_by)
            ci_project_collection.delete_one({'app_id': app_id, 'branch': branch_name})
            return True
        except Exception, e:
            root_logger.exception("del_ci_project error: %s", e)

    @staticmethod
    def mod_ci_project(app_id, branch_name, jdk_version=None, new_branch_name=None, build_count=None,
                       last_build_time=None, status=None):
        try:
            change = dict()
            if jdk_version:
                change['jdk_version'] = jdk_version
            if new_branch_name:
                change['branch'] = new_branch_name
                pom_info = ApprepoService.get_info_from_pom(app_id, branch_name=new_branch_name)
                if pom_info:
                    version = pom_info.get('version')
                    if len(version) < 9 or version[-9:] != '-SNAPSHOT':
                        return False, u'修改项目失败，非SNAPSHOT版本'
                    change['version'] = version
            if build_count:
                change['build_count'] = build_count
            if last_build_time:
                change['last_build_time'] = last_build_time
            if status:
                change['status'] = status
            ci_project_collection.update_one({'app_id': app_id, 'branch': branch_name}, {'$set': change})
            return True, u'修改成功'
        except Exception, e:
            root_logger.exception("mod_ci_project error: %s", e)
        return False, u'修改失败，请检查相同应用相同分支是否已经创建过持续集成项目'

    @staticmethod
    def get_ci_project(app_id, branch_name):
        return ci_project_collection.find_one({'app_id': app_id, 'branch': branch_name}, {'_id': False})

    @staticmethod
    def list_ci_project(query, asc=True, order_by='create_at'):
        regx = re.compile(query, re.IGNORECASE)
        pipeline = [
            {'$project': {
                '_id': False,
            }},
            {'$match': {
                '$or': [{'app_name': regx}, {'branch': regx}, {'version': regx}]
            }}
        ]
        if asc:
            pipeline.append({'$sort': {order_by: ASCENDING}})
        else:
            pipeline.append({'$sort': {order_by: DESCENDING}})
        return pipeline, ci_project_collection

    @staticmethod
    def build_ci_project(app_id, branch_name, operator_id='system'):
        cp = ci_project_collection.find_one({'app_id': app_id, 'branch': branch_name})
        if cp:
            build_count = cp.get('build_count', 0)
            ci_project_collection.update_one({'app_id': app_id, 'branch': branch_name},
                                             {'$set': {
                                                 'build_count': build_count+1,
                                                 'last_build_time': datetime.datetime.utcnow(),
                                                 'status': 'running'
                                             }})
            app_name = cp.get('app_name')
            kwargs = dict()
            kwargs['env'] = 'pre'
            kwargs['app_id'] = app_id
            kwargs['app_name'] = app_name
            kwargs['branch_name'] = cp.get('branch')
            kwargs['jdk_version'] = cp.get('jdk_version')
            kwargs['vcs_type'] = cp.get('vcs_type')
            kwargs['vcs_full_url'] = cp.get('vcs_full_url')
            flow_id = 'ci-' + hashlib.md5("{}-{}".format(app_id, branch_name)).hexdigest()
            OperationService.run_operation.delay('ci_build', 'jenkins', app_name, operator_id, _flow_id=flow_id, **kwargs)
            return True
