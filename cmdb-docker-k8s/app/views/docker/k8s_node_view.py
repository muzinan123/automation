# -*- coding:utf8 -*-

import json
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, send_file, session
from app.services.k8s_node_service import K8SNodeService
from app.services.core.core_service import CoreService
from app.decorators.access_control import require_login, privilege
from app.decorators.paginate import make_paging
from app.out.kubernetes_admin import KubernetesAdmin
from app.util import Util
from app import app

k8sNodeProfile = Blueprint('k8sNodeProfile', __name__)


@app.route("/docker/k8s_node/detail", methods=['GET'])
@require_login()
@privilege('docker')
def k8s_node_detail():
    node_id = request.values.get('node_id')
    host_id = request.values.get('host_id')
    if node_id:
        base = K8SNodeService.get_node(node_id)
        if base:
            info = KubernetesAdmin.get_node_info(base.org, base.env, base.name)
            pods = KubernetesAdmin.get_node_pods(base.org, base.env, base.name)
            return render_template('kubernetes/node-detail.html', title=u'Kubernetes Nodes', base=base.serialize(),
                                   info=info, pods=pods)
    if host_id:
        base = K8SNodeService.get_node_by_host_id(host_id)
        if base:
            info = KubernetesAdmin.get_node_info(base.org, base.env, base.name)
            pods = KubernetesAdmin.get_node_pods(base.org, base.env, base.name)
            return render_template('kubernetes/node-detail.html', title=u'Kubernetes Nodes', base=base.serialize(),
                                   info=info, pods=pods)
    return 'error', 400


@app.route("/docker/k8s_node/list", methods=['GET'])
@require_login()
@privilege("docker")
def k8s_node_list():
    return render_template('kubernetes/node-list.html', title=u'Kubernetes Nodes')


@app.route("/docker/k8s_node", methods=['DELETE', 'GET'])
@make_paging("nodeList")
@require_login()
@privilege("docker")
def k8s_node():
    if request.method == 'DELETE':
        node_id = request.values.get('id')
        org = request.values.get('org')
        result = K8SNodeService.del_node(node_id, org, session.get('userId'))
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
        org_str = request.values.get('org')
        org = None
        if org_str:
            org = org_str.split('+')
        cluster_name = request.values.get('cluster_name')
        data = K8SNodeService.list_node(query, env, org, cluster_name, order_by=order_by, order_desc=order_desc)
        return data


@app.route("/docker/k8s_node/export", methods=['GET'])
@privilege("docker")
def k8s_node_export():
    return "ok", 200
