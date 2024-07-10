# -*- coding:utf8 -*-

import requests

from app import app, idb_logger


class iDB(object):

    @staticmethod
    def apply_sql_review(project_id, project_owner, project_dept, env, sql_svn_path, revision):
        try:
            url = "{}/api/publish/sqlReviewApply".format(app.config['IDB_URL'])
            token = app.config['IDB_TOKEN']
            data = dict()
            data['publishSystem'] = 'duang'
            data['publishSystemNo'] = project_id
            data['publishOwner'] = project_owner
            data['publishOwnerDept'] = project_dept
            data['publishEnv'] = env
            data['sqlRepositoryType'] = 'svn'
            data['sqlRepositoryPath'] = sql_svn_path
            data['sqlRepositoryRevision'] = revision
            data['token'] = token
            idb_logger.info(url)
            idb_logger.info(data)
            response = requests.post(url, json=data, timeout=15)
            idb_logger.info(response.content)
            if response.status_code == 200 and response.json().get('errorCode') == 200:
                return True, "success"
            else:
                return False, response.json().get('errorMsg')
        except Exception, e:
            idb_logger.exception("apply_sql_review error: %s", e)

    @staticmethod
    def execute_sql(project_id, env, sql_svn_path, revision):
        try:
            url = "{}/api/publish/sqlExecuteApply".format(app.config['IDB_URL'])
            token = app.config['IDB_TOKEN']
            data = dict()
            data['publishSystem'] = 'duang'
            data['publishSystemNo'] = project_id
            data['publishEnv'] = env
            data['sqlRepositoryType'] = 'svn'
            data['sqlRepositoryPath'] = sql_svn_path
            data['sqlRepositoryRevision'] = revision
            data['token'] = token
            idb_logger.info(url)
            idb_logger.info(data)
            response = requests.post(url, json=data, timeout=15)
            idb_logger.info(response.content)
            if response.status_code == 200 and response.json().get('errorCode') == 200:
                return True, "success"
            else:
                return False, response.json().get('errorMsg')
        except Exception, e:
            idb_logger.exception("execute_sql error: %s", e)

    @staticmethod
    def get_sql_review_detail(sql_svn_path, revision):
        try:
            url = "{}/api/publish/sqlReviewDetail".format(app.config['IDB_URL'])
            token = app.config['IDB_TOKEN']
            data = dict()
            data['sqlRepositoryType'] = 'svn'
            data['sqlRepositoryPath'] = sql_svn_path
            data['sqlRepositoryRevision'] = revision
            data['token'] = token
            idb_logger.info(url)
            idb_logger.info(data)
            response = requests.post(url, json=data, timeout=15)
            idb_logger.info(response.content)
            if response.status_code == 200 and response.json().get('errorCode') == 200:
                result = response.json()
                return True, result.get('data').get('sql_review_detail')
            else:
                return False, response.json().get('errorMsg')
        except Exception, e:
            idb_logger.exception("get_sql_review_detail error: %s", e)

    @staticmethod
    def get_sql_execute_detail(sql_svn_path, revision):
        try:
            url = "{}/api/publish/sqlExecuteDetail".format(app.config['IDB_URL'])
            token = app.config['IDB_TOKEN']
            data = dict()
            data['sqlRepositoryType'] = 'svn'
            data['sqlRepositoryPath'] = sql_svn_path
            data['sqlRepositoryRevision'] = revision
            data['token'] = token
            idb_logger.info(url)
            idb_logger.info(data)
            response = requests.post(url, json=data, timeout=15)
            idb_logger.info(response.content)
            if response.status_code == 200 and response.json().get('errorCode') == 200:
                result = response.json()
                return result.get('data').get('sql_execute_detail')
            else:
                return response.json().get('errorMsg')
        except Exception, e:
            idb_logger.exception("get_sql_execute_detail error: %s", e)