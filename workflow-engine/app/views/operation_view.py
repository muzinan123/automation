# -*- coding:utf8 -*-

import time
import json

from flask import Blueprint, render_template, request, session, jsonify

from app.decorators.access_controle import require_login, ws_require_login, privilege
from app.decorators.paginate import make_paging_mongo
from app.services.operation.operation_service import OperationService
from app.services.operation.operation_template_service import OperationTemplateService
from app.services.operation.result_service import ResultService
from app.util import Util
from app import socketio

operationProfile = Blueprint('operationProfile', __name__)


@operationProfile.route("/result/list", methods=['GET'])
@require_login()
def result_list():
    return render_template('operation/result-list.html')


@operationProfile.route("/result", methods=['GET'])
@require_login()
@make_paging_mongo("resultList")
def result():
    query = request.values.get('query')
    operation_type = request.values.get('type')
    flow_id = request.values.get('flow_id')
    order_by = request.values.get('order_by', 'start_at')
    order_desc = Util.jsbool2pybool(request.values.get('order_desc', 'true'))
    data = OperationService.list_operation_result(query, operation_type=operation_type, flow_id=flow_id, order_by=order_by, order_desc=order_desc)
    return data


@operationProfile.route("/retry", methods=['POST'])
@require_login()
@privilege('pe')
def retry():
    opid = request.values.get('opid')
    o = OperationService.get_operation(opid)
    ret = dict()
    if o:
        operator_id = session['userId']
        kwargs = json.loads(o.get('params'))
        OperationService.run_operation.delay(o.get('type'), o.get('target'), o.get('app_name'), operator_id, **kwargs)
        ret['result'] = 1
    else:
        ret['result'] = -1
    return jsonify(ret)


@operationProfile.route("/result/detail", methods=['GET'])
@require_login()
def result_detail():
    operation_type = request.values.get('operation_type')
    opid = request.values.get('opid')
    data = ResultService.get_result_detail(operation_type, opid)
    ret = dict()
    ret['result'] = 1
    ret['data'] = data
    return jsonify(ret)


@operationProfile.route("/template/type", methods=['GET'])
@require_login()
def template_type():
    data = OperationTemplateService.list_template_type()
    ret = dict()
    ret['result'] = 1
    ret['data'] = data
    return jsonify(ret)


@operationProfile.route("/template", methods=['GET'])
@require_login()
def template():
    t_type = request.values.get('type')
    data = OperationTemplateService.list_template(t_type)
    ret = dict()
    ret['result'] = 1
    ret['data'] = data
    return jsonify(ret)


@socketio.on('get_result', namespace='/result')
@ws_require_login()
def ws_get_result(data):
    opid = data.get('opid')
    data = OperationService.get_operation_progress(opid)
    socketio.emit('result', data, namespace='/result')
