# -*- coding:utf-8 -*-

import datetime

from app.services.flow.config import Config
from app.models import db
from app import app

table_name_prefix = app.config.get('TABLE_NAME_PREFIX', '')


class WorkFlowInstance(db.Model):
    __bind_key__ = 'main'
    __tablename__ = '{}_workflow_instance'.format(table_name_prefix)
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.String(32), primary_key=True)
    type = db.Column(db.String(32))
    init_task_id = db.Column(db.Integer())
    current_task_type = db.Column(db.String(64))
    current_task_id = db.Column(db.Integer())
    current_task = db.relationship('WorkFlowTaskInstance', foreign_keys='WorkFlowInstance.current_task_id', uselist=False,
                                   primaryjoin="WorkFlowInstance.current_task_id==WorkFlowTaskInstance.id")
    create_at = db.Column(db.DateTime(), default=datetime.datetime.now())
    modify_at = db.Column(db.DateTime(), default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    workflow_task_instances = db.relationship('WorkFlowTaskInstance', foreign_keys='WorkFlowTaskInstance.workflow_instance_id', uselist=True,
                                              primaryjoin="WorkFlowTaskInstance.workflow_instance_id==WorkFlowInstance.id")

    def serialize(self):
        return {
            'id': self.id,
            'type': self.type,
            'current_task_type': self.current_task_type,
            'current_task_id': self.current_task_id,
            'create_at': datetime.datetime.strftime(self.create_at, '%Y-%m-%d %H:%M:%S'),
            'modify_at': datetime.datetime.strftime(self.modify_at, '%Y-%m-%d %H:%M:%S'),
            'current_flow_info': Config.get_flow_info(self.type, self.current_task_type)
        }


class WorkFlowTaskInstance(db.Model):
    __bind_key__ = 'main'
    __tablename__ = '{}_workflow_task_instance'.format(table_name_prefix)
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer(), primary_key=True)
    workflow_instance_id = db.Column(db.String(32))
    workflow_instance = db.relationship('WorkFlowInstance', foreign_keys='WorkFlowTaskInstance.workflow_instance_id', uselist=False,
                                        primaryjoin="WorkFlowTaskInstance.workflow_instance_id==WorkFlowInstance.id")
    workflow_type = db.Column(db.String(32))
    type = db.Column(db.String(32))
    go = db.Column(db.String(32))
    creator_id = db.Column(db.String(64))
    modifier_id = db.Column(db.String(64))
    create_at = db.Column(db.DateTime(), default=datetime.datetime.now())
    modify_at = db.Column(db.DateTime(), default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    participants = db.relationship('TaskParticipant', foreign_keys='TaskParticipant.task_instance_id',
                                   primaryjoin="and_(TaskParticipant.task_instance_id == WorkFlowTaskInstance.id, TaskParticipant.active==True)")

    def serialize(self):
        return {
            'id': self.id,
            'workflow_instance_id': self.workflow_instance_id,
            'workflow_type': self.workflow_type,
            'type': self.type,
            'go': self.go,
            'create_at': datetime.datetime.strftime(self.create_at, '%Y-%m-%d %H:%M:%S'),
            'modify_at': datetime.datetime.strftime(self.modify_at, '%Y-%m-%d %H:%M:%S'),
        }


class TaskParticipant(db.Model):
    __bind_key__ = 'main'
    __tablename__ = '{}_workflow_task_participant'.format(table_name_prefix)
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer(), primary_key=True)
    task_instance_id = db.Column(db.Integer())
    task_instance = db.relationship('WorkFlowTaskInstance', foreign_keys='TaskParticipant.task_instance_id', uselist=False,
                                    primaryjoin="TaskParticipant.task_instance_id==WorkFlowTaskInstance.id")
    workflow_instance_id = db.Column(db.String(32))
    workflow_type = db.Column(db.String(32))
    task_type = db.Column(db.String(32))
    user_id = db.Column(db.String(64))
    user = db.relationship('User', foreign_keys='TaskParticipant.user_id', uselist=False,
                           primaryjoin="TaskParticipant.user_id==User.id")
    privilege_name = db.Column(db.String(16))
    active = db.Column(db.Boolean())

    def serialize(self):
        return {
            'id': self.id,
            'task_instance_id': self.task_instance_id,
            'task_type': self.task_type,
            'privilege_name': self.privilege_name,
            'user_id': self.user.id,
            'user_name': self.user.name,
            'user_real_name': self.user.real_name
        }

    def brief(self):
        return {
            'privilege_name': self.privilege_name,
            'user_id': self.user.id,
            'user_name': self.user.name,
            'user_real_name': self.user.real_name
        }
