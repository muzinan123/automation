# -*- coding:utf8 -*-

import json
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, send_file, session
from app.services.k8s_cluster_service import K8SClusterService
from app.decorators.access_control import require_login, privilege
from app.decorators.paginate import make_paging
from app.util import Util
from app import app

k8sClusterProfile = Blueprint('k8sClusterProfile', __name__)


@app.route("/docker/k8s_cluster/detail", methods=['GET'])
@require_login()
@privilege('docker')
def k8s_cluster_detail():
    cluster_id = request.values.get('id')
    name = request.values.get('name')
    org = request.values.get('org')
    department_name = request.values.get('department_name')
    if cluster_id:
        base = K8SClusterService.get_cluster(cluster_id)
        if base:
            nodes = base.nodes
            return render_template('kubernetes/cluster-detail.html', title=u'Kubernetes Cluster', base=base.serialize(),
                                   nodes=[e.serialize() for e in nodes])
    if name and org and department_name:
        base = K8SClusterService.get_cluster_by_name(name, org, department_name)
        if base:
            nodes = base.nodes
            return render_template('kubernetes/cluster-detail.html', title=u'Kubernetes Cluster', base=base.serialize(),
                                   nodes=[e.serialize() for e in nodes])
    return 'error', 400


@app.route("/docker/k8s_cluster/list", methods=['GET'])
@require_login()
@privilege("docker")
def k8s_cluster_list():
    return render_template('kubernetes/cluster-list.html', title=u'Kubernetes Cluster')


@app.route("/docker/k8s_cluster", methods=['PUT', 'DELETE', 'POST', 'GET'])
@make_paging("clusterList")
@require_login()
@privilege("docker")
def k8s_cluster():
    if request.method == 'PUT':
        name = request.values.get('name')
        org = request.values.get('org')
        department_name = request.values.get('department_name')
        description = request.values.get('description')
        create_boom = request.values.get('create_boom') == 'true'
        result = K8SClusterService.add_cluster(name, org, department_name, description, creator=session.get('userId'), create_boom=create_boom)
        ret = dict()
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    elif request.method == 'DELETE':
        cluster_id = request.values.get('id')
        result = K8SClusterService.del_cluster(cluster_id, delete_by=session.get('userId'))
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
        data = K8SClusterService.list_cluster(query, order_by=order_by, order_desc=order_desc, org=org)
        return data


@app.route("/docker/k8s_cluster/export", methods=['GET'])
@privilege("docker")
def k8s_cluster_export():
    return "ok", 200
