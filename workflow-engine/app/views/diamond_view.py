# -*- coding:utf-8 -*-

import datetime
from flask import Blueprint, render_template, request, jsonify, session

from app.decorators.access_controle import require_login
from app.services.project.project_record_service import ProjectRecordService
from app.services.diamond_service import DiamondService
from app.services.diff_service import DiffService


diamondProfile = Blueprint('diamondProfile', __name__)


@diamondProfile.route("/list/<string:project_id>", methods=['GET'])
@require_login()
def list_diamond(project_id):
    data = DiamondService.list_project_diamond(project_id)
    ret = dict()
    ret['result'] = 1
    ret['data'] = data
    return jsonify(ret)


@diamondProfile.route("/base-diamond", methods=['GET'])
@require_login()
def base_diamond():
    data_id = request.values.get('data_id')
    env = request.values.get('env')
    data = DiamondService.query_diamond(env, data_id)
    ret = dict()
    ret['result'] = 1
    ret['data'] = data
    return jsonify(ret)


@diamondProfile.route("/project-diamond", methods=['PUT', 'DELETE', 'POST', 'GET'])
@require_login()
def project_diamond():
    if request.method == 'PUT':
        data = request.json
        project_id = data.get('project_id')
        data_id = data.get('data_id')
        env = data.get('env')
        content = data.get('content')
        m_type = data.get('m_type')
        base_version = data.get('base_version')
        base_content = data.get('base_content')
        creator_id = session['userId']
        content = content.replace("\n", "\r\n")
        content = content.replace("\r\r\n", "\r\n")
        ret = dict()
        result = DiamondService.create_project_diamond(project_id, env, data_id, m_type, 'init', base_version, base_content, content, creator_id)
        if env == 'test' or env == 'aut' and result:
            commit_result, msg = DiamondService.commit_single_diamond(project_id, env, data_id)
            if commit_result:
                ret['result'] = 1
                ret['message'] = u'保存并提交成功'
            else:
                ret['result'] = -1
                ret['message'] = u'保存成功但是提交失败, {}'.format(msg)
        elif result:
            ret['result'] = 1
            ret['message'] = u'保存成功'
        else:
            ret['result'] = -1
            ret['message'] = u'保存失败,请确认项目中相同环境下是否已经存在相同dataId的修改。'
        return jsonify(ret)
    elif request.method == 'DELETE':
        project_id = request.values.get('project_id')
        data_id = request.values.get('data_id')
        env = request.values.get('env')
        result = DiamondService.delete_project_diamond(project_id, env, data_id)
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    elif request.method == 'POST':
        data = request.json
        project_id = data.get('project_id')
        data_id = data.get('data_id')
        env = data.get('env')
        content = data.get('content')
        m_type = data.get('m_type')
        content = content.replace("\n", "\r\n")
        content = content.replace("\r\r\n", "\r\n")
        result = DiamondService.mod_project_diamond(project_id, env, data_id, m_type=m_type, content=content)
        ret = dict()
        if env == 'test' or env == 'aut' and result:
            commit_result, msg = DiamondService.commit_single_diamond(project_id, env, data_id)
            if commit_result:
                ret['result'] = 1
                ret['message'] = u'保存并提交成功'
            else:
                ret['result'] = -1
                ret['message'] = u'保存成功但是提交失败, {}'.format(msg)
        elif result:
            ret['result'] = 1
            ret['message'] = u'保存成功'
        else:
            ret['result'] = -1
            ret['message'] = u'保存失败'
        return jsonify(ret)
    elif request.method == 'GET':
        action = request.values.get('action')
        project_id = request.values.get('project_id')
        data_id = request.values.get('data_id')
        env = request.values.get('env')
        if project_id and data_id and env:
            data = DiamondService.get_project_diamond(project_id, env, data_id)
            ret = dict()
            if data:
                if action == 'show':
                    diff = DiffService.diff(data.pop('base_content'), data.pop('content'))
                    data['diff'] = diff
                    ret['result'] = 1
                    ret['data'] = data
                elif action == 'edit':
                    data.pop('base_content')
                    ret['result'] = 1
                    ret['data'] = data
            else:
                ret['result'] = -1
            return jsonify(ret)
    return "error", 400


@diamondProfile.route("/project-diamond/review", methods=['POST'])
@require_login()
def project_diamond_review():
    data = request.json
    project_id = data.get('project_id')
    env = data.get('env')
    data_id = data.get('data_id')
    review_status = data.get('review_status')
    if review_status == 'pass':
        ProjectRecordService.add_project_record(project_id, session['userId'], 'code_review', "DIAMOND_REVIEW", "DIAMOND_REVIEW_PASS", u"{}环境Diamond[{}]审批通过".format(env, data_id), datetime.datetime.now())
    elif review_status == 'refuse':
        ProjectRecordService.add_project_record(project_id, session['userId'], 'code_review', "DIAMOND_REVIEW",
                                                "DIAMOND_REVIEW_REFUSE", u"{}环境Diamond[{}]审批拒绝".format(env, data_id),
                                                datetime.datetime.now())
    result = DiamondService.mod_project_diamond(project_id, env, data_id, review_status=review_status)
    ret = dict()
    if result:
        ret['result'] = 1
    else:
        ret['result'] = -1
    return jsonify(ret)
