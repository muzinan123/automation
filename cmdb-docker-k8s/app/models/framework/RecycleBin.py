# -*- coding:utf-8 -*-

from app.models import db
import datetime


class RecycleBin(db.Model):
    __tablename__ = 'recycle_bin'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer(), primary_key=True)
    resource_type = db.Column(db.String(128))
    resource_content = db.Column(db.String(2000))
    delete_at = db.Column(db.DateTime(), default=datetime.datetime.now())
    delete_by = db.Column(db.String(64), default='system')

    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'resource_type': self.resource_type,
            'resource_content': self.resource_content,
            'delete_at': datetime.datetime.strftime(self.delete_at, '%Y-%m-%d %H:%M:%S'),
            'delete_by': self.delete_by
        }
