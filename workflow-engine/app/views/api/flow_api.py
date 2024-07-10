# -*- coding:utf8 -*-

from flask import Blueprint, request, session, jsonify, send_file, render_template

from app.decorators.access_controle import api
from app.services.flow.workflow import Workflow


flowApiProfile = Blueprint('flowApiProfile', __name__)


@flowApiProfile.route("/go", methods=['POST'])
@api()
def go():
    flow_id = request.values.get('flow_id')
    direction = request.values.get('direction')
    operator_id = request.values.get('operator_id', 'system')
    flow_data_change_str = request.values.get('flow_data_change')
    if flow_data_change_str:
        result = Workflow.save_flow_data(flow_id, flow_data_change_str=flow_data_change_str)
        if not result:
            ret = dict()
            ret['result'] = -2
            return jsonify(ret)
    result = Workflow.go(flow_id, direction, operator_id)
    ret = dict()
    if result:
        ret['result'] = 1
    else:
        ret['result'] = -1
    return jsonify(ret)
