# -*- coding:utf-8 -*-

import datetime
from app.models import db


class Department(db.Model):
    __bind_key__ = 'public'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80))
    parent_id = db.Column(db.Integer())
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())
    modified_at = db.Column(db.DateTime, default=datetime.datetime.now(),
                            onupdate=datetime.datetime.now())
    enabled = db.Column(db.Boolean, default=True)

    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'created_at': datetime.datetime.strftime(self.created_at, '%Y-%m-%d %H:%M:%S'),
            'modified_at': datetime.datetime.strftime(self.modified_at, '%Y-%m-%d %H:%M:%S'),
            'enabled': self.enabled
        }
