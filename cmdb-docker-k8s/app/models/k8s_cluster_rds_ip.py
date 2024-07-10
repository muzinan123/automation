# -*- coding:utf8 -*-

from app.models import db


class K8SClusterRdsIP(db.Model):
    __tablename__ = 'k8s_cluster_rds_ip'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    cluster_name = db.Column(db.String(255), primary_key=True)
    ip = db.Column(db.String(32), primary_key=True)
    create_at = db.Column(db.DateTime)

    def serialize(self):
        ret = {
            'cluster_name': self.cluster_name,
            'ip': self.ip
        }
        return ret
