# -*- coding:utf-8 -*-

import datetime

from app.mongodb import antx_base_collection, antx_project_collection
from app import root_logger


class AntxService(object):

    @staticmethod
    def query_base_antx(env, app_id):
        base_antx = antx_base_collection.find_one({"env": env, "app_id": app_id})
        content = []
        if base_antx:
            content = base_antx.get('content')
        return content

    @staticmethod
    def create_project_antx(project_id, app_env_list):
        error_msg = list()
        for one in app_env_list:
            app_id = one.get('app_id')
            app_name = one.get('app_name')
            for env in one.get('env_list'):
                try:
                    content = AntxService.query_base_antx(env, int(app_id))
                    antx_project_collection.insert_one({'project_id': project_id, 'app_id': int(app_id), 'env': env,
                                                        'app_name': app_name, 'content': content, 'base_content': content,
                                                        'review_status': 'init'})
                except Exception, e:
                    root_logger.exception("create_project_antx error: %s", e)
                    error_msg.append(u'{}应用的{}环境的Antx配置添加失败'.format(app_name, env))
        if len(error_msg):
            return False, error_msg
        else:
            return True, ['ok']

    @staticmethod
    def delete_project_antx(project_id, app_id, env):
        try:
            result = antx_project_collection.delete_one({"project_id": project_id, "app_id": app_id, "env": env})
            if result.deleted_count == 1:
                return True
        except Exception, e:
            root_logger.exception("delete_project_antx error: %s", e)
        return False

    @staticmethod
    def mod_project_antx(project_id, app_id, env, content=None, review_status=None):
        try:
            change = dict()
            if content is not None:
                change['content'] = content
            if review_status is not None:
                change['review_status'] = review_status
            result = antx_project_collection.update_one({"project_id": project_id, "app_id": app_id, "env": env}, {"$set": change})
            return True
        except Exception, e:
            root_logger.exception("mod_project_antx error: %s", e)

    @staticmethod
    def list_project_antx(project_id):
        records = antx_project_collection.find({"project_id": project_id}, {'_id': False, 'content': False, 'base_content': False})
        return [e for e in records]

    @staticmethod
    def get_project_antx(project_id, app_id, env):
        record = antx_project_collection.find_one({"project_id": project_id, "app_id": app_id, "env": env}, {"_id": False})
        return record

    @staticmethod
    def try_merge_project_prd_antx(source_project_id, target_project_id, app_id):
        # 预检查，预发上到生产时执行，如果包含相同应用，将应用老版本的antx(source_project)合并和新版本的antx(target_project)中去
        source_project_antx = antx_project_collection.find_one({'project_id': source_project_id, 'env': 'prd', 'app_id': app_id})
        target_project_antx = antx_project_collection.find_one({'project_id': target_project_id, 'env': 'prd', 'app_id': app_id})
        if source_project_antx:
            if target_project_antx:
                # 合并
                source_content = source_project_antx.get('content')
                target_content = target_project_antx.get('content')
                same_key_list = set([e.get('k') for e in source_content]) & set([e.get('k') for e in target_content])
                source_dict = {e.get('k'): e.get('v') for e in source_content}
                target_dict = {e.get('k'): e.get('v') for e in target_content}
                error_key_list = list()
                for k in same_key_list:
                    a = source_dict.get(k)
                    b = target_dict.get(k)
                    if a != b:
                        error_key_list.append(k)
                if error_key_list:
                    return False, error_key_list
        return True, list()

    @staticmethod
    def merge_project_prd_antx(source_project_id, target_project_id, app_id):
        # 预发上到生产时执行，如果包含相同应用，将应用老版本的antx(source_project)合并和新版本的antx(target_project)中去
        source_project_antx = antx_project_collection.find_one(
            {'project_id': source_project_id, 'env': 'prd', 'app_id': app_id})
        target_project_antx = antx_project_collection.find_one(
            {'project_id': target_project_id, 'env': 'prd', 'app_id': app_id})
        if source_project_antx:
            if target_project_antx:
                # 合并
                source_content = source_project_antx.get('content')
                target_content = target_project_antx.get('content')
                diff_key_list = (set([e.get('k') for e in source_content]) - set(
                    [e.get('k') for e in target_content])) | (
                                set([e.get('k') for e in target_content]) - set([e.get('k') for e in source_content]))
                same_key_list = set([e.get('k') for e in source_content]) & set([e.get('k') for e in target_content])
                source_dict = {e.get('k'): e.get('v') for e in source_content}
                target_dict = {e.get('k'): e.get('v') for e in target_content}
                merge_dict = dict()
                for k in same_key_list:
                    merge_dict[k] = source_dict.get(k)
                for k in diff_key_list:
                    merge_dict[k] = source_dict.get(k) if source_dict.get(k) else target_dict.get(k)
                merge_content = [{'k': e[0], 'v': e[1]} for e in merge_dict.items()]
                AntxService.mod_project_antx(target_project_id, app_id, 'prd', merge_content)
            else:
                # 新版本不包含antx，创建antx，直接复制老版本的antx
                project_id = source_project_antx.get('project_id')
                app_id = source_project_antx.get('app_id')
                env = source_project_antx.get('env')
                app_name = source_project_antx.get('app_name')
                app_env_list = list()
                app_env_list.append({'app_id': app_id, 'app_name': app_name, 'env_list': [env]})
                AntxService.create_project_antx(project_id, app_env_list)
        return True

    @staticmethod
    def commit_project_antx(project_id, env):
        project_antx_list = antx_project_collection.find({'project_id': project_id, 'env': env})
        for project_antx in project_antx_list:
            app_id = project_antx.get('app_id')
            change = dict()
            change['app_id'] = app_id
            change['env'] = env
            change['content'] = project_antx.get('content')
            change['app_name'] = project_antx.get('app_name')
            change['modified_at'] = datetime.datetime.utcnow()
            antx_base_collection.update_one({'app_id': app_id, 'env': env}, {"$set": change}, upsert=True)

    @staticmethod
    def update_base_antx(env, app_id, name, content):
        data = list()
        for line in content.split("\n"):
            if line:
                record = dict()
                k = line.split("=", 1)[0].strip()
                v = line.split("=", 1)[1].strip()
                record['k'] = k
                record['v'] = v
                data.append(record)
            else:
                continue
        change = dict()
        change['app_name'] = name
        change['content'] = data
        change['modified_at'] = datetime.datetime.utcnow()
        antx_base_collection.update_one({"app_id": app_id, "env": env}, {"$set": change}, upsert=True)
