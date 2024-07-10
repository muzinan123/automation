# -*- coding:utf-8 -*-

import datetime
from sqlalchemy import or_
from app.services.framework.recycle_service import RecycleService
from app.models.framework.Api import ApiACL
from app.models import db
from app import root_logger, api_logger
from app import api_list


class ApiService(object):

    @staticmethod
    def add_acl(app_name, token, ip, api_name, creator):
        try:
            acl = ApiACL(app=app_name, token=token, ip=ip, api_name=api_name, created_at=datetime.datetime.now(), creator=creator, enabled=True)
            db.session.add(acl)
            db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("add_acl error: %s", e)
        return False

    @staticmethod
    def del_acl(acl_id):
        try:
            acl = ApiACL.query.get(acl_id)
            if RecycleService.recycle(acl, commit=False):
                db.session.delete(acl)
                db.session.commit()
                return True
        except Exception, e:
            root_logger.exception("del_acl error: %s", e)
        return False

    @staticmethod
    def mod_acl(acl_id, app_name, token, ip, api_name, enabled):
        try:
            acl = ApiACL.query.get(acl_id)
            if app_name is not None:
                acl.app = app_name
            if token is not None:
                acl.token = token
            if ip is not None:
                acl.ip = ip
            if api_name is not None:
                acl.api_name = api_name
            if enabled is not None:
                acl.enabled = enabled
            db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("mod_acl error: %s", e)
        return False

    @staticmethod
    def list_acl(query=''):
        acls = ApiACL.query.filter(
                                   or_(ApiACL.api_name.like("%" + query + "%") if query is not None else None,
                                       ApiACL.app.like("%" + query + "%") if query is not None else None,
                                       ApiACL.ip.like("%" + query + "%") if query is not None else None)
                                   )
        return acls

    @staticmethod
    def list_api():
        return list(api_list)

    @staticmethod
    def check_acl(token, ip, api_name):
        try:
            api_logger.debug("acl check with: {}, {}, {}".format(token, ip, api_name))
            result = ApiACL.query.filter(ApiACL.token == token, ApiACL.enabled,
                                         or_(ApiACL.ip == ip, ApiACL.ip == '*'),
                                         or_(ApiACL.api_name == api_name, ApiACL.api_name == '*'))
            if result.first():
                api_logger.debug("acl check pass")
                return True
        except Exception, e:
            api_logger.exception("check_acl error: %s", e)
        return False
