# -*- coding:utf-8 -*-

from flask import Blueprint, jsonify, request
from app.services.docker_engine_service import DockerEngineService
from app.services.docker_cluster_service import DockerClusterService
from app.services.k8s_cluster_service import K8SClusterService
from app.decorators.access_control import api
from app import app

coreApiProfile = Blueprint('coreApiProfile', __name__)


@app.route('/api/core/docker/engine/<string:engine_id>')
@api()
def api_core_docker_engine(engine_id):
    engine = DockerEngineService.get_engine(engine_id)
    ret = dict()
    if engine:
        ret['result'] = 1
        ret['data'] = engine.serialize()
    else:
        ret['result'] = -1
    return jsonify(ret)


@app.route('/api/core/docker/cluster/<string:cluster_id>')
@api()
def api_core_docker_cluster(cluster_id):
    cluster = DockerClusterService.get_cluster(cluster_id)
    ret = dict()
    if cluster:
        ret['result'] = 1
        ret['data'] = cluster.serialize()
    else:
        ret['result'] = -1
    return jsonify(ret)


@app.route("/api/core/kubernetes/cluster/<string:cluster_id>")
@api()
def api_core_kubernetes_cluster(cluster_id):
    cluster = K8SClusterService.get_cluster(cluster_id)
    ret = dict()
    if cluster:
        ret['result'] = 1
        ret['data'] = cluster.serialize()
    else:
        ret['result'] = -1
    return jsonify(ret)
