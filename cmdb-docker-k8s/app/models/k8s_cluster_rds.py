# -*- coding:utf8 -*-

import datetime
from app.models import db


class K8SClusterRds(db.Model):
    __tablename__ = 'k8s_cluster_rds'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    cluster_name = db.Column(db.String(255), primary_key=True)
    rds_id = db.Column(db.String(64), primary_key=True)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now())

    def serialize(self):
        ret = {
            'cluster_name': self.cluster_name,
            'rds_id': self.rds_id
        }
        return ret
