# -*- coding: utf8 -*-

from sqlalchemy import or_, and_

from app.models.ProjectRecord import ProjectRecord
from app.models import db
from app import root_logger


class ProjectRecordService(object):

    @staticmethod
    def add_project_record(project_id, operator_id, role, process, action, remark, gmt_modified):
        try:
            record = ProjectRecord(project_id=project_id, operator_id=operator_id, role=role, process=process, action=action, remark=remark, gmt_modified=gmt_modified)
            db.session.add(record)
            db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("project record add exception: %s", e)
            return False

    @staticmethod
    def mod_project_record(record_id, remark=None):
        try:
            record = ProjectRecord.query.get(record_id)
            if remark is not None:
                record.remark = remark
            db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("project record mod exception: %s", e)

    @staticmethod
    def query_project_record(project_id):
        records = ProjectRecord.query.filter(ProjectRecord.project_id == project_id).order_by(ProjectRecord.id.desc())
        return [e.serialize() for e in records]

    @staticmethod
    def query_record_by_action():
        return ProjectRecord.query.filter(or_(ProjectRecord.action == 'PUBLISH_UAT_VERIFY_ROLLBACK',
                                              ProjectRecord.action == 'OWNER_ROLLBACK_PUBLISH',
                                              ProjectRecord.action == 'OWNER_ROLLBACK'))

    @staticmethod
    def query_test_record_number(project_id, action):
        return ProjectRecord.query.filter(ProjectRecord.project_id == project_id,
                                          ProjectRecord.action == action).count()

    @staticmethod
    def query_record_by_time(start, end):
        projects = ProjectRecord.query.filter(and_(ProjectRecord.gmt_modified >= start, ProjectRecord.gmt_modified < end))
        return projects

    @staticmethod
    def get_reason_name(code):
        if code == 'exist_bug':
            return u"存在Bug"
        elif code == 'publish_problem':
            return u"发布问题"
        elif code == 'commit_problem':
            return u"代码漏提交"
        elif code == 'code_conflict':
            return u"代码冲突"
        elif code == 'code_stale':
            return u"不是最新代码"
        elif code == 'other':
            return u"其它"

