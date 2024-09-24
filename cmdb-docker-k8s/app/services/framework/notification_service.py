# -*- coding:utf-8 -*-

from sqlalchemy import func, desc, and_
from app.models import db
from app.models.framework.Notification import Notification
import datetime


class NotificationService(object):

    @staticmethod
    def get_unreaded(user_id):
        ns = db.session.query(func.count('*')).select_from(Notification).filter(Notification.readed == False, Notification.target_user_id == user_id).scalar()
        return ns

    @staticmethod
    def list_by_user(user_id, query=None, created_at=None):
        ns = Notification.query.filter(Notification.target_user_id == user_id,
                                       Notification.content.like("%"+query+"%") if query is not None else "",
                                       and_(Notification.created_at >= created_at + ' 00:00:00',
                                            Notification.created_at <= created_at + ' 23:59:59') if created_at is not None else ""
                                       ).order_by(desc(Notification.created_at))
        return ns

    @staticmethod
    def add(content, type, targets):
        for target_user_id in targets:
            ns = Notification(content=content, type=type, target_user_id=target_user_id.get('id'), created_at=datetime.datetime.now())
            db.session.add(ns)
        db.session.commit()

    @staticmethod
    def readed(msg_id):
        ns = Notification.query.get(msg_id)
        ns.readed = True
        ns.modified_at = datetime.datetime.now()
        db.session.commit()

    @staticmethod
    def all_readed(user_id):
        ns = Notification.query.filter(Notification.target_user_id == user_id, Notification.readed == False)
        for n in ns:
            n.readed = True
        db.session.commit()
