# -*- coding: utf8 -*-

import requests

from app import app, apprepo_logger


class Apprepo(object):

    @staticmethod
    def get_app_info(app_id):
        try:
            url = "{}/api/app/project/{}/info".format(app.config['APPREPO_URL'], app_id)
            response = requests.get(url, headers={'api': app.config['APPREPO_TOKEN']})
            if response.status_code == 200:
                return response.json().get('data')
        except Exception, e:
            apprepo_logger.exception("get_app_info error: %s", e)

    @staticmethod
    def get_app_list(query):
        try:
            data = {"query": query}
            url = "{}/api/app/project/all/list".format(app.config['APPREPO_URL'])
            response = requests.get(url, headers={'api': app.config['APPREPO_TOKEN']}, data=data)
            if response.status_code == 200:
                return response.json().get('data')
        except Exception, e:
            apprepo_logger.exception("get_app_list error: %s", e)

    @staticmethod
    def list_branch(app_id, directory='branch'):
        try:
            url = "{}/api/app/project/{}/branch/list".format(app.config['APPREPO_URL'], app_id)
            data = {'directory': directory}
            apprepo_logger.info("url: {}".format(url))
            apprepo_logger.info("data: {}".format(data))
            response = requests.get(url, params=data, headers={'api': app.config['APPREPO_TOKEN']})
            apprepo_logger.debug("response: {}".format(response.content))
            if response.status_code == 200:
                return response.json().get('data')
        except Exception, e:
            apprepo_logger.exception("list_branch error: %s", e)

    @staticmethod
    def delete_branch(app_id, branch_name, directory='release'):
        try:
            url = "{}/api/app/project/{}/branch/delete".format(app.config['APPREPO_URL'], app_id)
            data = {'branch_name': branch_name, 'directory': directory}
            apprepo_logger.info("url: {}".format(url))
            apprepo_logger.info("data: {}".format(data))
            response = requests.post(url, data=data, headers={'api': app.config['APPREPO_TOKEN']})
            apprepo_logger.info("response: {}".format(response.content))
            if response.status_code == 200:
                return response.json()
        except Exception, e:
            apprepo_logger.exception("create_branch error: %s", e)

    @staticmethod
    def create_branch(app_id, branch_name, directory='branch', source=None):
        try:
            url = "{}/api/app/project/{}/branch/create".format(app.config['APPREPO_URL'], app_id)
            data = {'branch_name': branch_name, 'directory': directory, 'source': source}
            apprepo_logger.info("url: {}".format(url))
            apprepo_logger.info("data: {}".format(data))
            response = requests.post(url, data=data, headers={'api': app.config['APPREPO_TOKEN']})
            apprepo_logger.info("response: {}".format(response.content))
            if response.status_code == 200:
                return response.json()
        except Exception, e:
            apprepo_logger.exception("create_branch error: %s", e)

    @staticmethod
    def get_current_revision_or_commit(app_id, svn_relative_path=None, git_branch_name=None):
        try:
            url = "{}/api/app/project/{}/current_revision_or_commit".format(app.config['APPREPO_URL'], app_id)
            data = {'relative_path': svn_relative_path, 'branch_name': git_branch_name}
            apprepo_logger.info("url: {}".format(url))
            apprepo_logger.info("data: {}".format(data))
            response = requests.post(url, data=data, headers={'api': app.config['APPREPO_TOKEN']})
            apprepo_logger.info("response: {}".format(response.content))
            if response.status_code == 200:
                if response.json().get('result') == 1:
                    return response.json().get('data')
        except Exception, e:
            apprepo_logger.exception("get_current_revision_or_commit error: %s", e)

    @staticmethod
    def merge(app_id, source, target, svn_revision=None, git_commit_hash=None, commit=False, update_pom=False,
              duang_project_id=None, update_parent_version=True, update_self_version=False, exclude_list=None, accept=None):
        try:
            commit_str = "true" if commit else "false"
            update_pom_str = "true" if update_pom else "false"
            update_parent_version_str = "true" if update_parent_version else "false"
            update_self_version_str = "true" if update_self_version else "false"

            url = "{}/api/app/project/{}/merge".format(app.config['APPREPO_URL'], app_id)
            data = {'source': source, 'target': target, 'revision': svn_revision, 'commit_hash': git_commit_hash,
                    'commit': commit_str, 'update_pom': update_pom_str, 'duang_project_id': duang_project_id,
                    'update_parent_version': update_parent_version_str, 'update_self_version': update_self_version_str,
                    'accept': accept
                    }
            apprepo_logger.info("url: {}".format(url))
            apprepo_logger.info("data: {}".format(data))
            response = requests.post(url, data=data, headers={'api': app.config['APPREPO_TOKEN']})
            apprepo_logger.info("response: {}".format(response.content))
            if response.status_code == 200:
                return response.json()
        except Exception, e:
            apprepo_logger.exception("create_branch error: %s", e)

    @staticmethod
    def get_info_from_pom(app_id, relative_path=None, branch_name=None, svn_revision=None, git_commit_hash=None):
        try:
            url = "{}/api/app/project/{}/get_info_from_pom".format(app.config['APPREPO_URL'], app_id)
            data = {'relative_path': relative_path, 'branch_name': branch_name, 'svn_revision': svn_revision, 'git_commit_hash': git_commit_hash}
            apprepo_logger.info("url: {}".format(url))
            apprepo_logger.info("data: {}".format(data))
            response = requests.post(url, data=data, headers={'api': app.config['APPREPO_TOKEN']})
            apprepo_logger.info("response: {}".format(response.content))
            if response.status_code == 200:
                return response.json().get('data')
        except Exception, e:
            apprepo_logger.exception("get_info_from_pom error: %s", e)

    @staticmethod
    def get_app_id_by_name(app_name):
        try:
            url = "{}/api/app/project/query_id_by_name".format(app.config['APPREPO_URL'])
            response = requests.get(url, params={'app_name': app_name}, timeout=20)
            if response.status_code == 200 and response.json().get("success") == 1:
                return response.json().get('id')
        except Exception, e:
            apprepo_logger.exception("get id by name error:%s", e)

    @staticmethod
    def list_app_id_by_user_id(user_id):
        try:
            url = "{}/api/app/project/list_project_id_by_user_id".format(app.config['APPREPO_URL'])
            response = requests.get(url, params={'user_id': user_id}, headers={'api': app.config['APPREPO_TOKEN']}, timeout=5)
            if response.status_code == 200 and response.json().get("result") == 1:
                return response.json().get('data')
        except Exception, e:
            apprepo_logger.exception("list id by user id error:%s", e)

    @staticmethod
    def create_sql_scripts_project(project_id, server_id):
        url = "{}/api/svn/sqlscript/create".format(app.config['APPREPO_URL'])
        data = {"project_id": project_id, "server_id": server_id, "production": "duang"}
        apprepo_logger.info("url: "+url)
        apprepo_logger.info("data: "+unicode(data))
        try:
            response = requests.post(url, data=data, headers={'api': app.config['APPREPO_TOKEN']}, timeout=20)
            content = response.content
            apprepo_logger.info("response:" + content)
            if response.status_code == 200:
                if response.json().get("result") == 1:
                    return True, response.json().get("data")
                else:
                    return False, response.json().get("message")
            else:
                return False, "SQL review branch create failed"
        except Exception, e:
            apprepo_logger.exception("SQL review branch create failed:%s", e)
            return False, "SQL review branch create failed"

    @staticmethod
    def get_sql_scripts_project_current_revision(svn_project_id, relative_path):
        url = "{}/api/svn/sqlscript/{}/current_revision".format(app.config['APPREPO_URL'], svn_project_id)

        data = {"relative_path": relative_path}
        apprepo_logger.info("url: " + url)
        apprepo_logger.info("data: " + unicode(data))
        try:
            response = requests.post(url, data=data, headers={'api': app.config['APPREPO_TOKEN']}, timeout=10)
            content = response.content
            apprepo_logger.info("response:"+ content)
            if response.status_code == 200:
                if response.json().get("result") == 1:
                    return True, response.json().get("data")
                else:
                    return False, "Get sql review project revision failed"
            else:
                return  False, "Get sql review project revision failed"
        except Exception, e:
            apprepo_logger.exception("Get sql review project revision failed:%s", e)
            return False, "Get sql review project revision failed"

    @staticmethod
    def list_project_code_review_status(project_id):
        try:
            url = "{}/diff/api/query_status".format(app.config['APPREPO_URL'])
            data = dict()
            data['project_id'] = project_id
            data['system'] = 'duang'
            apprepo_logger.info("url: {}".format(url))
            apprepo_logger.info("data: {}".format(data))
            response = requests.get(url, params=data, headers={'api': app.config['APPREPO_TOKEN']}, timeout=20)
            apprepo_logger.info("response: {}".format(response.content))
            if response.status_code == 200 and response.json().get("result") == 1:
                return response.json().get('data')
        except Exception, e:
            apprepo_logger.exception("list_project_code_review_status error:%s", e)
