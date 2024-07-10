# -*- coding:utf8 -*-

import datetime
from app.models import db


class K8SAppCluster(db.Model):
    __tablename__ = 'k8s_app_cluster'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    app_id = db.Column(db.BIGINT, primary_key=True)
    app_name = db.Column(db.String(128))
    env = db.Column(db.String(16), primary_key=True)
    cluster_name = db.Column(db.String(255), primary_key=True)
    platform = db.Column(db.String(32), primary_key=True)
    create_at = db.Column(db.DateTime)
    is_new = db.Column(db.Boolean(), default=True)
    org = db.Column(db.String(32))

    def serialize(self):
        ret = {
            'app_id': self.app_id,
            'app_name': self.app_name,
            'env': self.env,
            'cluster_name': self.cluster_name,
            'platform': self.platform,
            'create_at': datetime.datetime.strftime(self.create_at, '%Y-%m-%d %H:%M:%S') if self.create_at else "-",
            'is_new': self.is_new,
            'org': self.org
        }
        return ret
