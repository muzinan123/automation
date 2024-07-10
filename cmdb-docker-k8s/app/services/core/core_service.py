# -*- coding: utf8 -*-

import hashlib
from app.services.framework.recycle_service import RecycleService
from app.models.core_uuid_mapping import CoreUUIDMapping
from app.models import db
from app.out.core import Core
from app import root_logger


class CoreService(object):

    @staticmethod
    def register(res_id, is_tag, tag_name, tag_type, res_type):
        try:
            res_uuid = CoreService.get_res_uuid(res_id, res_type)
            c = CoreUUIDMapping(res_id=res_id, res_type=res_type, res_uuid=res_uuid)
            db.session.merge(c)
            db.session.flush()
            if Core.register(is_tag, tag_name, tag_type, res_uuid, res_id, res_type):
                db.session.commit()
                return res_uuid
        except Exception, e:
            root_logger.exception("add_mapping error: %s", e)

    @staticmethod
    def unregister(res_id, res_type):
        try:
            res_uuid = CoreService.get_res_uuid(res_id, res_type)
            Core.unregister(res_uuid)
            return True
        except Exception, e:
            root_logger.exception("del_mapping error: %s", e)

    @staticmethod
    def add_tag(res_id, res_type, tag_type, tag_name):
        res_uuid = CoreService.get_res_uuid(res_id, res_type)
        if Core.add_tag(res_uuid, tag_type, tag_name):
            return True

    @staticmethod
    def remove_tag(res_id, res_type, tag_type, tag_name):
        res_uuid = CoreService.get_res_uuid(res_id, res_type)
        if Core.remove_tag(res_uuid, tag_type, tag_name):
            return True

    @staticmethod
    def get_res_uuid(res_id, res_type):
        return hashlib.sha1("{}@{}".format(res_id, res_type)).hexdigest()

    @staticmethod
    def list_all_tag(res_id, res_type):
        res_uuid = CoreService.get_res_uuid(res_id, res_type)
        data = Core.list_tag(res_uuid)
        if data:
            return data
        return list()

    @staticmethod
    def list_tag(res_id, res_type, tag_type):
        res_uuid = CoreService.get_res_uuid(res_id, res_type)
        data = Core.list_tag(res_uuid, tag_type_list=tag_type)
        if data:
            return data
        return list()

    @staticmethod
    def list_all_addable_tag(res_type, tag_type=None):
        if res_type:
            data = Core.addable_tag(res_type, tag_type_list=tag_type)
            if data:
                return data
        return list()

    @staticmethod
    def list_resource_by_tag(query_list, resource_type_list):
        if query_list:
            data = Core.list_resource_by_tag(query_list, resource_type_list)
            if data:
                ret = list()
                for one in data:
                    if one.get('res_type') in resource_type_list:
                        ret.append(one.get('res_id'))
                return ret
        return list()
