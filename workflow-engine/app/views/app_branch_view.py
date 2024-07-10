# -*- coding: utf8 -*-

from flask import Blueprint, render_template, request, jsonify, session

from app.decorators.access_controle import api, require_login
from app.services.project.project_service import ProjectService
from app.services.app_branch_service import AppBranchService
from app.services.antx_service import AntxService
from app.util import Util
import json

appBranchProfile = Blueprint('appBranchProfile', __name__)


@appBranchProfile.route("/list/<string:project_id>", methods=['GET'])
@require_login()
def list_app_branch(project_id):
    project = ProjectService.get_project(project_id)
    app_list = AppBranchService.list_app_branch(project_id, ['app'])
    share_list = AppBranchService.list_app_branch(project_id, ['open', 'module'])
    dzbd_list = AppBranchService.list_app_branch(project_id, ['dzbd'])
    data = dict()
    data['app'] = app_list
    data['share'] = share_list
    data['dzbd'] = dzbd_list

    if session['userId'] in [e.participant_id for e in project.code_review_list]:
        for one in data['app']:
            app_id = one.get('app_id')
            branch = one.get('branch')
            original = one.get('original')
            submit_test = one.get('submit_test')
            one['review_token'] = AppBranchService.signiture_app_branch(project_id, app_id, branch, original, submit_test)
        for one in data['share']:
            app_id = one.get('app_id')
            branch = one.get('branch')
            original = one.get('original')
            submit_test = one.get('submit_test')
            one['review_token'] = AppBranchService.signiture_app_branch(project_id, app_id, branch, original, submit_test)
        for one in data['dzbd']:
            app_id = one.get('app_id')
            branch = one.get('branch')
            original = one.get('original')
            submit_test = one.get('submit_test')
            one['review_token'] = AppBranchService.signiture_app_branch(project_id, app_id, branch, original, submit_test)
    else:
        for one in data['app']:
            one['review_token'] = ""
        for one in data['share']:
            one['review_token'] = ""
        for one in data['dzbd']:
            one['review_token'] = ""

    ret = dict()
    ret['result'] = 1
    ret['data'] = data
    return jsonify(ret)


@appBranchProfile.route("/project-app-branch", methods=['POST', 'GET', 'PUT', 'DELETE'])
@require_login()
def project_app_branch():
    if request.method == 'PUT':
        data = request.json
        project_id = data.get('project_id')
        app_id = data.get('app_id')
        vcs_type = data.get('vcs_type')
        app_name = data.get('app_name')
        app_type = data.get('app_type')
        vcs_full_url = data.get('vcs_full_url')
        app_branch = AppBranchService.get_app_branch(project_id, app_id)
        if app_branch:
            version = app_branch.get('version')
            AppBranchService.disable_app_branch(project_id, app_id, version)
        result = AppBranchService.add_app_branch(project_id, app_id, 'DEFAULT', vcs_type, app_name, app_type, vcs_full_url)
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    elif request.method == 'DELETE':
        project_id = request.values.get('project_id')
        app_id = request.values.get('app_id')
        version = request.values.get('version')
        antx_env = request.values.get('antx_env')
        result = AppBranchService.disable_app_branch(project_id, int(app_id), int(version))
        if antx_env:
            for env in antx_env.split(','):
                AntxService.delete_project_antx(project_id, int(app_id), env)
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
        version = data.get('version')
        f_type = data.get('f_type')
        order = data.get('order')
        result = AppBranchService.mod_app_branch(project_id, app_id, version, f_type, order)
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)





