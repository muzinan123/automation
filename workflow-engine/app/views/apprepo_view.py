# -*- coding:utf8 -*-

from flask import Blueprint, render_template, request, session, jsonify, make_response, send_from_directory

from app.decorators.access_controle import require_login
from app.services.apprepo_service import ApprepoService

appRepoProfile = Blueprint('appRepoProfile', __name__)


@appRepoProfile.route("/<int:app_id>/info", methods=['GET'])
@require_login()
def get_app_info(app_id):
    ret = dict()
    data = ApprepoService.get_app_info(app_id)
    if data:
        ret['result'] = 1
        ret['data'] = data
    else:
        ret['result'] = -1
    return jsonify(ret)


@appRepoProfile.route("/<int:app_id>/list_branch", methods=['GET'])
@require_login()
def list_branch(app_id):
    ret = dict()
    data = ApprepoService.list_branch(app_id, directory='branch')
    if data:
        ret['result'] = 1
        ret['data'] = data
    else:
        ret['result'] = -1
    return jsonify(ret)
