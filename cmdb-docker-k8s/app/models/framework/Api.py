# -*- coding:utf-8 -*-

import datetime
from app.models import db


class ApiACL(db.Model):
    __tablename__ = 'api_access_control_list'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer(), primary_key=True)
    app = db.Column(db.String(64))
    token = db.Column(db.String(128))
    ip = db.Column(db.String(32))
    api_name = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())
    creator = db.Column(db.String(80))
    enabled = db.Column(db.Boolean())

    def serialize(self):
        return {
            'id': self.id,
            'app': self.app,
            'token': self.token,
            'ip': self.ip,
            'api_name': self.api_name,
            'created_at': datetime.datetime.strftime(self.created_at, '%Y-%m-%d %H:%M:%S'),
            'creator': self.creator,
            'enabled': self.enabled
        }
