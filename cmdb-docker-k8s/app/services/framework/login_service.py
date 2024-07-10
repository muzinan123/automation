# -*- coding:utf-8 -*-

import time
from sqlalchemy import or_, and_
import uuid

from app.models.framework.User import User
from app.models.framework.LoginHistory import LoginHistory
from app.models import db


class LoginService:

    def __init__(self):
        pass

    @staticmethod
    def authenticate(username, password):
        u = User.query.filter_by(name=username, active=1).first()
        if u:
            if u.password == password:
                return u.id
        return

    @staticmethod
    def add_login_history(username, login_ip):
        l = LoginHistory(name=username, login_ip=login_ip, login_at=time.strftime('%Y-%m-%d %H:%M:%S'))
        db.session.add(l)
        db.session.commit()

    @staticmethod
    def get_login_history(query, login_at):
        u = LoginHistory.query.filter(or_(LoginHistory.name.like("%" + query + "%") if query is not None else "",
                                      LoginHistory.login_ip.like("%" + query + "%") if query is not None else ""),
                                      and_(LoginHistory.login_at>=login_at+' 00:00:00', LoginHistory.login_at<=login_at+' 23:59:59') if login_at is not None else "" )
        return u

    @staticmethod
    def add_user_login_count(user_id):
        u = User.query.get(user_id)
        if u:
            u.login_count += 1
            db.session.commit()

    @staticmethod
    def give_token(user_id):
        u = User.query.get(user_id)
        if u and u.enabled:
            token=uuid.uuid4().hex
            u.token = token
            db.session.commit()
            return token