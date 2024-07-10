# -*- coding:utf8 -*-

import datetime
from app.models.k8s_cluster_rds import K8SClusterRds
from app.models.k8s_cluster_rds_ip import K8SClusterRdsIP
from app.models import db
from app.out.k8s_core_app import K8SCoreApp
from app import rds_logger


class K8SClusterRdsService(object):

    @staticmethod
    def check_count(rds_id):
        try:
            count = K8SCoreApp.get_aliyun_rds_white_groups(rds_id)
            rds_logger.info("K8SCoreApp.get_aliyun_rds_white_groups {} {}".format(rds_id, count))
            if count < 50:
                return True
            else:
                return False
        except Exception, e:
            rds_logger.exception("check_count error: %s", e)

    @staticmethod
    def del_cluster_rds(cluster_name, rds_id):
        try:
            k8s_app = K8SClusterRds.query.filter(K8SClusterRds.cluster_name == cluster_name,
                                                 K8SClusterRds.rds_id == rds_id).first()
            if k8s_app:
                db.session.delete(k8s_app)
                db.session.commit()
                return True
            else:
                return False
        except Exception, e:
            rds_logger.exception("del_cluster_rds error: %s", e)

    @staticmethod
    def add_cluster_rds(cluster_name, rds_id):
        try:
            e = K8SClusterRds(cluster_name=cluster_name, rds_id=rds_id, create_at=datetime.datetime.now())
            db.session.merge(e)
            db.session.commit()
            return True
        except Exception, e:
            rds_logger.exception("add_cluster_rds error: %s", e)

    @staticmethod
    def list_cluster_rds(cluster_name, rds_id):
        aa = K8SClusterRds.query.filter(K8SClusterRds.cluster_name == cluster_name if cluster_name else "",
                                        K8SClusterRds.rds_id == rds_id if rds_id else "")
        return aa

    @staticmethod
    def add_cluster_rds_ip(cluster_name, ip):
        try:
            e = K8SClusterRdsIP(cluster_name=cluster_name, ip=ip, create_at=datetime.datetime.now())
            db.session.merge(e)
            db.session.commit()
            return True
        except Exception, e:
            rds_logger.exception("add_cluster_rds_ip error: %s", e)

    @staticmethod
    def del_cluster_rds_ip(cluster_name, ip):
        try:
            e = K8SClusterRdsIP.query.filter(K8SClusterRdsIP.cluster_name == cluster_name,
                                             K8SClusterRdsIP.ip == ip).first()
            if e:
                count = K8SClusterRdsIP.query.filter(K8SClusterRdsIP.cluster_name == cluster_name).count()
                if count == 1:
                    re = K8SClusterRds.query.filter(K8SClusterRds.cluster_name == cluster_name).all()
                    for r in re:
                        db.session.delete(r)
                db.session.delete(e)
                db.session.commit()
                return True
            else:
                return False
        except Exception, e:
            rds_logger.exception("del_cluster_rds_ip error: %s", e)

    @staticmethod
    def list_cluster_rds_ip(cluster_name, ip):
        aa = K8SClusterRdsIP.query.filter(K8SClusterRdsIP.cluster_name == cluster_name if cluster_name else "",
                                          K8SClusterRdsIP.ip == ip if ip else "")
        return aa

    @staticmethod
    def get_cluster_rds_list_by_name(cluster_name):
        return K8SClusterRds.query.filter(K8SClusterRds.cluster_name == cluster_name).all()

    @staticmethod
    def get_cluster_rds_ip_list(cluster_name):
        return K8SClusterRdsIP.query.filter(K8SClusterRdsIP.cluster_name == cluster_name).all()