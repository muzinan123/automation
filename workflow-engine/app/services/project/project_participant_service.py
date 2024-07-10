# -*- coding: utf8 -*-

from app.models.Project import ProjectParticipant
from app.models import db
from app import root_logger


class ProjectParticipantService(object):

    @staticmethod
    def add_participant(project_id, participant_ids, privilege_name):
        # 先删除存在的记录然后插入
        try:
            participants = ProjectParticipant.query.filter(ProjectParticipant.project_id == project_id, ProjectParticipant.privilege_name == privilege_name)
            for participant in participants:
                db.session.delete(participant)
            db.session.flush()
            for participant_id in participant_ids.split(','):
                p = ProjectParticipant(project_id=project_id, participant_id=participant_id, privilege_name=privilege_name)
                db.session.add(p)
            db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("add_participant error: %s", e)

    @staticmethod
    def query_participant(project_id):
        participants = ProjectParticipant.query.filter(ProjectParticipant.project_id == project_id)
        return [e.serialize() for e in participants]

    @staticmethod
    def list_project_id_by_participant(participant_id, privilege_list=None):
        participants = ProjectParticipant.query.filter(ProjectParticipant.participant_id == participant_id,
                                                       ProjectParticipant.privilege_name.in_(privilege_list) if privilege_list else "")
        return participants
