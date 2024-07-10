# -*- coding:utf8 -*-

from flask import Blueprint, jsonify, render_template, request, session, make_response, url_for

from app.decorators.access_controle import require_login, privilege
from app.decorators.paginate import make_paging_mongo
from app.services.framework.kafka_service import KafkaService
from app.util import Util

kafkaProfile = Blueprint('kafkaProfile', __name__)


@kafkaProfile.route("/message/list", methods=['GET'])
@require_login()
def message_list():
    return render_template("framework/kafka-message-list.html")


@kafkaProfile.route("/messages", methods=['GET'])
@require_login()
@make_paging_mongo("messageList")
def messages():
    query = request.values.get('query', '')
    data_type = request.values.get('data_type', None)
    order_by = request.values.get('order_by', 'produce_at')
    order_desc = Util.jsbool2pybool(request.values.get('order_desc', 'true'))
    data = KafkaService.list_message(query, data_type, order_by, order_desc)
    return data


@kafkaProfile.route("/message/reproduce", methods=['POST'])
@require_login()
@privilege('duang_admin')
def reproduce():
    message_id = request.values.get('id')
    result = KafkaService.reproduce(message_id)
    ret = dict()
    if result:
        ret['result'] = 1
    else:
        ret['result'] = -1
    return jsonify(ret)


@kafkaProfile.route("/info", methods=['GET'])
@require_login()
@privilege('duang_admin')
def info():
    return render_template("framework/kafka-info.html")


@kafkaProfile.route("/info/show", methods=['GET'])
@require_login()
@privilege('duang_admin')
def info_show():
    data = KafkaService.get_kafka_info()
    ret = dict()
    if data:
        ret['result'] = 1
        ret['data'] = data
    else:
        ret['result'] = -1
    return jsonify(ret)
