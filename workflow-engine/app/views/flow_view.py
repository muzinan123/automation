# -*- coding:utf8 -*-

from flask import Blueprint, jsonify, render_template, request, session, make_response, url_for

from app.decorators.access_controle import require_login
from app.decorators.paginate import make_paging
from app.services.flow.config import Config
from app.services.flow.workflow import Workflow, WorkflowService
from app.services.flow.workflow_template_service import WorkflowTemplateService
from app.util import Util


flowProfile = Blueprint('flowProfile', __name__)


@flowProfile.route("/publish/list", methods=['GET'])
@require_login()
def publish_list():
    return render_template('flow/publish/list.html')


@flowProfile.route("/publish/config", methods=['GET'])
@require_login()
def publish_config():
    flow_type = request.values.get('flow_type', 'default')
    return render_template('flow/publish/config.html', flow_type=flow_type)


@flowProfile.route("/load_svg", methods=['GET'])
@require_login()
def load_flow_svg():
    flow_type = request.values.get('flow_type')
    current_task_type = request.values.get('current_task_type')
    ret = dict()
    data = dict()
    svg = "graph TB\n "
    svg += "\n ".join(Config.get_flow_svg(flow_type, current_task_type))
    data['svg'] = svg
    ret['result'] = 1
    ret['data'] = data
    return jsonify(ret)


@flowProfile.route("/publish/task_info", methods=['GET', 'POST'])
@require_login()
def publish_task_info():
    if request.method == 'GET':
        flow_type = request.values.get('flow_type')
        task_name = request.values.get('task_name')
        ret = dict()
        data = Config.get_flow_info(flow_type, task_name)
        if data:
            ret['result'] = 1
            ret['data'] = data
        else:
            ret['result'] = -1
        return jsonify(ret)
    elif request.method == 'POST':
        data = request.json
        result = WorkflowTemplateService.mod_template(data)
        ret = dict()
        if result:
            Config.reload_config(data.get('type'))
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)


@flowProfile.route("/publish/flow", methods=['GET', 'PUT', 'POST'])
@require_login()
@make_paging("publishFlowList")
def publish_flow():
    if request.method == 'GET':
        query = request.values.get('query')
        order_by = request.values.get('order_by', 'create_at')
        order_desc = Util.jsbool2pybool(request.values.get('order_desc', 'true'))
        data = WorkflowService.list(query, list_all=True, order_by=order_by, order_desc=order_desc)
        return data
    elif request.method == 'PUT':
        flow_id = request.values.get('flow_id')
        flow_type = request.values.get('flow_type')
        creator_id = session.get('userId')
        flow_data_str = request.values.get('flow_data')
        instance_id = Workflow.new(flow_id, flow_type, flow_data_str=flow_data_str, creator_id=creator_id)
        ret = dict()
        if instance_id:
            ret['result'] = 1
            ret['data'] = instance_id
        else:
            ret['result'] = -1
        return jsonify(ret)
    elif request.method == 'POST':
        operator = request.values.get('operator', None)
        flow_id = request.values.get('flow_id')
        direction = request.values.get('direction')
        operator_id = session.get('userId')
        operator = request.values.get('operator')
        flow_data_change_str = request.values.get('flow_data_change')
        workflow = WorkflowService.get(flow_id)
        task_id = workflow.current_task_id
        task_info = Config.get_flow_info(workflow.type, workflow.current_task_type)
        direction_info = task_info.get('directions')
        direction_info.get(direction)
        ret = dict()
        ret['result'] = -1
        if direction_info.get(direction):
            prvgs = direction_info.get(direction).get("prvg")
            flag = 0
            if prvgs:
                for prvg in prvgs:
                    if WorkflowService.user_participated_in(task_id, operator_id, prvg):
                        flag = 1
                        break
            if flag == 1 or operator == 'admin':
                if flow_data_change_str:
                    result = Workflow.save_flow_data(flow_id, flow_data_change_str=flow_data_change_str)
                    if result:
                        ret['result'] = 1
                    else:
                        ret['result'] = -2
                if direction:
                    result = Workflow.go(flow_id, direction, operator_id=operator_id)
                    if result:
                        ret['result'] = 1
        return jsonify(ret)
    return "error", 400


@flowProfile.route("/publish/flow/<string:flow_id>", methods=['GET'])
@require_login()
def publish_flow_detail(flow_id):
    flow_info = WorkflowService.get(flow_id)
    if flow_info:
        task_list = [e.serialize() for e in flow_info.workflow_task_instances]
        return render_template("flow/publish/detail.html", flow_info=flow_info.serialize(), task_list=task_list)
    return "not found", 404
