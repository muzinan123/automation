# -*- coding:utf-8 -*-

import datetime
from app.models import db


class Notification(db.Model):
    __bind_key__ = 'public'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer(), primary_key=True)
    content = db.Column(db.String(128))
    type = db.Column(db.String(32))
    target_user_id = db.Column(db.String(64))
    target_user = db.relationship('User', foreign_keys='Notification.target_user_id',
                                  primaryjoin="Notification.target_user_id==User.id")
    readed = db.Column(db.Boolean(), default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(), index=True)
    modified_at = db.Column(db.DateTime, default=datetime.datetime.now(),onupdate=datetime.datetime.now())

    db.Index('idx_target_user_id_readed', target_user_id, readed)

    def serialize(self):
        return {
            'id' : self.id,
            'content': self.content,
            'type': self.type,
            'readed': self.readed,
            'created_at': datetime.datetime.strftime(self.created_at, '%Y-%m-%d %H:%M:%S'),
            'modified_at': datetime.datetime.strftime(self.modified_at, '%Y-%m-%d %H:%M:%S')
        }
