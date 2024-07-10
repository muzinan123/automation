# -*- coding:utf8 -*-

from flask import Blueprint, render_template, request, session, jsonify, make_response, send_from_directory

from app.decorators.access_controle import require_login
from app.decorators.paginate import make_paging_mongo
from app.services.aut_ci_project.aut_ci_project_service import AutCiProjectService
from app.services.apprepo_service import ApprepoService
from app.services.antx_service import AntxService

autciProjectProfile = Blueprint('autciProjectProfile', __name__)


@autciProjectProfile.route("/list", methods=['GET'])
@require_login()
def aut_ci_project_list():
    return render_template('aut-ci-project/list.html')


@autciProjectProfile.route("/create", methods=['GET'])
@require_login()
def aut_ci_project_create():
    return render_template('aut-ci-project/create.html')


@autciProjectProfile.route("/build-record", methods=['GET'])
@require_login()
def aut_ci_project_build_record():
    flow_id = request.values.get('flow_id')
    return render_template('aut-ci-project/build-record.html', flow_id=flow_id)


@autciProjectProfile.route("/aut-ci-project", methods=['PUT', 'DELETE', 'POST', 'GET'])
@require_login()
@make_paging_mongo("autciProjectList")
def aut_ci_project():
    if request.method == 'PUT':
        app_id = request.json.get('app_id')
        app_name = request.json.get('app_name')
        app_type = request.json.get('app_type')
        vcs_type = request.json.get('vcs_type')
        vcs_full_url = request.json.get('vcs_full_url')
        company = request.json.get('company')
        department = request.json.get('department')
        production = request.json.get('production')
        branch_name = request.json.get('branch_name')
        jdk_version = request.json.get('jdk_version')
        project_id = AutCiProjectService.add_aut_ci_project(app_id, app_name, app_type, vcs_type, vcs_full_url, company, department,
                                                            production, branch_name, jdk_version, session['userId'])
        ret = dict()
        ret['result'] = -1
        if project_id:
            add_antx_result, add_antx_info = AntxService.create_project_antx(project_id, [{'app_id': app_id, 'app_name': app_name, 'env_list': ['aut']}])
            if add_antx_result:
                ret['result'] = 1
                ret['info'] = u"创建成功"
            else:
                ret['info'] = u'创建Antx失败: {}'.format(add_antx_info)
        else:
            ret['info'] = u"创建失败"
        return jsonify(ret)
    elif request.method == 'DELETE':
        project_id = request.json.get('project_id')
        app_id = request.json.get('app_id')
        result = AutCiProjectService.del_aut_ci_project(project_id, session['userId'])
        AntxService.delete_project_antx(project_id, app_id, 'aut')
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    elif request.method == 'POST':
        project_id = request.json.get('project_id')
        branch_name = request.json.get('branch_name')
        jdk_version = request.json.get('jdk_version')
        result, info = AutCiProjectService.mod_aut_ci_project(project_id, branch_name=branch_name, jdk_version=jdk_version)
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
        pipeline, collection = AutCiProjectService.list_aut_ci_project(query, asc=asc, order_by=order_by)
        return pipeline, collection


@autciProjectProfile.route("/aut-ci-project/build", methods=['POST'])
@require_login()
def aut_ci_project_build():
    project_id = request.json.get('project_id')
    result = AutCiProjectService.build_aut_ci_project(project_id, operator_id=session['userId'])
    ret = dict()
    if result:
        ret['result'] = 1
    else:
        ret['result'] = -1
    return jsonify(ret)
