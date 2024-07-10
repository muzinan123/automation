# -*- coding: utf8 -*-

from flask import Blueprint, jsonify, render_template, request, session, make_response, url_for, send_file

from app.decorators.access_controle import require_login, privilege
from app.decorators.paginate import make_paging, make_paging_mongo
from app.services.nexus_service import NexusService
from app.util import Util

nexusProfile = Blueprint('nexusProfile', __name__)


@nexusProfile.route("/dependency/list", methods=['GET'])
@require_login()
def list_dependency_list():
    return render_template("nexus/dependency-list.html")


@nexusProfile.route("/dependency", methods=['GET'])
@require_login()
@make_paging('dependencyList')
def list_dependency():
    query = request.values.get('query')
    order_by = request.values.get('order_by', 'create_at')
    order_desc = Util.jsbool2pybool(request.values.get('order_desc', 'true'))
    data = NexusService.list_app_dependency(query, order_by, order_desc)
    return data


@nexusProfile.route("/dependency/parent-version", methods=['GET'])
@require_login()
def list_dependency_parent_version():
    data = NexusService.get_parent_version()
    ret = dict()
    if data:
        ret['result'] = 1
        ret['data'] = data
    else:
        ret['result'] = -1
    return jsonify(ret)


@nexusProfile.route("/dependency/parent/pom.xml", methods=['GET'])
def get_dependency_parent_pom_xml():
    project_id = request.values.get('project_id')
    result = NexusService.generate_pom(project_id=project_id)
    result.seek(0)
    if result:
        return send_file(result, attachment_filename="pom.xml")


@nexusProfile.route("/dependency/log", methods=['GET'])
@require_login()
@make_paging_mongo('logList')
def list_dependency_log():
    share_name = request.values.get('share_name')
    asc = Util.jsbool2pybool(request.values.get('asc', 'true'))
    pipeline, collection = NexusService.list_app_dependency_log(share_name, asc)
    return pipeline, collection


@nexusProfile.route("/mod_version", methods=['POST'])
@require_login()
@privilege('pe')
def mod_version():
    artifact_id = request.values.get('artifact_id')
    version = request.values.get('version')
    result = NexusService.mod_version(artifact_id, version, modifier=session['userId'])
    ret = dict()
    if result:
        ret['result'] = 1
    else:
        ret['result'] = -1
    return jsonify(ret)
