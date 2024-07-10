# -*- coding:utf8 -*-

import json

from flask import Blueprint, request, jsonify, send_file, render_template
from flask_socketio import emit
from app.services.apprepo_service import ApprepoService
from app.decorators.access_controle import api
from app.services.antx_service import AntxService
from app.services.diamond_service import DiamondService
from app.services.operation.operation_service import OperationService
from app.services.nexus_service import NexusService
from app.services.project.project_service import ProjectService
from app.services.project.sql_scripts_project_service import SQLScriptsProjectService
from app.services.framework.message_service import MessageService
from app.services.flow.workflow import Workflow
from app.out.zabbix import Zabbix
from app.out.monitor import Monitor
from app.util import Util
from app import app

commonApiProfile = Blueprint('commonApiProfile', __name__)


@commonApiProfile.route("/operate", methods=['POST'])
@api()
def operate():
    sync = request.values.get('sync')
    operation_type = request.values.get('operation_type')
    target = request.values.get('target')
    app_name = request.values.get('app_name')
    operator_id = request.values.get('operator_id')
    params = request.values.get('params')
    kwargs = json.loads(params)
    emit('notify_new', {}, namespace='/result', broadcast=True)
    if sync:
        result = OperationService.run_operation(operation_type, target, app_name, operator_id, **kwargs)
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    else:
        OperationService.run_operation.delay(operation_type, target, app_name, operator_id, **kwargs)
        ret = dict()
        ret['result'] = 1
        return jsonify(ret)


@commonApiProfile.route("/get_updated_pom/pom.xml", methods=['POST'])
@api()
def get_updated_pom():
    if request.method == 'POST':
        project_id = request.values.get('project_id')
        parent_version = request.values.get('parent_version') == 'true'
        self_version = request.values.get('self_version') == 'true'
        file = request.files['pom']
        if file and file.filename == 'pom.xml':
            new_pom = NexusService.update_app_pom(file.stream, parent_version=parent_version, self_version=self_version,
                                                  project_id=project_id)
            new_pom.seek(0)
            if new_pom:
                return send_file(new_pom, attachment_filename="pom.xml")
    return 'error', 400


@commonApiProfile.route("/get_updated_version", methods=['GET'])
def get_updated_version():
    parent = request.values.get('parent') == 'true'
    artifact_id = request.values.get('artifact_id')
    project_id = request.values.get('project_id')
    share_version = "-1"
    if artifact_id:
        NexusService.preallocate_share_version(artifact_id, project_id)
        share_version = NexusService.get_share_version(artifact_id, project_id=project_id)
    if parent:
        NexusService.preallocate_parent_version(project_id)
    parent_version = NexusService.get_parent_version(project_id=project_id)
    return "parent:{} share:{}".format(parent_version, share_version), 200


@commonApiProfile.route("/commit_version_by_project_id", methods=['POST'])
def commit_version_by_project_id():
    project_id = request.values.get('project_id')
    if project_id:
        result = NexusService.commit_version_by_project_id(project_id)
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    return "error", 400


@commonApiProfile.route("/antx/<string:env>/<string:project_id>/<int:app_id>/<string:app_name>.properties", methods=['GET'])
@api()
def download_antx(env, project_id, app_id, app_name):
    # antx.properties下载
    data = AntxService.get_project_antx(project_id, app_id, env)
    if data:
        return render_template('antx/antx.properties', content=data.get("content", []))
    else:
        base_content = AntxService.query_base_antx(env, app_id)
        return render_template('antx/antx.properties', content=base_content)


@commonApiProfile.route("/query/antx", methods=['GET'])
def query_antx():
    # antx根据appName和env查询Antx content接口
    name = request.values.get("appName")
    env = request.values.get("env")
    app_id = ApprepoService.get_app_id_by_name(name)
    ret = dict()
    if not app_id:
        ret["success"] = 0
        return jsonify(ret)
    content = AntxService.query_base_antx(env, app_id)
    content_string = ''
    for ct in content:
        content_string = content_string + ct.get('k') + ' = ' + ct.get('v').replace('&','&amp;') + '\n'
    ret['success'] = 1
    ret['content'] = content_string
    return jsonify(ret)


@commonApiProfile.route("/update/antx", methods=['POST'])
def update_antx():
    # 修改Antx接口
    name = request.values.get("appName")
    env = request.values.get("env")
    content = request.values.get("content")
    app_id = ApprepoService.get_app_id_by_name(name)
    ret = dict()
    if not app_id:
        ret["success"] = 0
        ret["errMsg"] = "can't find app"
        return jsonify(ret)
    try:
        AntxService.update_base_antx(env, app_id, name, content)
        ret["success"] = 1
        return jsonify(ret)
    except Exception, e:
        ret["success"] = 0
        ret["errMsg"] = e.message
        return jsonify(ret)


@commonApiProfile.route("/query/diamond", methods=['GET'])
def query_diamond_duang():
    # 老duang使用,根据env和dataId查询diamond version
    duang_env = request.values.get('env')
    if duang_env == 'local':
        env = 'test'
    else:
        env = duang_env
    data_id = request.values.get('dataId')
    version = DiamondService.query_diamond_version(data_id, env)
    ret = dict()
    ret['success'] = 1
    ret['version'] = version
    ret['env'] = duang_env
    ret['dataId'] = data_id
    return jsonify(ret)


