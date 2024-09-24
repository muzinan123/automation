# -*- coding:utf-8 -*-

import hashlib
from flask import Blueprint, jsonify, request

from app.services.docker_engine_service import DockerEngineService
from app.services.docker_cluster_service import DockerClusterService
from app.services.k8s_node_service import K8SNodeService
from app.services.k8s_cluster_service import K8SClusterService
from app.out.kubernetes_admin import KubernetesAdmin
from app.decorators.access_control import api
from app import app

apiProfile = Blueprint('apiProfile', __name__)


@app.route("/api/listAllClusterJSON.do", methods=['GET', 'POST'])
#@api()
def list_all_docker_cluster():
    # 根据环境env和公司company(ZA ZATECH)返回所有的docker clusters
    #  如果env和company全是None，默认为查找全部
    env = request.values.get('env', None)
    org = request.values.get('company', None)
    data = list()
    dockers = DockerClusterService.get_cluster_by_env_org(env, org)
    for docker in dockers:
        data.append(docker.name)
    return jsonify(data)


@app.route("/api/listDockerHostByClusterJSON.do", methods=['GET', 'POST'])
#@api()
def host_info_by_cluster():
    # 根据cluster env company查询docker主机信息
    # 查询条件全部为空时默认查找全部
    cluster = request.values.get('cluster', None)
    env = request.values.get('env', None)
    org = request.values.get('company', None)
    data = list()
    dockers = DockerClusterService.get_info_by_cluster(cluster, env, org)
    for item in dockers:
        for engine in item.engines:
            e = engine.serialize()
            dic = dict()
            dic['cluster'] = item.name
            dic['env'] = item.env.upper()
            dic['company'] = item.org
            dic['hostName'] = e.get('name')
            dic['hostIp'] = e.get('ip')
            dic['port'] = str(e.get('port'))
            dic['isDeleted'] = 'N'
            status = e.get('status')
            if status == 'healthy':
                status = 'Healthy'
            else:
                status = 'Unhealth'
            dic['status'] = status
            data.append(dic)
    return jsonify(data)


@app.route("/api/list_cluster_with_ecs", methods=['GET'])
@api()
def api_list_cluster_with_ecs():
    cluster_list = DockerClusterService.list_cluster(None)
    ret = list()
    for cluster in cluster_list:
        cluster_info = dict()
        cluster_info['id'] = cluster.id
        cluster_info['name'] = cluster.name
        cluster_info['org'] = cluster.org
        cluster_info['env'] = cluster.env
        cluster_info['engine'] = list()
        for engine in cluster.engines:
            engine_info = dict()
            engine_info['host_id'] = engine.host_id
            engine_info['ip'] = engine.ip
            cluster_info['engine'].append(engine_info)
        ret.append(cluster_info)
    return jsonify(ret)


@app.route("/api/list_k8s_cluster_with_ecs", methods=['GET'])
@api()
def api_list_k8s_cluster_with_ecs():
    cluster_list = K8SClusterService.list_cluster(None)
    ret = list()
    for cluster in cluster_list:
        cluster_info = dict()
        cluster_info['id'] = cluster.id
        cluster_info['name'] = cluster.name
        cluster_info['org'] = cluster.org
        cluster_info['env'] = cluster.env
        cluster_info['node'] = list()
        for node in cluster.nodes:
            node_info = dict()
            node_info['host_id'] = node.host_id
            node_info['ip'] = node.ip
            cluster_info['node'].append(node_info)
        ret.append(cluster_info)
    return jsonify(ret)


@app.route("/api/list_k8s_node", methods=['GET'])
@api()
def api_list_k8s_node():
    query = request.values.get('query')
    env = request.values.get('env')
    org = request.values.get('org')
    cluster_name = request.values.get('cluster_name')
    data = K8SNodeService.list_node(query, env, org, cluster_name)
    ret = dict()
    ret['result'] = 1
    ret['data'] = [e.api_serialize() for e in data]
    return jsonify(ret)


@app.route("/api/engine/add", methods=['PUT'])
@api()
def api_engine_add():
    ip = request.values.get('ip')
    port = request.values.get('port')
    host_id = request.values.get('host_id')
    existed = DockerEngineService.get_engine_by_host_id(host_id)
    if not existed:
        result = DockerEngineService.add_engine(ip, port, host_id)
    else:
        result = True
    ret = dict()
    if result:
        ret['result'] = 1
        return jsonify(ret)
    else:
        ret['result'] = -1
        return jsonify(ret)


@app.route("/api/k8s_node/add", methods=['PUT'])
@api()
def api_k8s_node_add():
    org = request.values.get('org')
    env = request.values.get('env')
    node_name = request.values.get('node_name')
    cluster_name = request.values.get('cluster_name')
    department_name = request.values.get('department_name')
    host_id = request.values.get('host_id')
    publicnetwork = request.values.get('publicnetwork') == 'true'
    is_existed = K8SNodeService.check_existed(node_name, env, org)
    ret = dict()
    if is_existed:
        ret['result'] = 1
    else:
        result = K8SNodeService.add_node(org, env, node_name, cluster_name, department_name, host_id, publicnetwork=publicnetwork)
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
    return jsonify(ret)


@app.route("/api/k8s_node/<string:org>/<string:env>/<string:name>/verify_env", methods=['GET'])
def api_k8s_node_verify_env(org, env, name):
    node = KubernetesAdmin.get_node_info(org, env, name)
    if node:
        return str(1)
    else:
        return str(0)


@app.route("/api/k8s_node/<string:org>/<string:env>/<string:name>/verify_bizcluster/<string:bizcluster>", methods=['GET'])
def api_k8s_node_verify_bizcluster(org, env, name, bizcluster):
    node = KubernetesAdmin.get_node_info(org, env, name)
    if node:
        # v3
        cluster_name = node.get('bizcluster')
        if not cluster_name:
            # v2
            if org == 'ZATECH':
                cluster_name = node['labels'].get('com.zhonganinfo.bizcluster')
            elif org == 'ZA':
                cluster_name = node['labels'].get('com.zhonganonline.bizcluster')
        if cluster_name and cluster_name == bizcluster:
            return str(1)
        else:
            return str(0)
    else:
        return str(0)
