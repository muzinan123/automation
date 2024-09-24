# -*- coding:utf8 -*-

import datetime
from app.models import db


class K8SNode(db.Model):
    __tablename__ = 'k8s_node'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.String(32), primary_key=True)
    org = db.Column(db.String(16))
    name = db.Column(db.String(64))
    env = db.Column(db.String(8))
    host_id = db.Column(db.String(64), unique=True)
    cluster_id = db.Column(db.String(32))
    cluster = db.relationship('K8SCluster', uselist=False, foreign_keys='K8SNode.cluster_id',
                              primaryjoin='K8SNode.cluster_id==K8SCluster.id')
    ip = db.Column(db.String(16))
    pod_cidr = db.Column(db.String(20))
    cpu = db.Column(db.String(16))
    memory = db.Column(db.String(16))
    create_at = db.Column(db.DateTime)
    sync = db.Column(db.Boolean(), default=True)

    def serialize(self, recurse=True):
        ret = {
            'id': self.id,
            'org': self.org,
            'name': self.name,
            'env': self.env,
            'host_id': self.host_id,
            'ip': self.ip,
            'pod_cidr': self.pod_cidr,
            'cpu': self.cpu,
            'memory': self.memory,
            'create_at': datetime.datetime.strftime(self.create_at, '%Y-%m-%d %H:%M:%S') if self.create_at else "-",
            'sync': self.sync
        }
        if recurse:
            cluster = dict()
            if self.cluster:
                cluster = self.cluster.serialize(recurse=False)
            ret['cluster'] = cluster
        return ret

    def api_serialize(self):
        ret = {
            'org': self.org,
            'name': self.name,
            'env': self.env,
            'host_id': self.host_id,
            'ip': self.ip,
            'pod_cidr': self.pod_cidr,
            'cpu': self.cpu,
            'memory': self.memory,
        }
        if self.cluster:
            ret['cluster_name'] = self.cluster.name
        return ret
