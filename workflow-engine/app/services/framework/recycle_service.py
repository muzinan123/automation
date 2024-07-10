# -*- coding:utf-8 -*-

import json
import datetime
from bson import json_util

from app.models import db
from app.models.RecycleBin import RecycleBin
from app.mongodb import recycle_collection
from app import root_logger


class RecycleService(object):

    @staticmethod
    def recycle(resource, delete_by='system', commit=True):
        try:
            resource_type = type(resource)
            resource_content = json.dumps(resource.serialize())
            recycle_bin = RecycleBin(resource_type=resource_type, resource_content=resource_content,delete_by=delete_by)
            db.session.add(recycle_bin)
            if commit:
                db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("recycle error: %s", e)
            return False

    @staticmethod
    def recycle_mongo(res, res_type, delete_by='system'):
        try:
            res_str = json.dumps(res, default=json_util.default)
            r = dict(res_type=res_type, res=res_str, delete_by=delete_by, delete_at=datetime.datetime.utcnow())
            recycle_collection.insert(r)
            return True
        except Exception, e:
            root_logger.exception("recycle mongo error: %s", e)
            return False
