# -*- coding:utf-8 -*-

import re
from sqlalchemy import or_

from app.models.framework.User import User
from app.models.framework.Role import Role
from app.models.framework.RolePrivilege import RolePrivilege
from app.models.framework.Privilege import Privilege
from app.models.framework.Department import Department
from app.models import db
from app import app


class UserService:
    email_check = re.compile(r'^(\w)+(\.\w+)*@(\w)+((\.\w+)+)$')

    def __init__(self):
        pass

    @staticmethod
    def is_exist(username):
        u = User.query.filter_by(name=username).first()
        if u:
            return u.id
        else:
            return False

    def check_user(self, username, password, email):
        if username and password and email:
            if self.email_check.match(email):
                if not self.is_exist(username):
                    return True
        return False

    @staticmethod
    def add_sso_user(name, email, real_name, work_no, phone, department, sex):
        u = User(id=work_no, name=name, email=email, real_name=real_name, work_no=work_no, phone=phone,
                 sex=sex, login_count=0)
        r = Role.query.get(app.config.get('DEFAULT_ROLE_ID'))
        d = Department.query.filter_by(name=department).first()
        if r:
            u.role = r
        if d:
            u.department = d
        db.session.add(u)
        db.session.commit()
        return u.id

    @staticmethod
    def get_users(query):
        u = User.query.filter(or_(User.name.like("%" + query + "%") if query is not None else "",
                                  User.real_name.like("%" + query + "%") if query is not None else ""))
        return u

    @staticmethod
    def get_user_by_name(user_name):
        u = User.query.filter(User.name == user_name)
        return u

    @staticmethod
    def get_user(user_id):
        u = User.query.get(user_id)
        return u

    @staticmethod
    def mod_user(user_id, phone, email, role_id, enabled):
        u = User.query.get(user_id)
        if phone:
            u.phone = phone
        if email:
            u.email = email
        if role_id:
            r = Role.query.get(role_id)
            if r:
                u.role = r
        if enabled != None:
            u.enabled = int(enabled)
        db.session.commit()

    @staticmethod
    def check_token(token):
        u = User.query.filter_by(token=token, enabled=True)
        if u.first():
            return u.first().id
        else:
            return

    @staticmethod
    def has_privilege(user_id, privilege_name, rw):
        r = User.query.get(user_id).role
        rp = r.privileges.filter_by(privilege_name=privilege_name).first()
        if rp:
            if rp.rw >= rw:
                return True
        return False

    @staticmethod
    def get_user_info(user_id):
        u = User.query.get(user_id)
        r = u.role
        userInfo = {}
        userInfo['name'] = u.name
        userInfo['role'] = r.name
        userInfo['real_name'] = u.real_name
        return userInfo

    @staticmethod
    def get_user_privileges(user_id):
        u = User.query.get(user_id)
        r = u.role
        ps = r.privileges.all()
        privileges = {}
        for p in ps:
            privileges[p.privilege_name] = p.rw
        return privileges

    @staticmethod
    def get_user_resource_privileges(user_id, pattern):
        pattern = pattern.format(id='')
        u = User.query.get(user_id)
        r = u.role
        ps = r.privileges.filter(RolePrivilege.privilege_name.like(pattern + "%")).all()
        privileges = dict()
        for p in ps:
            privileges[p.privilege_name] = p.rw
        return privileges

    # privilege = task.type
    @staticmethod
    def get_user_by_privilege(privilege):
        privilege = Privilege.query.filter(Privilege.name == privilege).first()
        if privilege:
            roles = privilege.roles
            ret = set()
            for role in roles:
                if role.rw == 2:
                    users = role.role.users
                    for user in users:
                        ret.add(user)
            return ret

    @staticmethod
    def get_all_department():
        depts = Department.query.filter(Department.id != '1')
        ret = list()
        for dept in depts:
            ret.append((str(dept.id), dept.name))
        return ret

