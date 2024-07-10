# -*- coding: utf8 -*-
from app.models.UserCredit import UserCreditDetail, UserCredit
from app.services.project.project_record_service import ProjectRecordService
from app.services.project.project_service import ProjectService
from app.models import db
from app import root_logger


class UserCreditService(object):

    @staticmethod
    def add_credit_detail(user_id, project_id, increment, action, modifier, gmt_modified):
        # 新增详细记录
        try:
            u = UserCreditDetail(user_id=user_id, project_id=project_id, increment=increment, action=action, modifier=modifier, gmt_modified=gmt_modified)
            db.session.add(u)
            db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("add credit detail error:%s", e)

    @staticmethod
    def update_credit(user_id, increment, gmt_modified):
        # 有记录直接更新无则插入记录
        try:
            c = UserCredit.query.get(user_id)
            if c:
                credit = c.credit + increment
                c.credit = credit
                c.gmt_modified = gmt_modified
                db.session.commit()
            else:
                u = UserCredit(user_id=user_id, credit=increment, gmt_modified=gmt_modified)
                db.session.add(u)
                db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("upsert user credit error:%s", e)

    @staticmethod
    def cal_credit(start, end):
        # 定时计算用户的积分，并插入数据库
        records = ProjectRecordService.query_record_by_time(start, end)
        try:
            for r in records:
                record = r.serialize()
                project_id = record.get('project_id')
                action = record.get('action')
                modifier = record.get('operator_id')
                gmt_modified = record.get('gmt_modified')
                increment = 0
                p = ProjectService.get_project(project_id)
                if p:
                    owner_id = p.owner_id
                    if action == 'PRD_COMPLETE':
                        # 自动发布完成加3分
                        increment = 3
                    elif action == 'PUBLISH_URGENCY_OTHERS':
                        # 紧急发布 除0-9 20-24点外
                        increment = -2
                    elif action == 'PUBLISH_URGENCY_TWENTY_POINTS':
                        # 20-24 紧急发布
                        increment = -3
                    elif action == 'PUBLISH_URGENCY_ZERO_POINTS':
                        # 0-9 紧急发布
                        increment = -4
                    elif action == 'PRE_NOT_PASS':
                        # 验证回退
                        increment = -2
                    elif action == 'LOCAL_NOT_PASS':
                        # owner回退
                        increment = -2


                    # elif action == 'SQL_REVIEW_URGENCY_SIX_POINTS':
                    #     # 18-21
                    #     increment = -3
                    # elif action == 'SQL_REVIEW_URGENCY_NINE_POINTS':
                    #     # 21-24
                    #     increment = -4
                    # elif action == 'SQL_REVIEW_URGENCY_TWELVE_POINTS':
                    #     # 0-9
                    #     increment = -5
                    if increment != 0:
                        u = UserCreditDetail(user_id=owner_id, project_id=project_id, increment=increment, action=action,
                                         modifier=modifier, gmt_modified=gmt_modified)
                        db.session.add(u)
                        c = UserCredit.query.get(owner_id)
                        if c:
                            credit = c.credit + increment
                            c.credit = credit
                            c.gmt_modified = gmt_modified
                            db.session.flush()
                        else:
                            u = UserCredit(user_id=owner_id, credit=increment, gmt_modified=gmt_modified)
                            db.session.add(u)
                            db.session.flush()
            db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("calculate user credit error:%s", e)
