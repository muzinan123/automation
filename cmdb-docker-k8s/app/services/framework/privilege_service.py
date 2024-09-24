# -*- coding:utf-8 -*-

from app.models import db
from app.models.framework.Role import Role
from app.models.framework.Privilege import Privilege
from app.models.framework.RolePrivilege import RolePrivilege


class PrivilegeService:

    def __init__(self):
        pass

    @staticmethod
    def is_exist(privilege_name):
        if Privilege.query.filter_by(name=privilege_name).first():
            return True
        else:
            return False

    @staticmethod
    def add_privilege(name, alias):
        p = Privilege(name=unicode(name), alias=unicode(alias))
        rs = Role.query.all()
        for r in rs:
            rp = RolePrivilege(rw=0, role_name=r.name, privilege_name=p.name)
            rp.role = r
            p.roles.append(rp)
        db.session.add(p)
        db.session.commit()

    @staticmethod
    def del_privilege(id):
        p = Privilege.query.get(id)
        db.session.delete(p)
        db.session.commit()

    @staticmethod
    def mod_privilege(id, alias):
        p = Privilege.query.get(id)
        p.alias = unicode(alias)
        db.session.commit()

    @staticmethod
    def get_privileges():
        p = Privilege.query.all()
        return p

    @staticmethod
    def get_role_privileges(role_id):
        rps = RolePrivilege.query.filter_by(role_id = role_id).all()
        return rps

    @staticmethod
    def link_role_privilege(role_id, privilege_id, read, write):
        rps = RolePrivilege.query.filter_by(role_id = role_id, privilege_id = privilege_id)
        if rps:
            rp = rps.first()
            if read:
                if write:
                    rp.rw = 2
                else:
                    rp.rw = 1
            else:
                rp.rw = 0
            db.session.commit()
