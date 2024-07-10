# -*- coding:utf8 -*-

import datetime
from app.models import db


class K8SAppClusterLog(db.Model):
    __tablename__ = 'k8s_app_cluster_log'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.BIGINT, primary_key=True, autoincrement=True)
    app_id = db.Column(db.BIGINT)
    app_name = db.Column(db.String(128))
    env = db.Column(db.String(16))
    cluster_name = db.Column(db.String(255))
    platform = db.Column(db.String(32))
    org = db.Column(db.String(32))
    type = db.Column(db.Integer)
    ips = db.Column(db.Text)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now())

    def serialize(self):
        ret = {
            'id': self.id,
            'app_id': self.app_id,
            'app_name': self.app_name,
            'env': self.env,
            'cluster_name': self.cluster_name,
            'platform': self.platform,
            'org': self.org,
            'type': self.type,
            'ips': self.ips,
            'create_at': datetime.datetime.strftime(self.create_at, '%Y-%m-%d %H:%M:%S') if self.create_at else "-"

        }
        return ret
