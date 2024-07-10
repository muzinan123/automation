# -*- coding:utf8 -*-

from app.models import db


class CoreUUIDMapping(db.Model):
    __bind_key__ = 'main'
    __tablename__ = 'core_uuid_mapping'
    res_id = db.Column(db.String(64), primary_key=True)
    res_type = db.Column(db.String(16), primary_key=True)
    res_uuid = db.Column(db.String(64), unique=True)

    def serialize(self):
        return {
            'res_id': self.res_id,
            'res_type': self.res_type,
            'res_uuid': self.res_uuid
        }
