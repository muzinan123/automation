# -*- coding:utf8 -*-

import json
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, send_file
from app.services.docker_engine_service import DockerEngineService
from app.services.core.core_service import CoreService
from app.decorators.access_control import require_login, privilege
from app.decorators.paginate import make_paging
from app.out.docker_client import Docker
from app.util import Util
from app import app

engineProfile = Blueprint('engineProfile', __name__)


@app.route("/docker/engine/detail", methods=['GET'])
@require_login()
@privilege('docker')
def docker_engine_detail():
    engine_id = request.values.get('engine_id')
    host_id = request.values.get('host_id')
    if engine_id:
        base = DockerEngineService.get_engine(engine_id)
        if base:
            info = Docker.info(base.ip, base.port)
            images = Docker.list_image(base.ip, base.port)
            containers = Docker.list_container(base.ip, base.port)
            return render_template('docker/engine-detail.html', title=u'Docker Engine', base=base.serialize(),
                                   info=info, images=images, containers=containers)
    if host_id:
        base = DockerEngineService.get_engine_by_host_id(host_id)
        if base:
            info = Docker.info(base.ip, base.port)
            images = Docker.list_image(base.ip, base.port)
            containers = Docker.list_container(base.ip, base.port)
            return render_template('docker/engine-detail.html', title=u'Docker Engine', base=base.serialize(),
                                   info=info, images=images, containers=containers)
    return 'error', 400


@app.route("/docker/engine/list", methods=['GET'])
@require_login()
@privilege("docker")
def docker_engine_list():
    return render_template('docker/engine-list.html', title=u'Docker Engine')


@app.route("/docker/engine", methods=['PUT', 'DELETE', 'POST', 'GET'])
@make_paging("engineList")
@require_login()
@privilege("docker")
def docker_engine():
    if request.method == 'PUT':
        ip = request.values.get('ip')
        port = request.values.get('port')
        host_id = request.values.get('host_id')
        result = DockerEngineService.add_engine(ip, port, host_id)
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    elif request.method == 'DELETE':
        engine_id = request.values.get('id')
        result = DockerEngineService.del_engine(engine_id)
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    elif request.method == 'POST':
        engine_id = request.values.get('id')
        env = request.values.get('env')
        cluster_name = request.values.get('cluster_name')
        # 插入
        result = DockerEngineService.mod_engine(engine_id, env=env, cluster_name=cluster_name)
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    elif request.method == 'GET':
        query = request.values.get('query', '')
        order_by = request.values.get('order_by', 'id')
        order_desc = Util.jsbool2pybool(request.values.get('order_desc', 'true'))
        env_str = request.values.get('env')
        env = None
        if env_str:
            env = env_str.split('+')
        cluster_name = request.values.get('cluster_name')
        data = DockerEngineService.list_engine(query, env, cluster_name, order_by=order_by, order_desc=order_desc)
        return data


@app.route("/docker/engine/export", methods=['GET'])
@privilege("docker")
def docker_engine_export():
    return "ok", 200
