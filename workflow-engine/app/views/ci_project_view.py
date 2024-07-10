# -*- coding:utf8 -*-

from flask import Blueprint, render_template, request, session, jsonify, make_response, send_from_directory

from app.decorators.access_controle import require_login
from app.decorators.paginate import make_paging_mongo
from app.services.ci_project.ci_project_service import CiProjectService
from app.services.apprepo_service import ApprepoService

ciProjectProfile = Blueprint('ciProjectProfile', __name__)


@ciProjectProfile.route("/list", methods=['GET'])
@require_login()
def ci_project_list():
    return render_template('ci-project/list.html')


@ciProjectProfile.route("/create", methods=['GET'])
@require_login()
def ci_project_create():
    return render_template('ci-project/create.html')


@ciProjectProfile.route("/build-record", methods=['GET'])
@require_login()
def ci_project_build_record():
    flow_id = request.values.get('flow_id')
    return render_template('ci-project/build-record.html', flow_id=flow_id)


@ciProjectProfile.route("/detail/basic/<int:app_id>/<string:branch>", methods=['GET'])
@require_login()
def ci_project_detail_basic(app_id, branch):
    data = CiProjectService.get_ci_project(app_id, branch)
    ret = dict()
    if data:
        ret['result'] = 1
        ret['data'] = data
    else:
        ret['result'] = -1
    return jsonify(ret)


@ciProjectProfile.route("/ci-project", methods=['PUT', 'DELETE', 'POST', 'GET'])
@require_login()
@make_paging_mongo("ciProjectList")
def ci_project():
    if request.method == 'PUT':
        app_id = request.json.get('app_id')
        app_name = request.json.get('app_name')
        vcs_type = request.json.get('vcs_type')
        vcs_full_url = request.json.get('vcs_full_url')
        company = request.json.get('company')
        department = request.json.get('department')
        production = request.json.get('production')
        branch_name = request.json.get('branch_name')
        jdk_version = request.json.get('jdk_version')
        result, info = CiProjectService.add_ci_project(app_id, app_name, vcs_type, vcs_full_url, company, department,
                                                       production, branch_name, jdk_version, session['userId'])
        ret = dict()
        if result:
            ret['result'] = 1
            ret['info'] = info
        else:
            ret['result'] = -1
            ret['info'] = info
        return jsonify(ret)
    elif request.method == 'DELETE':
        app_id = request.json.get('app_id')
        branch_name = request.json.get('branch_name')
        result = CiProjectService.del_ci_project(app_id, branch_name, session['userId'])
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    elif request.method == 'POST':
        app_id = request.json.get('app_id')
        branch_name = request.json.get('branch_name')
        jdk_version = request.json.get('jdk_version')
        new_branch_name = request.json.get('new_branch_name')
        result, info = CiProjectService.mod_ci_project(app_id, branch_name, jdk_version=jdk_version,
                                                       new_branch_name=new_branch_name)
        ret = dict()
        if result:
            ret['result'] = 1
            ret['info'] = info
        else:
            ret['result'] = -1
            ret['info'] = info
        return jsonify(ret)
    elif request.method == 'GET':
        query = request.values.get('query')
        asc = request.values.get('asc')
        order_by = request.values.get('order_by', 'create_at')
        pipeline, collection = CiProjectService.list_ci_project(query, asc=asc, order_by=order_by)
        return pipeline, collection


@ciProjectProfile.route("/ci-project/participant_app_id", methods=['GET'])
@require_login()
def participant_app_id():
    app_id_list = ApprepoService.list_app_id_by_user_id(session['userId'])
    ret = dict()
    ret['data'] = app_id_list
    ret['result'] = 1
    return jsonify(ret)


@ciProjectProfile.route("/ci-project/build", methods=['POST'])
@require_login()
def ci_project_build():
    app_id = request.json.get('app_id')
    branch_name = request.json.get('branch_name')
    result = CiProjectService.build_ci_project(app_id, branch_name, operator_id=session['userId'])
    ret = dict()
    if result:
        ret['result'] = 1
    else:
        ret['result'] = -1
    return jsonify(ret)
