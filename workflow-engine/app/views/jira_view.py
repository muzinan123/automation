# -*- coding:utf8 -*-

from flask import Blueprint, request, jsonify

from app.decorators.access_controle import allow_cross_domain, require_login
from app.services.project.project_service import ProjectService
from app.services.jira_service import JiraService
from app.services.framework.user_service import UserService
from app.services.framework.kafka_service import KafkaService


jiraProfile = Blueprint('jiraProfile', __name__)


@jiraProfile.route('/project/check_issue_info', methods=['POST'])
@allow_cross_domain()
def check_issue_info():
    issue_id = request.values.get('issueId')
    issue_key = request.values.get('issueKey')
    ret = dict()
    if not issue_id or not issue_key:
        ret['success'] = False
        ret['errorMsg'] = 'issueId is null or issue_key is null'
        return jsonify(ret)
    project_id = ProjectService.query_project_by_issue_info(issue_id, issue_key)
    ret['success'] = True
    ret['projectId'] = project_id
    return jsonify(ret)


@jiraProfile.route('/project/sync_issue_info', methods=['POST'])
@allow_cross_domain()
def sync_issue_info():
    # 同步jira信息至project表中
    # 加一个允许跨域的
    jira_issue_id = request.values.get('issueId')
    jira_issue_key = request.values.get('issueKey')
    ret = dict()
    if not jira_issue_id or not jira_issue_key:
        ret['success'] = False
        ret['errorMsg'] = u'参数错误[issueId is null or issueKey is null]'
        return jsonify(ret)
    if not JiraService.get_jira_approve_status(jira_issue_key):
        ret['success'] = False
        ret['errorMsg'] = u'未通过需求审批阶段，无法创建项目，请先进行需求审批'
        return jsonify(ret)
    elif JiraService.get_jira_approve_status(jira_issue_key) is None:
        ret['success'] = False
        ret['errorMsg'] = u'同步异常'
        return jsonify(ret)
    res = JiraService.get_project_by_jira(issue_key=jira_issue_key)
    if res:
        project_name = res.get('summary')
        summary = res.get('description')
        creator_name = request.values.get('login_user')
        creator = UserService.get_user_by_name(creator_name).one_or_none()
        if creator:
            owner_id = creator.id
        else:
            ret['success'] = False
            ret['errorMsg'] = u'Duang系统中没有找到经办人信息，请联系core@zhongan.com进行检查'
            return jsonify(ret)
        begin_date = res.get('created')
        project_type = res.get('issuetype').get('name')
        begin_date_str = begin_date[0:10]
        jira_project_key = res.get('project').get('key') if res.get('project') else None
        project_id = ProjectService.add_project(name=project_name, project_type=project_type, begin_date=begin_date_str,
                                                owner_id=owner_id, summary=summary, jira_issue_id=jira_issue_id,
                                                jira_issue_key=jira_issue_key, jira_project_key=jira_project_key)
        if project_id:
            ret = dict()
            data = KafkaService.assemble_jira_sync_duang_kafka_json(project_id, project_name, jira_issue_id=jira_issue_id, jira_issue_key=jira_issue_key)
            KafkaService.produce(data)
            ret['success'] = True
            return jsonify(ret)
    return jsonify({"success": False, "errorMsg": u"同步异常"})


@jiraProfile.route('/project/check_version_info', methods=['POST'])
@allow_cross_domain()
def check_version_info():
    version_id = request.values.get('versionId')
    ret = dict()
    if not version_id:
        ret['success'] = False
        ret['errorMsg'] = 'versionId is null'
        return jsonify(ret)
    project_id = ProjectService.query_project_by_version_info(version_id)
    ret['success'] = True
    ret['projectId'] = project_id
    return jsonify(ret)


@jiraProfile.route('/project/sync_version_info', methods=['POST'])
@allow_cross_domain()
def sync_version_info():
    # 同步jira信息至project表中
    # 加一个允许跨域的
    jira_version_id = request.values.get('versionId')
    ret = dict()
    if not jira_version_id:
        ret['success'] = False
        ret['errorMsg'] = u'参数错误[versionId is null]'
        return jsonify(ret)
    res = JiraService.get_project_by_jira(version_id=jira_version_id)
    if res:
        project_name = res.get('name')
        summary = res.get('description')
        creator_name = request.values.get('login_user')
        creator = UserService.get_user_by_name(creator_name).one_or_none()
        if creator:
            owner_id = creator.id
        else:
            ret['success'] = False
            ret['errorMsg'] = u'Duang系统中没有找到经办人信息，请联系core@zhongan.com进行检查'
            return jsonify(ret)
        project_id = res.get('projectId')
        jira_project_key = JiraService.get_project_key_by_jira(project_id)
        begin_date = res.get('startDate')
        release_date = res.get('releaseDate')
        project_id = ProjectService.add_project(name=project_name, begin_date=begin_date, expect_publish_date=release_date,
                                                 owner_id=owner_id, summary=summary, jira_version_id=jira_version_id, jira_project_key=jira_project_key)
        if project_id:
            ret = dict()
            data = KafkaService.assemble_jira_sync_duang_kafka_json(project_id, project_name, jira_version_id=jira_version_id)
            KafkaService.produce(data)
            ret['success'] = True
            return jsonify(ret)
    return jsonify({"success": False, "errorMsg": u"同步异常"})
