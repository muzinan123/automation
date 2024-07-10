# -*- coding:utf-8 -*-

from app.models import db


class RolePrivilege(db.Model):
    __bind_key__ = 'public'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id'), primary_key=True)
    privilege_id = db.Column(db.Integer(), db.ForeignKey('privilege.id'), primary_key=True)
    role_name = db.Column(db.String(80))
    privilege_name = db.Column(db.String(80))
    rw = db.Column(db.Integer())
    role = db.relationship("Role", back_populates="privileges", uselist=False)
    privilege = db.relationship("Privilege", back_populates="roles", uselist=False)

    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'role_id': self.role_id,
            'role_name': self.role_name,
            'role_alias': self.role.alias,
            'privilege_id': self.privilege_id,
            'privilege_name': self.privilege_name,
            'privilege_alias': self.privilege.alias,
            'rw': self.rw
        }
