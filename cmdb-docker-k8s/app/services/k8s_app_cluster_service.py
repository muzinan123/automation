# -*- coding:utf8 -*-

import datetime
from app.models.k8s_app_cluster import K8SAppCluster
from app.models.k8s_cluster_rds_ip import K8SClusterRdsIP
from app.models import db
from app import app, root_logger


class K8SAppClusterService(object):

    @staticmethod
    def add_app_cluster(app_name, env, cluster_name, platform, is_new):
        try:
            e = K8SAppCluster(app_name=app_name, env=env, cluster_name=cluster_name, platform=platform, is_new=is_new)
            db.session.merge(e)
            db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("add_app_cluster error: %s", e)

    @staticmethod
    def select_app_cluster(app_id, env, cluster_name, platform, is_new):
        try:
            result = K8SAppCluster.query.filter(K8SAppCluster.env == env if env is not None else "",
                                                K8SAppCluster.cluster_name == cluster_name if cluster_name is not None else "",
                                                K8SAppCluster.platform == platform if platform is not None else "",
                                                K8SAppCluster.is_new == is_new if is_new is not None else "",
                                                K8SAppCluster.app_id == app_id).all()
            return result
        except Exception, e:
            root_logger.exception("select_app_cluster error: %s", e)

    @staticmethod
    def select_un_app_cluster(app_id, app_name, env, cluster_name, platform, is_new):
        try:
            result = K8SAppCluster.query.filter(K8SAppCluster.app_name == app_name if app_name is not None else "",
                                                K8SAppCluster.env == env if env is not None else "",
                                                K8SAppCluster.cluster_name != cluster_name if cluster_name is not None else "",
                                                K8SAppCluster.platform == platform if platform is not None else "",
                                                K8SAppCluster.is_new == is_new if is_new is not None else "",
                                                K8SAppCluster.app_id == app_id).first()
            return result
        except Exception, e:
            root_logger.exception("select_un_app_cluster error: %s", e)

    @staticmethod
    def select_un_app_clusters(app_id, app_name, env, cluster_name, platform, is_new):
        try:
            result = K8SAppCluster.query.filter(K8SAppCluster.app_name == app_name if app_name is not None else "",
                                                K8SAppCluster.env == env if env is not None else "",
                                                K8SAppCluster.cluster_name != cluster_name if cluster_name is not None else "",
                                                K8SAppCluster.platform == platform if platform is not None else "",
                                                K8SAppCluster.is_new == is_new if is_new is not None else "",
                                                K8SAppCluster.app_id == app_id)
            return result
        except Exception, e:
            root_logger.exception("select_un_app_cluster error: %s", e)

    @staticmethod
    def select_un_app_name(app_id, env, cluster_name, platform):
        try:
            result = K8SAppCluster.query.filter(K8SAppCluster.env == env if env is not None else "",
                                                K8SAppCluster.cluster_name == cluster_name if cluster_name is not None else "",
                                                K8SAppCluster.platform == platform if platform is not None else "",
                                                K8SAppCluster.app_id != app_id).all()
            return result
        except Exception, e:
            root_logger.exception("select_un_app_cluster error: %s", e)

    @staticmethod
    def update_app_cluster(app_id, app_name, env, cluster_name, platform, is_new, org):
        try:
            e = K8SAppCluster(app_id=app_id, app_name=app_name, env=env, cluster_name=cluster_name, platform=platform,
                              is_new=is_new, org=org, create_at=datetime.datetime.now())
            db.session.merge(e)
            db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("select_un_app_cluster error: %s", e)

    @staticmethod
    def del_by_cluster_id(cluster_id):
        try:
            k8s_app = K8SAppCluster.query.filter(K8SAppCluster.cluster_id == cluster_id).all()
            if k8s_app:
                for k in k8s_app:
                    db.session.delete(k)
                    db.session.flush()
                db.session.commit()
                return True
            else:
                return False
        except Exception, e:
            root_logger.exception("del_by_cluster_id error: %s", e)

    @staticmethod
    def del_app_cluster(app_id, app_name, env, cluster_name, platform, is_new):
        try:
            k8s_app = K8SAppCluster.query.filter(K8SAppCluster.app_id == app_id, K8SAppCluster.app_name == app_name, K8SAppCluster.env == env,
                                                 K8SAppCluster.cluster_name == cluster_name, K8SAppCluster.platform == platform,
                                                 K8SAppCluster.is_new == is_new).all()
            if k8s_app:
                for e in k8s_app:
                    db.session.delete(e)
                    db.session.flush()
                db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("del_app_cluster error: %s", e)
            return False

    @staticmethod
    def get_cluster_by_name(app_name, env, cluster_id):
        return K8SAppCluster.query.filter(K8SAppCluster.name == app_name, K8SAppCluster.env == env,
                                          K8SAppCluster.cluster_id == cluster_id).first()

    @staticmethod
    def get_cluster_name(ip):
        return K8SClusterRdsIP.query.filter(K8SClusterRdsIP.ip == ip)
