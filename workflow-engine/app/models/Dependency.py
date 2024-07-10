# -*- coding:utf-8 -*-

import datetime

from app.models import db
from app import app

table_name_prefix = app.config.get('TABLE_NAME_PREFIX', '')


class MavenDependency(db.Model):
    __bind_key__ = 'main'
    __tablename__ = '{}_maven_dependency'.format(table_name_prefix)
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    artifact_id = db.Column(db.String(128), primary_key=True)
    type = db.Column(db.String(16))
    version = db.Column(db.String(16))
    create_at = db.Column(db.DateTime(), default=datetime.datetime.now())
    modify_at = db.Column(db.DateTime(), default=datetime.datetime.now(), onupdate=datetime.datetime.now())

    def serialize(self):
        return {
            'artifact_id': self.artifact_id,
            'type': self.type,
            'version': self.version,
            'create_at': datetime.datetime.strftime(self.create_at, '%Y-%m-%d %H:%M:%S'),
            'modify_at': datetime.datetime.strftime(self.modify_at, '%Y-%m-%d %H:%M:%S'),
        }
