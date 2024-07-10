# -*- coding: utf8 -*-
import requests
import datetime
from app import app, out_logger


class Jira(object):

    @staticmethod
    def get_issue_by_jira(issue_key):
        try:
            headers = {"jira-user": app.config['JIRA_USER'], "token": app.config['JIRA_TOKEN']}
            url = '{}/rest/api/latest/issue/{}'.format(app.config['JIRA_SERVER_URL'], issue_key)
            out_logger.info(url)
            response = requests.get(url, headers=headers, timeout=20)
            out_logger.info(response.content)
            return response.json().get('fields')
        except Exception, e:
            out_logger.exception("get project info exception %s", e)

    @staticmethod
    def get_approve_status(issue_key):
        try:
            headers = {"jira-user": app.config['JIRA_USER'], "token": app.config['JIRA_TOKEN']}
            url = '{}/rest/api/latest/issue/{}?expand=changelog'.format(app.config['JIRA_SERVER_URL'], issue_key)
            out_logger.info(url)
            response = requests.get(url, headers=headers, timeout=20)
            out_logger.info(response.content)
            return response.json().get('changelog').get('histories')
        except Exception, e:
            out_logger.exception("get approve status exception %s", e)

    @staticmethod
    def get_version_by_jira(version_id):
        try:
            headers = {"jira-user": app.config['JIRA_USER'], "token": app.config['JIRA_TOKEN']}
            url = '{}/rest/api/latest/version/{}'.format(app.config['JIRA_SERVER_URL'], version_id)
            out_logger.info(url)
            response = requests.get(url, headers=headers, timeout=20)
            out_logger.info(response.content)
            return response.json()
        except Exception, e:
            out_logger.exception("get project info exception %s", e)

    @staticmethod
    def get_project_key_by_jira(project_id):
        try:
            headers = {"jira-user": app.config['JIRA_USER'], "token": app.config['JIRA_TOKEN']}
            url = '{}/rest/api/latest/project/{}'.format(app.config['JIRA_SERVER_URL'], project_id)
            out_logger.info(url)
            response = requests.get(url, headers=headers, timeout=20)
            out_logger.info(response.content)
            return response.json().get('key')
        except Exception, e:
            out_logger.exception("get project info exception %s", e)

    @staticmethod
    def get_issue_transitions_done_code(issue_id):
        try:
            headers = {"jira-user": app.config['JIRA_USER'], "token": app.config['JIRA_TOKEN']}
            url = '{}/rest/api/latest/issue/{}/transitions'.format(app.config['JIRA_SERVER_URL'], issue_id)
            out_logger.info(url)
            response = requests.get(url, headers=headers, timeout=20)
            out_logger.info(response.content)
            data = response.json().get('transitions')
            for d in data:
                if d.get('name') == 'Done':
                    return d.get('id')
        except Exception, e:
            out_logger.exception("get jira issue transitions done code exception %s", e)

    @staticmethod
    def make_issue_transitions_done(issue_id, code):
        try:
            headers = {"jira-user": app.config['JIRA_USER'], "token": app.config['JIRA_TOKEN']}
            url = '{}/rest/api/latest/issue/{}/transitions'.format(app.config['JIRA_SERVER_URL'], issue_id)
            data = {'transition': {'id': code}}
            out_logger.info(url)
            out_logger.info(data)
            response = requests.post(url, headers=headers, json=data, timeout=20)
            out_logger.info("return code: "+str(response.status_code))
            if response.status_code == 204:
                return True
            return False
        except Exception, e:
            out_logger.exception("close jira project exception %s", e)

    @staticmethod
    def make_version_release(version_id):
        try:
            headers = {"jira-user": app.config['JIRA_USER'], "token": app.config['JIRA_TOKEN']}
            url = '{}/rest/api/latest/version/{}'.format(app.config['JIRA_SERVER_URL'], version_id)
            data = {'released': True, 'releaseDate': datetime.datetime.now().strftime('%Y-%m-%d')}
            out_logger.info(url)
            out_logger.info(data)
            response = requests.put(url, headers=headers, json=data, timeout=20)
            out_logger.info("return code: "+str(response.status_code))
            if response.status_code == 200:
                return True
            return False
        except Exception, e:
            out_logger.exception("close jira project exception %s", e)