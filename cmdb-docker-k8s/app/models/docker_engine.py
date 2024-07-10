# -*- coding:utf-8 -*-

from app.out.docker_client import Docker
from app.models import db


class DockerEngine(db.Model):
    __tablename__ = 'docker_engine'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.String(64), primary_key=True)
    host_id = db.Column(db.String(64), unique=True)
    name = db.Column(db.String(128))
    ip = db.Column(db.String(16))
    port = db.Column(db.Integer())
    version = db.Column(db.String(16))
    cpu = db.Column(db.Integer())
    memory = db.Column(db.BigInteger())
    org = db.Column(db.String(16))
    env = db.Column(db.String(8))
    registry = db.Column(db.String(32))
    cluster_name = db.Column(db.String(32))
    cluster_store = db.Column(db.String(64))
    kernel_version = db.Column(db.String(32))
    sync = db.Column(db.Boolean(), default=True)
    core_sync = db.Column(db.Boolean(), default=False)

    cluster = db.relationship('DockerCluster', uselist=False, foreign_keys='DockerEngine.cluster_name',
                              primaryjoin='and_(DockerEngine.cluster_name==DockerCluster.name, DockerEngine.'
                                          'org==DockerCluster.org, '
                                          'DockerEngine.env==DockerCluster.env)')

    def serialize(self):
        ping = Docker.ping(self.ip, self.port)
        return {
            'id': self.id,
            'host_id': self.host_id,
            'name': self.name,
            'ip': self.ip,
            'port': self.port,
            'version': self.version,
            'cpu': self.cpu,
            'memory': self.memory,
            'org': self.org,
            'env': self.env,
            'registry': self.registry,
            'cluster_name': self.cluster_name,
            'cluster_store': self.cluster_store,
            'kernel_version': self.kernel_version,
            'sync': self.sync,
            'core_sync': self.core_sync,
            'status': 'healthy' if ping else 'unhealthy'
        }
