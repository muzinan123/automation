# -*- coding:utf8 -*-

import datetime
from app.models import db


class K8SCluster(db.Model):
    __tablename__ = 'k8s_cluster'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.String(32), primary_key=True)
    name = db.Column(db.String(64))
    org = db.Column(db.String(16))
    department_name = db.Column(db.String(80))
    description = db.Column(db.String(128))
    create_at = db.Column(db.DateTime)
    creator = db.Column(db.String(64))
    nodes = db.relationship('K8SNode', foreign_keys='K8SNode.cluster_id',
                            primaryjoin='K8SNode.cluster_id==K8SCluster.id')
    sync = db.Column(db.Boolean(), default=True)
    core_sync = db.Column(db.Boolean(), default=False)

    def serialize(self, recurse=True):
        ret = {
            'id': self.id,
            'name': self.name,
            'org': self.org,
            'department_name': self.department_name,
            'description': self.description,
            'create_at': datetime.datetime.strftime(self.create_at, '%Y-%m-%d %H:%M:%S') if self.create_at else "-",
            'creator': self.creator,
        }
        if recurse:
            nodes = list()
            for node in self.nodes:
                nodes.append(node.serialize(recurse=False))
            ret['nodes'] = nodes
        return ret
