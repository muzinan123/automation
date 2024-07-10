# -*- coding:utf-8 -*-

import datetime
from app.models import db
from app import app


# 用户
class User(db.Model):
    __bind_key__ = 'public'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(64))
    email = db.Column(db.String(64))
    real_name = db.Column(db.String(64))
    work_no = db.Column(db.String(64))
    phone = db.Column(db.String(50))
    sex = db.Column(db.String(10))
    token = db.Column(db.String(64))
    login_count = db.Column(db.Integer, default=0)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), default=app.config['DEFAULT_ROLE_ID'])
    role = db.relationship("Role", back_populates="users")
    department_id = db.Column(db.Integer)
    department = db.relationship("Department", uselist=False, foreign_keys='User.department_id',
                                 primaryjoin="User.department_id==Department.id")
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())
    modified_at = db.Column(db.DateTime, default=datetime.datetime.now(),onupdate=datetime.datetime.now())
    enabled = db.Column(db.Boolean, default=True)
    sync = db.Column(db.Boolean, default=True)

    def serialize(self):
        """Return object data in easily serializeable format"""
        department_name = '-'
        if self.department:
            department_name = self.department.name
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'real_name': self.real_name,
            'work_no': self.work_no,
            'phone': self.phone,
            'department_id': self.department_id,
            'department': department_name,
            'sex': self.sex,
            'login_count': self.login_count,
            'role_id': self.role_id,
            'role_name': self.role.name if self.role else None,
            'role_alias': self.role.alias if self.role else None,
            'created_at': datetime.datetime.strftime(self.created_at, '%Y-%m-%d %H:%M:%S'),
            'modified_at': datetime.datetime.strftime(self.modified_at, '%Y-%m-%d %H:%M:%S'),
            'enabled': self.enabled
        }

    def brief(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'real_name': self.real_name
        }