@commonApiProfile.route("/update/diamond", methods=['POST'])
def update_diamond_duang():
    # 老duang使用,根据env和dataId更新diamond version, version = version + 1
    duang_env = request.values.get('env')
    if duang_env == 'local':
        env = 'test'
    else:
        env = duang_env
    data_id = request.values.get('dataId')
    d = DiamondService.update_diamond_version(data_id, env)
    ret = dict()
    if d:
        ret['success'] = 1
    else:
        ret['success'] = 0
    return jsonify(ret)


@commonApiProfile.route("/add/diamond", methods=['POST'])
def add_diamond_duang():
    # 老duang使用,新增engine_diamond_version记录
    duang_env = request.values.get('env')
    if duang_env == 'local':
        env = 'test'
    else:
        env = duang_env
    data_id = request.values.get('dataId')
    d = DiamondService.add_diamond_version(data_id, env)
    ret = dict()
    if d:
        ret['success'] = 1
    else:
        ret['success'] = 0
    return jsonify(ret)


@commonApiProfile.route("/query/diamond/list", methods=['GET'])
@api()
def query_diamond_list():
    # westworld使用,根据env查询engine_diamond_version list
    env = request.values.get('env')
    diamond_list = DiamondService.query_diamond_by_env(env)
    ret = dict()
    ret['success'] = 1
    ret['data'] = diamond_list
    return jsonify(ret)


@commonApiProfile.route("/query/diamond/content", methods=['GET'])
@api()
def query_diamond_content():
    # westworld使用,根据env和dataId查询diamond信息
    env = request.values.get('env')
    data_id = request.values.get('data_id')
    diamond = DiamondService.query_diamond(env, data_id)
    ret = dict()
    ret['success'] = 1
    ret['data'] = diamond
    return jsonify(ret)


@commonApiProfile.route("/update/diamond/content", methods=['POST'])
@api()
def update_diamond_content():
    # westworld使用,根据dataId,env更新diamond的version + 1, modifier和content
    env = request.values.get('env')
    data_id = request.values.get('dataId')
    content = request.values.get('content')
    version = request.values.get('version')
    modifier = request.values.get('modifier')
    if version and Util.can_tune_to(version, int):
        res, error = DiamondService.update_diamond_content_version(data_id, env, content, int(version), modifier)
        ret = dict()
        if res:
            ret['success'] = 1
        else:
            ret['success'] = 0
            ret['error'] = error
        return jsonify(ret)
    return "error", 400


@commonApiProfile.route("/sqlreview/feedback", methods=['GET'])
@api()
def sqlreview_feedback():
    project_id = request.values.get('project_id')
    review_status = request.values.get('review_status')
    env = request.values.get('env')

    if review_status in ['pass', 'not_pass', 'not_support']:
        if review_status == 'not_support':
            result = SQLScriptsProjectService.change_to_manual(project_id, env)
            datas = dict()
            datas['project_id'] = project_id
            datas['url'] = app.config.get('SERVER_URL') + '/project/detail/' + project_id
            MessageService.sql_review(datas)
        else:
            result, message = ProjectService.update_sql_review_status(project_id, 'system', env, review_status)
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
            ret['message'] = message
        return jsonify(ret)
    return "error", 400


@commonApiProfile.route("/sqlexecute/feedback", methods=['GET'])
@api()
def sqlexecute_feedback():
    project_id = request.values.get('project_id')
    execute_status = request.values.get('execute_status')
    env = request.values.get('env')
    if execute_status in ['success', 'failed']:
        result = ProjectService.update_sql_execute_status(project_id, 'system', env, execute_status)
        ret = dict()
        if result:
            project = SQLScriptsProjectService.get_sql_scripts_project(project_id)
            result = Workflow.go(project.get('publish_id'), execute_status)
            if result:
                ret['result'] = 1
            else:
                ret['result'] = -1
        else:
            ret['result'] = -1
        return jsonify(ret)
    return "error", 400


@commonApiProfile.route("/stop/app_monitor", methods=['POST'])
@api()
def stop_app_monitor():
    data = request.json
    app_name = data.get('app_name')
    addr_list = data.get('addr_list')
    check_url = data.get('check_url')
    ret = dict()
    has_error = False
    app_error_list = list()

    for addr in addr_list:
        addr_tmp = addr.split(':')
        ip = addr_tmp[0]
        port = addr_tmp[1]
        hostid = Zabbix.query_host_info(ip)
        if not hostid:
            za_result = True
        else:
            # 根据hostid获取httptest信息
            httptest_id = Zabbix.query_httptest_info(hostid, str(port))
            # 启停监控
            if httptest_id:
                za_result = Zabbix.httptest_update(httptest_id, 1)
            else:
                za_result = True
        mon_result = Monitor.monitor_stop(ip, str(port), app_name, check_url)
        if not za_result or not mon_result:
            has_error = True
            app_error_list.append("{}:{}".format(ip, port))
    if has_error:
        ret['result'] = -1
    else:
        ret['result'] = 1
    ret['info'] = {'app_name': app_name, 'addr_list': app_error_list, 'check_url': check_url}
    return jsonify(ret)
