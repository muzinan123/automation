# -*- coding: utf8 -*-
from app.out.jira import Jira
from app.services.project.project_service import ProjectService


class JiraService(object):

    @staticmethod
    def get_project_by_jira(issue_key=None, version_id=None):
        if issue_key:
            res = Jira.get_issue_by_jira(issue_key)
        elif version_id:
            res = Jira.get_version_by_jira(version_id)
        if res:
            return res

    @staticmethod
    def get_jira_approve_status(issue_key):
        # jira获取需求审核的是否通过
        history_list = Jira.get_approve_status(issue_key)
        if history_list:
            for h in history_list:
                items = h.get('items')
                for item in items:
                    if item.get('fromString') == u'需求审核':
                        return True
            return False
        elif history_list is not None:
            return False

    @staticmethod
    def get_project_key_by_jira(project_id):
        if project_id:
            res = Jira.get_project_key_by_jira(project_id)
            if res:
                return res

    @staticmethod
    def close_jira_project(project_id):
        project = ProjectService.get_project(project_id)
        if project:
            issue_id = project.jira_issue_id
            version_id = project.jira_version_id
            if issue_id:
                code = Jira.get_issue_transitions_done_code(issue_id)
                if code:
                    Jira.make_issue_transitions_done(issue_id, code)
            elif version_id:
                Jira.make_version_release(version_id)
            return True




