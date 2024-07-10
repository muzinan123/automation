# -*- coding: utf-8 -*-
from app.models import db
import datetime


class Project(db.Model):
    __bind_key__ = 'main'
    __tablename__ = 'project'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    alias = db.Column(db.String(64))
    type = db.Column(db.String(64))
    company_id = db.Column(db.Integer)
    company_code = db.Column(db.String(64))
    company_label = db.Column(db.String(128))
    dept_id = db.Column(db.Integer)
    dept_code = db.Column(db.String(64))
    dept_label = db.Column(db.String(128))
    product_id = db.Column(db.Integer)
    product_code = db.Column(db.String(64))
    product_label = db.Column(db.String(128))
    system_id = db.Column(db.Integer)
    summary = db.Column(db.String(1024))
    owner_id = db.Column(db.String(64), nullable=False)
    owner = db.relationship("User", foreign_keys='Project.owner_id', uselist=False,
                            primaryjoin="Project.owner_id==User.id")
    ba_id = db.Column(db.String(64))
    ba = db.relationship("User", foreign_keys='Project.ba_id', uselist=False,
                         primaryjoin="Project.ba_id==User.id")
    begin_date = db.Column(db.Date, default=datetime.date.today())
    expect_publish_date = db.Column(db.Date)
    completed_date = db.Column(db.DateTime())
    sql_script_url = db.Column(db.String(256))
    gmt_created = db.Column(db.DateTime(), default=datetime.datetime.now())
    gmt_modified = db.Column(db.DateTime(), default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    creator = db.Column(db.String(32), default='system')
    modifier = db.Column(db.String(32), default='system')
    is_deleted = db.Column(db.String(2), default='N')
    jira_issue_id = db.Column(db.Integer, default=0)
    jira_issue_key = db.Column(db.String(64), default='')
    jira_version_id = db.Column(db.Integer, default=0)
    jira_project_key = db.Column(db.String(16))
    regulator_id = db.Column(db.String(64))
    code_review_status = db.Column(db.SmallInteger, default=0)
    sql_review_status = db.Column(db.SmallInteger, default=0)
    data_review_status = db.Column(db.SmallInteger, default=99)
    test_status = db.Column(db.SmallInteger, default=0)
    publish_status = db.Column(db.SmallInteger, default=0)
    demand_review_status = db.Column(db.SmallInteger, default=2)
    times = db.Column(db.Integer, default=0) # 第几次发布
    qa_list = db.relationship("ProjectParticipant", foreign_keys='ProjectParticipant.project_id', uselist=True,
                              primaryjoin="and_(ProjectParticipant.project_id == Project.id, ProjectParticipant.privilege_name.in_(['qa', 'sqa']))")
    dev_list = db.relationship("ProjectParticipant", foreign_keys='ProjectParticipant.project_id', uselist=True,
                               primaryjoin="and_(ProjectParticipant.project_id == Project.id, ProjectParticipant.privilege_name=='dev')")
    code_review_list = db.relationship("ProjectParticipant", foreign_keys='ProjectParticipant.project_id', uselist=True,
                                       primaryjoin="and_(ProjectParticipant.project_id == Project.id, ProjectParticipant.privilege_name=='code_review')")

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'alias': self.alias,
            'type': self.type,
            'company_id': self.company_id,
            'company_code': self.company_code,
            'company_label': self.company_label,
            'dept_id': self.dept_id,
            'dept_code': self.dept_code,
            'dept_label': self.dept_label,
            'product_id': self.product_id,
            'product_code': self.product_code,
            'product_label': self.product_label,
            'system_id': self.system_id,
            'summary': self.summary,
            'owner_id': self.owner_id,
            'owner': self.owner.brief() if self.owner else {},
            'ba_id': self.ba_id,
            'ba': self.ba.brief() if self.ba else {},
            'begin_date': datetime.date.strftime(self.begin_date, '%Y-%m-%d') if self.begin_date else "",
            'expect_publish_date': datetime.date.strftime(self.expect_publish_date, '%Y-%m-%d') if self.expect_publish_date else "",
            'completed_date': datetime.datetime.strftime(self.completed_date, '%Y-%m-%d %H:%M:%S') if self.completed_date else "",
            'sql_script_url': self.sql_script_url,
            'jira_issue_id': self.jira_issue_id,
            'jira_issue_key': self.jira_issue_key,
            'jira_version_id': self.jira_version_id,
            'jira_project_key': self.jira_project_key,
            'regulator_id': self.regulator_id,
            'demand_review_status': self.demand_review_status,
            'code_review_status': self.code_review_status,
            'sql_review_status': self.sql_review_status,
            'data_review_status': self.data_review_status,
            'test_status': self.test_status,
            'publish_status': self.publish_status,
            'times': self.times,
            'qa_list': [e.participant.brief() for e in self.qa_list],
            'dev_list': [e.participant.brief() for e in self.dev_list],
            'code_review_list': [e.participant.brief() for e in self.code_review_list],
        }

    def brief(self):
        return {
            'id': self.id,
            'name': self.name,
            'alias': self.alias,
            'type': self.type,
            'company_id': self.company_id,
            'company_code': self.company_code,
            'company_label': self.company_label,
            'dept_id': self.dept_id,
            'dept_code': self.dept_code,
            'dept_label': self.dept_label,
            'product_id': self.product_id,
            'product_code': self.product_code,
            'product_label': self.product_label,
            'system_id': self.system_id,
            'summary': self.summary,
            'owner_id': self.owner_id,
            'owner': self.owner.brief() if self.owner else {},
            'begin_date': datetime.date.strftime(self.begin_date, '%Y-%m-%d') if self.begin_date else "",
            'expect_publish_date': datetime.date.strftime(self.expect_publish_date, '%Y-%m-%d') if self.expect_publish_date else "",
            'completed_date': datetime.datetime.strftime(self.completed_date, '%Y-%m-%d %H:%M:%S') if self.completed_date else "",
            'sql_script_url': self.sql_script_url
        }


class ProjectParticipant(db.Model):
    __bind_key__ = 'main'
    __tablename__ = 'project_participant'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    participant_id = db.Column(db.String(64), nullable=False)
    participant = db.relationship("User", foreign_keys='ProjectParticipant.participant_id', uselist=False,
                                  primaryjoin="ProjectParticipant.participant_id==User.id")
    privilege_name = db.Column(db.String(16), nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'participant_id': self.participant_id,
            'privilege_name': self.privilege_name,
            'participant': self.participant.brief()
        }
