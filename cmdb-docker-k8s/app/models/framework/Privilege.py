# -*- coding:utf-8 -*-

from app.models import db


# 权限
class Privilege(db.Model):
    __bind_key__ = 'public'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    alias = db.Column(db.String(255))
    roles = db.relationship('RolePrivilege', cascade='all, delete', lazy='dynamic')

    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'alias': self.alias
        }