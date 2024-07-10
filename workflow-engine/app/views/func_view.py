# -*- coding:utf8 -*-

from flask import Blueprint, jsonify

from app.decorators.access_controle import require_login
from app.services.operation.pool import func_list

funcProfile = Blueprint('funcProfile', __name__)


@funcProfile.route("/list/func", methods=['GET'])
@require_login()
def list_func():
    return jsonify({e[0]: e[1] for e in func_list})



