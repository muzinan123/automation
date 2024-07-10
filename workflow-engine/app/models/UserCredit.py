# -*- coding:utf-8 -*-

import datetime

from app.models import db


class UserCredit(db.Model):
    # 用户积分表
    __tablename__ = 'user_credit'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    user_id = db.Column(db.String(64), primary_key=True)  # wz00xxx
    credit = db.Column(db.Integer, default=0)
    modifier = db.Column(db.String(32), default='system')
    gmt_modified = db.Column(db.DateTime, default=datetime.datetime.now())
    user = db.relationship("User", uselist=False, foreign_keys='UserCredit.user_id', primaryjoin="UserCredit.user_id == User.id")

    def serialize(self):
        return {
            'user_id': self.user_id,
            'credit': self.credit,
            'modifier': self.modifier,
            'gmt_modified': datetime.datetime.strftime(self.gmt_modified, '%Y-%m-%d %H:%M:%S'),
            'user': self.user.brief()
        }


class UserCreditDetail(db.Model):
    __tablename__ = 'user_credit_detail'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64))  # wz00xxx
    project_id = db.Column(db.Integer)
    increment = db.Column(db.Integer, default=0)  # 加分 减分
    action = db.Column(db.String(64))
    modifier = db.Column(db.String(32), default='system')
    gmt_modified = db.Column(db.DateTime, default=datetime.datetime.now())


    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'increment': self.increment,
            'action': self.action,
            'modifier': self.modifier,
            'gmt_modified': datetime.datetime.strftime(self.gmt_modified, '%Y-%m-%d %H:%M:%S'),
        }