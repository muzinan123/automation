# -*- coding:utf-8 -*-

import datetime
from pymongo import ASCENDING

from app.mongodb import experienced_app_list_collection
from app import root_logger


class ExperiencedAppListService(object):

    @staticmethod
    def add_experience(app_id, app_name, app_type, project_id, publish_id):
        try:
            result = ExperiencedAppListService.check_has_experience(app_id)
            if result:
                experienced_app_list_collection.update_one({'app_id': app_id}, {
                    '$push': {'his_list': {
                        '$each': [{'project_id': project_id, 'publish_id': publish_id, 'time': datetime.datetime.utcnow()}],
                        '$sort': {'time': -1}
                    }}})
            else:
                experienced_app_list_collection.insert_one({'app_id': app_id, 'app_name': app_name, 'app_type': app_type, 'his_list': [
                    {'project_id': project_id, 'publish_id': publish_id, 'time': datetime.datetime.utcnow()}]})
        except Exception, e:
            root_logger.exception("add_experience error: %s", e)

    @staticmethod
    def list_experience(query):
        if query:
            pipeline = [{'$project': {'_id': 0}}, {'$match': {'app_name': {'$regex': query, '$options': '$i'}}},
                        {'$sort': {'app_id': ASCENDING}}]
        else:
            pipeline = [{'$project': {'_id': 0}}, {'$sort': {'app_id': ASCENDING}}]
        return pipeline, experienced_app_list_collection

    @staticmethod
    def check_has_experience(app_id):
        one = experienced_app_list_collection.find_one({'app_id': app_id})
        if one:
            return True
        else:
            return False
