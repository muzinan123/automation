# -*- coding:utf8 -*-

import datetime
import hashlib
from sqlalchemy import desc

from app.services.core.core_service import CoreService
from app.services.framework.recycle_service import RecycleService
from app.models.k8s_cluster import K8SCluster
from app.models import db
from app.out.kubernetes_admin import KubernetesAdmin
from app import app, root_logger


class K8SClusterService(object):

    @staticmethod
    def add_cluster(name, org, department_name, description, creator='system', create_boom=False):
        try:
            if create_boom:
                is_existed = KubernetesAdmin.get_group(org, department_name)
                if not is_existed:
                    result = KubernetesAdmin.add_group(org, department_name, department_name)
                    if not result:
                        return False
                    # Boom3 默认会在创建新Group时，创建一个同名的bizcluster
                    if department_name != name:
                        result = KubernetesAdmin.add_bizcluster(org, department_name, name, description)
                        if not result:
                            return False
                else:
                    result = KubernetesAdmin.add_bizcluster(org, department_name, name, description)
                    if not result:
                        return False
            cluster_id = hashlib.md5(name + "@" + department_name + "@" + org + "@K8S").hexdigest()
            r = K8SCluster(id=cluster_id, name=name, org=org, department_name=department_name, description=description,
                           create_at=datetime.datetime.now(), creator=creator, core_sync=1)
            db.session.add(r)
            db.session.flush()
            if CoreService.register(cluster_id, "true", name + "@" + department_name + "@" + org + "@K8S", ["k8s_cluster"], "k8s_cluster"):
                db.session.commit()
                return True
        except Exception, e:
            root_logger.exception("add_cluster error: %s", e)

    @staticmethod
    def check_exist(name, org, department_name):
        r = K8SCluster.query.filter(K8SCluster.name == name, K8SCluster.org == org,
                                    K8SCluster.department_name == department_name).first()
        if r:
            return True

    @staticmethod
    def del_cluster(cluster_id, delete_by='system'):
        try:
            r = K8SCluster.query.get(cluster_id)
            if CoreService.unregister(cluster_id, 'k8s_cluster'):
                RecycleService.recycle(r, delete_by=delete_by, commit=False)
                db.session.delete(r)
                db.session.commit()
                return True
        except Exception, e:
            root_logger.exception("del_cluster error: %s", e)

    @staticmethod
    def list_cluster(query, order_by='id', order_desc=None, org=None, department_name=None):
        result = K8SCluster.query.filter(
            K8SCluster.name.like("%" + query + "%") if query else "",
            K8SCluster.org.in_(org) if org is not None else "",
            K8SCluster.department_name.like("%" + department_name + "%") if department_name else ""
        ).order_by(desc(eval('K8SCluster.' + order_by)) if order_desc else (eval('K8SCluster.' + order_by)))
        return result

    @staticmethod
    def get_cluster(cluster_id):
        return K8SCluster.query.get(cluster_id)

    @staticmethod
    def get_cluster_by_name(name, org, department_name):
        return K8SCluster.query.filter(K8SCluster.name == name, K8SCluster.org == org,
                                       K8SCluster.department_name == department_name).first()

    @staticmethod
    def sync_cluster():
        for org_env in app.config.get('K8S_ORG_ENV'):
            org = org_env.get('org')
            group_list = KubernetesAdmin.list_group(org)
            for g in group_list:
                group = g.get('group')
                cluster_list = KubernetesAdmin.list_group_bizcluster(org, group)
                if cluster_list:
                    K8SCluster.query.filter(K8SCluster.org == org, K8SCluster.department_name == group).update(dict(sync=False))
                    for one in cluster_list:
                        cluster_id = hashlib.md5(one.get('bizcluster') + "@" + group + "@" + org + "@K8S").hexdigest()
                        k = K8SCluster(id=cluster_id, name=one.get('bizcluster'), org=org, department_name=group,
                                       description=one.get('description'), sync=1)
                        db.session.merge(k)
        db.session.flush()
        cluster_new_list = K8SCluster.query.filter(K8SCluster.core_sync == False)
        for cluster_new in cluster_new_list:
            if CoreService.register(cluster_new.id, "true",
                                    cluster_new.name + "@" + cluster_new.department_name + "@" + cluster_new.org + "@K8S",
                                    ['k8s_cluster'], 'k8s_cluster'):
                cluster_new.core_sync = True
        db.session.commit()
        cluster_old_list = K8SCluster.query.filter(K8SCluster.sync == False)
        for cluster_old in cluster_old_list:
            CoreService.unregister(cluster_old.id, 'k8s_cluster')
            RecycleService.recycle(cluster_old, commit=False)
            db.session.delete(cluster_old)
        db.session.commit()

    @staticmethod
    def get_cluster_id(cluster_name, org):
        return K8SCluster.query.filter(K8SCluster.org == org, K8SCluster.name == cluster_name).first()