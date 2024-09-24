# -*- coding:utf-8 -*-

import datetime
from app.models import db


class LoginHistory(db.Model):
    __bind_key__ = 'public'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer, primary_key=True)
    login_at = db.Column(db.DateTime())
    name = db.Column(db.String(255))
    login_ip = db.Column(db.String(255))

    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'login_at': datetime.datetime.strftime(self.login_at, '%Y-%m-%d %H:%M:%S'),
            'name': self.name,
            'login_ip': self.login_ip
        }
