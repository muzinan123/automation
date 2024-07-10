# -*- coding:utf-8 -*-

import json
from app.models import db
from app.models.framework.RecycleBin import RecycleBin
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
    def restore(id):
        pass
