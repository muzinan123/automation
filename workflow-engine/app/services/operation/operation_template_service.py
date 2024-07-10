# -*- coding: utf8 -*-

from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from app.services.framework.recycle_service import RecycleService
from app.mongodb import operation_template_collection
from app import root_logger


class OperationTemplateService(object):

    @staticmethod
    def add_template(template):
        try:
            obj_id = operation_template_collection.insert_one(template).inserted_id
            return str(obj_id)
        except DuplicateKeyError:
            pass
        except Exception, e:
            root_logger.exception("add_template error: %s", e)

    @staticmethod
    def del_template(template_type, name, delete_by='system'):
        try:
            m = operation_template_collection.find_one({'type': template_type, 'name': name})
            RecycleService.recycle_mongo(m, 'operation_template', delete_by=delete_by)
            if m:
                operation_template_collection.remove({'type': template_type, 'name': name})
            return True
        except Exception, e:
            root_logger.exception("del_template error: %s", e)

    @staticmethod
    def mod_template(template):
        try:
            template_type = template.pop('type')
            name = template.pop('name')
            operation_template_collection.update_one({'type': template_type, 'name': name}, {'$set': template})
            return True
        except Exception, e:
            root_logger.exception("mod_module error: %s", e)

    @staticmethod
    def get_template(template_type, name):
        return operation_template_collection.find_one({'type': template_type, 'name': name})

    @staticmethod
    def list_template(template_type):
        pipeline = [{'$project': {
            '_id': False
        }}, {'$match': {
            '$or': [{'type': template_type}]
        }}, {'$sort': {"order": ASCENDING}}]
        items = operation_template_collection.aggregate(pipeline, allowDiskUse=True)
        return [e for e in items]

    @staticmethod
    def list_template_type():
        pipeline = [
            {'$group': {
                '_id': '$type'
            }}
        ]
        items = operation_template_collection.aggregate(pipeline, allowDiskUse=True)
        return [e.get('_id') for e in items]

