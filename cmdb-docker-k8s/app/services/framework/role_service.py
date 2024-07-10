# -*- coding:utf-8 -*-

from app.models import db
from app.models.framework.Role import Role
from app.models.framework.Privilege import Privilege
from app.models.framework.User import User
from app.models.framework.RolePrivilege import RolePrivilege


class RoleService:

    def __init__(self):
        pass

    @staticmethod
    def is_exist(role_name):
        if Role.query.filter_by(name=role_name).first():
            return True
        else:
            return False

    @staticmethod
    def add_role(name, alias):
        r = Role(name=unicode(name), alias=unicode(alias))
        ps = Privilege.query.all()
        for p in ps:
            rp = RolePrivilege(rw=0, role_name=r.name, privilege_name=p.name)
            rp.privilege = p
            r.privileges.append(rp)
        db.session.add(r)
        db.session.commit()

    @staticmethod
    def del_role(role_id):
        r = Role.query.get(role_id)
        us = User.query.filter(User.role == r)
        for u in us:
            u.role = None
        db.session.delete(r)
        db.session.commit()

    @staticmethod
    def mod_role(role_id, alias):
        r = Role.query.get(role_id)
        if alias:
            r.alias = unicode(alias)
        db.session.commit()

    @staticmethod
    def get_role():
        r = Role.query.all()
        return r

    @staticmethod
    def link_user_role(user_id, role_id):
        u = User.query.get(user_id)
        r = Role.query.get(role_id)
        u.role = r
        db.session.commit()
