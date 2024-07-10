# -*- coding:utf8 -*-

import json
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, send_file, session
from app.services.docker_cluster_service import DockerClusterService
from app.services.core.core_service import CoreService
from app.decorators.access_control import require_login, privilege
from app.decorators.paginate import make_paging
from app.out.docker_client import Docker
from app.util import Util
from app import app

clusterProfile = Blueprint('clusterProfile', __name__)


@app.route("/docker/cluster/detail", methods=['GET'])
@require_login()
@privilege('docker')
def docker_cluster_detail():
    cluster_id = request.values.get('id')
    name = request.values.get('name')
    org = request.values.get('org')
    env = request.values.get('env')
    if cluster_id:
        base = DockerClusterService.get_cluster(cluster_id)
        if base:
            engines = base.engines
            return render_template('docker/cluster-detail.html', title=u'Docker Cluster', base=base.serialize(),
                                   engines=[e.serialize() for e in engines])
    if name and org and env:
        base = DockerClusterService.get_cluster_by_name(name, org, env)
        if base:
            engines = base.engines
            return render_template('docker/cluster-detail.html', title=u'Docker Cluster', base=base.serialize(),
                                   engines=[e.serialize() for e in engines])
    return 'error', 400


@app.route("/docker/cluster/list", methods=['GET'])
@require_login()
@privilege("docker")
def docker_cluster_list():
    return render_template('docker/cluster-list.html', title=u'Docker Cluster')


@app.route("/docker/cluster", methods=['PUT', 'DELETE', 'POST', 'GET'])
@make_paging("clusterList")
@require_login()
@privilege("docker")
def docker_cluster():
    if request.method == 'PUT':
        name = request.values.get('name')
        org = request.values.get('org')
        env = request.values.get('env')
        result = DockerClusterService.add_cluster(name, org, env, creator=session.get('userId'))
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    elif request.method == 'DELETE':
        cluster_id = request.values.get('id')
        result = DockerClusterService.del_cluster(cluster_id, delete_by=session.get('userId'))
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
        org_str = request.values.get('org')
        org = None
        if org_str:
            org = org_str.split('+')
        data = DockerClusterService.list_cluster(query, order_by=order_by, order_desc=order_desc, org=org)
        return data


@app.route("/docker/cluster/export", methods=['GET'])
@privilege("docker")
def docker_cluster_export():
    return "ok", 200

