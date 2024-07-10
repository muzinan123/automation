# -*- coding:utf-8 -*-

import datetime

from app.models import db
from app import app

table_name_prefix = app.config.get('TABLE_NAME_PREFIX', '')


class DiamondVersion(db.Model):
    __bind_key__ = 'main'
    __tablename__ = '{}_diamond_version'.format(table_name_prefix)
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    data_id = db.Column(db.String(128), primary_key=True)
    env = db.Column(db.String(16), primary_key=True)
    version = db.Column(db.Integer)
    create_at = db.Column(db.DateTime(), default=datetime.datetime.now())
    modify_at = db.Column(db.DateTime(), default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    creator = db.Column(db.String(64))
    modifier = db.Column(db.String(64))

    def serialize(self):
        return {
            'data_id': self.data_id,
            'env': self.env,
            'version': self.version,
            'create_at': datetime.datetime.strftime(self.create_at, '%Y-%m-%d %H:%M:%S'),
            'modify_at': datetime.datetime.strftime(self.modify_at, '%Y-%m-%d %H:%M:%S'),
            'creator': self.creator,
            'modifier': self.modifier
        }
