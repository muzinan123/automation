# -*- coding:utf8 -*-

import time
import hashlib
import datetime
from sqlalchemy import desc, or_

from app.services.core.core_service import CoreService
from app.services.framework.recycle_service import RecycleService
from app.services.k8s_cluster_rds import K8SClusterRdsService
from app.services.k8s_cluster_service import K8SClusterService
from app.out.k8s_core_app import K8SCoreApp
from app.models.k8s_node import K8SNode
from app.models.k8s_cluster import K8SCluster
from app.models.k8s_app_cluster import K8SAppCluster
from app.models import db
from app.out.kubernetes_admin import KubernetesAdmin
from app.out.cmdb_aliyun import Aliyun
from app import app, root_logger, rds_logger


class K8SNodeService(object):

    @staticmethod
    def add_node(org, env, node_name, cluster_name, department_name, host_id, publicnetwork=False):
        try:
            exist_labels = dict()

            if org in app.config['K8S_ORG_RELATIONSHIP'].get('online'):
                prefix = 'com.zhonganonline'
            else:
                prefix = 'com.zhonganinfo'
            if publicnetwork:
                if not exist_labels.get('{}.publicnetwork'.format(prefix)) == 'true':
                    exist_labels['{}.publicnetwork'.format(prefix)] = 'true'
            if not exist_labels.get('{}.bizcluster'.format(prefix)) == cluster_name:
                exist_labels['{}.bizcluster'.format(prefix)] = cluster_name
            if not exist_labels.get('{}.env'.format(prefix)) == env:
                exist_labels['{}.env'.format(prefix)] = env
            if not exist_labels.get('{}.department'.format(prefix)) == department_name:
                exist_labels['{}.department'.format(prefix)] = department_name
            result = KubernetesAdmin.add_node_with_label(org, env, node_name, exist_labels)
            if not result:
                return False

            cluster_id = hashlib.md5(cluster_name + "@" + department_name + "@" + org + "@" + "@K8S").hexdigest()
            node_id = hashlib.md5(node_name + "@" + env + "@" + org + "@K8S").hexdigest()
            k = K8SNode(id=node_id, org=org, name=node_name, env=env, host_id=host_id, cluster_id=cluster_id,
                        ip=node_name, create_at=datetime.datetime.now())
            db.session.add(k)
            db.session.commit()
            # flag = K8SNodeService.modify_aliyun_rds_white_ip(cluster_name, env, org, node.get('ip'))
            # if not flag:
            #     return False
        except Exception, e:
            root_logger.exception("add_node error: %s", e)

    # 新增RDS白名单处理逻辑，新增时将相关的集群新增新地NODE节点
    @staticmethod
    def modify_aliyun_rds_white_ip(cluster_name, env, ip, platform):
        try:
            kc = K8SAppCluster.query.filter(K8SAppCluster.env == env, K8SAppCluster.cluster_name ==cluster_name
                                            ,K8SAppCluster.platform == platform).all()
            # 白名单组的名称
            plat = ''
            if platform == 'boom1':
                plat = 'b1'
            elif platform == 'boom3':
                plat = 'b3'
            cluster_name_str = cluster_name + '_' + env + '_' + plat
            if kc:
                for k in kc:
                    flag_rds, rds_list = K8SCoreApp.select_rds_by_app_name(k.app_id, k.app_name, 'rds', env, k.org)
                    if flag_rds and rds_list:
                        for rds in rds_list:
                            flag = K8SCoreApp.add_aliyun_rds_white_ip('append', rds, cluster_name_str, ip,
                                                                      'system', 'add_k8s_node')
                            rds_logger.info(
                                "K8SCoreApp.add_aliyun_rds_white_ip {} {} {} {} {}".format('append', rds,
                                                                                           cluster_name_str, ip,
                                                                                           'add_k8s_node'))
                            if flag == 1:
                                # 新增白名单组与IP的关系
                                K8SClusterRdsService.add_cluster_rds_ip(cluster_name_str, ip)
                                K8SClusterRdsService.add_cluster_rds(cluster_name_str, rds)
                                rds_logger.info("K8SClusterRdsService.add_cluster_rds_ip {} {}".format(cluster_name, ip))
            return True
        except Exception, e:
            rds_logger.info("K8SClusterRdsService.modify_aliyun_rds_white_ip error: %s", e)
            return False

    @staticmethod
    def check_existed(node_name, env, org):
        node_id = hashlib.md5(node_name + "@" + env + "@" + org + "@K8S").hexdigest()
        node = K8SNode.query.get(node_id)
        if node:
            return True

    @staticmethod
    def del_node(node_id, org, delete_by):
        try:
            node = K8SNode.query.get((node_id, org))
            if node:
                RecycleService.recycle(node, delete_by=delete_by, commit=False)
                db.session.delete(node)
                db.session.commit()
                return True
        except Exception, e:
            root_logger.exception("del_node error: %s", e)

    @staticmethod
    def mod_nodes(node_id, org, host_id):
        try:
            node = K8SNode.query.get((node_id, org))
            if node:
                node.host_id = host_id
                db.session.commit()
        except Exception, e:
            root_logger.exception("mod_node error: %s", e)

    @staticmethod
    def list_node(query, env, org, cluster_name, order_by="id", order_desc=None):
        cluster_id_list = list()
        if cluster_name:
            cluster_list = K8SCluster.query.filter(K8SCluster.name.like("%" + cluster_name + "%"))
            cluster_id_list = [e.id for e in cluster_list]
        result = K8SNode.query.filter(
            or_(K8SNode.id.like("%" + query + "%"), K8SNode.name.like("%" + query + "%"),
                K8SNode.ip.like("%" + query + "%")) if query is not None else "",
            (K8SNode.env.in_(env)) if env is not None else "",
            (K8SNode.org.in_(org)) if org is not None else "",
            (K8SNode.cluster_id.in_(cluster_id_list)) if cluster_name else ""
        ).order_by(
            desc(eval('K8SNode.' + order_by)) if order_desc else (eval('K8SNode.' + order_by)))
        return result

    @staticmethod
    def get_node(node_id):
        return K8SNode.query.get(node_id)

    @staticmethod
    def get_node_by_host_id(host_id):
        return K8SNode.query.filter(K8SNode.host_id == host_id).first()

    @staticmethod
    def sync_node():
        for org_env in app.config.get('K8S_ORG_ENV'):
            org = org_env.get('org')
            env_list = org_env.get('env')
            for env in env_list:
                node_list = KubernetesAdmin.list_nodes(org, env)
                if node_list:
                    K8SNode.query.filter(K8SNode.org == org, K8SNode.env == env).update(dict(sync=False))
                    for node in node_list:
                        # v3
                        cluster_name = node.get('bizcluster')
                        department_name = node.get('department')
                        if not cluster_name:
                            # v2
                            if org in app.config['K8S_ORG_RELATIONSHIP'].get('tech'):
                                labels = node.get('labels')
                                if labels:
                                    cluster_name = labels.get('com.zhonganinfo.bizcluster')
                                    department_name = labels.get('com.zhonganinfo.department')
                            elif org in app.config['K8S_ORG_RELATIONSHIP'].get('online'):
                                labels = node.get('labels')
                                if labels:
                                    cluster_name = labels.get('com.zhonganonline.bizcluster')
                                    department_name = labels.get('com.zhonganonline.department')
                        cluster_id = None
                        if cluster_name and department_name:
                            cluster_id = hashlib.md5(cluster_name + "@" + department_name + "@" + org + "@K8S").hexdigest()
                            k8s_cluster = K8SCluster.query.get(cluster_id)
                            if not k8s_cluster:
                                continue
                        node_id = hashlib.md5(node['name'] + "@" + env + "@" + org + "@K8S").hexdigest()
                        if node.get('creationTimestamp'):
                            create_time = datetime.datetime.strptime(node['creationTimestamp'], '%Y-%m-%d %H:%M:%S')
                        else:
                            create_time = datetime.datetime.strptime(node['create_at'], '%Y-%m-%d %H:%M:%S')
                        ip = node.get('ip')
                        if not ip:
                            ip = node.get('name')
                        k = K8SNode(id=node_id, org=org, name=node['name'], env=env, cluster_id=cluster_id, ip=ip,
                                    pod_cidr=node.get('pod_cidr'), cpu=node['cpu'], memory=node['memory'],
                                    create_at=create_time, sync=True)
                        db.session.merge(k)
        db.session.flush()
        node_old_list = K8SNode.query.filter(K8SNode.sync == False)
        for node_old in node_old_list:
            RecycleService.recycle(node_old, commit=False)
            db.session.delete(node_old)
        db.session.commit()

    @staticmethod
    def sync_info_from_ecs():
        node_list = K8SNode.query.filter(K8SNode.host_id == None, K8SNode.ip != None)
        for node in node_list:
            info = Aliyun.find_ecs_by_ip(node.ip)
            if info and info.get('instance_id'):
                node.host_id = info.get('instance_id')
        db.session.commit()

    @staticmethod
    def get_docker_nodes(cluster_id, env):
        return K8SNode.query.filter(K8SNode.cluster_id == cluster_id, K8SNode.env == env).all()

    @staticmethod
    def get_node_by_res_id(res_id):
        return K8SNode.query.filter(K8SNode.host_id == res_id).first()

    @staticmethod
    def get_cluster_name_by_ip(ip):
        result = K8SNode.query.filter(K8SNode.ip == ip).first()
        if result:
            res = K8SCluster.query.filter(K8SCluster.id == result.cluster_id).first()
            return res
        else:
            return ''