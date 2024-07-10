# -*- coding:utf-8 -*-

import datetime
from flask import Blueprint, render_template, request, jsonify, session

from app.decorators.access_controle import api, require_login
from app.services.project.project_record_service import ProjectRecordService
from app.services.antx_service import AntxService
from app.services.diff_service import DiffService
from app.util import Util


antxProfile = Blueprint('antxProfile', __name__)


@antxProfile.route("/list/<string:project_id>", methods=['GET'])
@require_login()
def list_antx(project_id):
    data = AntxService.list_project_antx(project_id)
    ret = dict()
    ret['result'] = 1
    ret['data'] = data
    return jsonify(ret)


@antxProfile.route("/base-antx", methods=['GET'])
@require_login()
def base_antx():
    app_id = request.values.get('app_id')
    env = request.values.get('env')
    if app_id and Util.can_tune_to(app_id, int):
        data = AntxService.query_base_antx(env, int(app_id))
        ret = dict()
        ret['result'] = 1
        ret['data'] = data
        return jsonify(ret)
    return "error", 400


@antxProfile.route("/project-antx", methods=['PUT', 'DELETE', 'POST', 'GET'])
@require_login()
def project_antx():
    if request.method == 'PUT':
        data = request.json
        project_id = data.get('project_id')
        app_env_list = data.get('app_env_list')
        result, error_msg = AntxService.create_project_antx(project_id, app_env_list)
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
            ret['info'] = '<br>'.join(error_msg)
        return jsonify(ret)
    elif request.method == 'DELETE':
        project_id = request.values.get('project_id')
        app_id = request.values.get('app_id')
        env = request.values.get('env')
        if project_id and app_id and env and Util.can_tune_to(app_id, int):
            result = AntxService.delete_project_antx(project_id, int(app_id), env)
            ret = dict()
            if result:
                ret['result'] = 1
            else:
                ret['result'] = -1
            return jsonify(ret)
    elif request.method == 'POST':
        data = request.json
        project_id = data.get('project_id')
        app_id = data.get('app_id')
        env = data.get('env')
        content = data.get('content')
        result = AntxService.mod_project_antx(project_id, app_id, env, content)
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    elif request.method == 'GET':
        action = request.values.get('action')
        project_id = request.values.get('project_id')
        app_id = request.values.get('app_id')
        env = request.values.get('env')
        if project_id and app_id and env and Util.can_tune_to(app_id, int):
            data = AntxService.get_project_antx(project_id, int(app_id), env)
            ret = dict()
            ret['result'] = -1
            if data:
                if action == 'show':
                    diff = DiffService.compare_list(data.pop('base_content'), data.pop('content'))
                    data['diff'] = diff
                    ret['result'] = 1
                    ret['data'] = data
                elif action == 'edit':
                    data.pop('base_content')
                    ret['result'] = 1
                    ret['data'] = data
            return jsonify(ret)
    return "error", 400


@antxProfile.route("/project-diamond/review", methods=['POST'])
@require_login()
def project_antx_review():
    data = request.json
    project_id = data.get('project_id')
    app_id = data.get('app_id')
    env = data.get('env')
    app_name = data.get('app_name')
    review_status = data.get('review_status')
    if review_status == 'pass':
        ProjectRecordService.add_project_record(project_id, session['userId'], 'code_review', "ANTX_REVIEW",
                                                "ANTX_REVIEW_PASS", u"{}环境{}应用ANTX审批通过".format(env, app_name),
                                                datetime.datetime.now())
    elif review_status == 'refuse':
        ProjectRecordService.add_project_record(project_id, session['userId'], 'code_review', "ANTX_REVIEW",
                                                "ANTX_REVIEW_REFUSE", u"{}环境{}应用ANTX审批拒绝".format(env, app_name),
                                                datetime.datetime.now())
    result = AntxService.mod_project_antx(project_id, app_id, env, review_status=review_status)
    ret = dict()
    if result:
        ret['result'] = 1
    else:
        ret['result'] = -1
    return jsonify(ret)
