# -*- coding:utf-8 -*-

import datetime
from app.models import db


class DockerCluster(db.Model):
    __tablename__ = 'docker_cluster'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.String(32), primary_key=True)
    name = db.Column(db.String(64))
    org = db.Column(db.String(16))
    env = db.Column(db.String(8))
    create_at = db.Column(db.DateTime)
    creator = db.Column(db.String(64))
    sync = db.Column(db.Boolean(), default=True)
    core_sync = db.Column(db.Boolean(), default=False)

    engines = db.relationship('DockerEngine', foreign_keys='DockerEngine.cluster_name',
                              primaryjoin='and_(DockerEngine.cluster_name==DockerCluster.name, DockerEngine.'
                                          'org==DockerCluster.org, '
                                          'DockerEngine.env==DockerCluster.env)')

    def serialize(self):
        engine_list = list()
        for engine in self.engines:
            engine_list.append(engine.serialize())
        return {
            'id': self.id,
            'name': self.name,
            'org': self.org,
            'env': self.env,
            'create_at': datetime.datetime.strftime(self.create_at, '%Y-%m-%d %H:%M:%S') if self.create_at else "-",
            'creator': self.creator,
            'sync': self.sync,
            'core_sync': self.core_sync,
            'engines': engine_list
        }
