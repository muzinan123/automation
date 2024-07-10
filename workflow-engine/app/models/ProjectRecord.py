# -*- coding: utf-8 -*-
from app.models import db
import datetime


class ProjectRecord(db.Model):
    __bind_key__ = 'main'
    __tablename__ = 'project_record'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    operator_id = db.Column(db.String(32), nullable=False)
    operator = db.relationship("User", uselist=False, foreign_keys='ProjectRecord.operator_id',
                                 primaryjoin="ProjectRecord.operator_id==User.id")
    role = db.Column(db.String(64))  # 点击按钮对应的角色
    process = db.Column(db.String(64), nullable=False)  # 执行流程
    action = db.Column(db.String(64), nullable=False)  # 执行动作
    remark = db.Column(db.String(1024))
    gmt_created = db.Column(db.DateTime(), default=datetime.datetime.now())
    gmt_modified = db.Column(db.DateTime(), default=datetime.datetime.now(), onupdate=datetime.datetime.now())

    def serialize(self):
        operator = ''
        if self.operator:
            operator = self.operator.real_name
        return {
            'id': self.id,
            'project_id': self.project_id,
            'operator_id': self.operator_id,
            'operator': operator,
            'role': self.role,
            'process': self.process,
            'action': self.action,
            'remark': self.remark,
            'gmt_created': datetime.datetime.strftime(self.gmt_created, '%Y-%m-%d %H:%M:%S'),
            'gmt_modified': datetime.datetime.strftime(self.gmt_modified, '%Y-%m-%d %H:%M:%S'),
        }