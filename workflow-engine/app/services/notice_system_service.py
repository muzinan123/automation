# -*- coding: utf-8 -*-

import datetime
from pymongo import ASCENDING, DESCENDING

from app.mongodb import notice_system_collection
from app import root_logger


class noticeSystemService(object):

    # 首页公告---查询
    @staticmethod
    def home_notice(week_day):
        data = notice_system_collection.find_one({"type": "notice", "week_day": week_day})
        return data

    # 首页系统更新说明---查询
    @staticmethod
    def home_systemupdate():
        data = notice_system_collection.find({"type": "systemUpdate"}, {'_id': False}).sort([('create_date', DESCENDING)]).limit(1)
        return [e for e in data]

    # 公告提示---查询
    @staticmethod
    def notice_find_list(week_day):
        if week_day != None:
            data = notice_system_collection.find({"type": "notice", "week_day": week_day}, {'_id': False}).sort([('week_day', ASCENDING)])
            return data
        else:
            data = notice_system_collection.find({"type": "notice"}, {'_id': False}).sort([('week_day', ASCENDING)])
            return data

    # 公告---修改
    @staticmethod
    def notice_update(content, week_day):
        try:
            result = notice_system_collection.update_one({"type": "notice", "week_day": week_day}, {"$set": {"content": content, "update_date": datetime.datetime.utcnow()}})
            return result
        except Exception, e:
            root_logger.exception("Query notice_system switch data failed: %s", e)
            return

    # 公告信息---新增
    @staticmethod
    def notice_insert(content, week_day, creator_id):
        try:
            notice_entity = {
                'content': content,
                'week_day': week_day,
                'create_date': datetime.datetime.utcnow(),
                'update_date': datetime.datetime.utcnow(),
                'creator_id': creator_id,
                'type': "notice"
            }
            result = notice_system_collection.insert_one(notice_entity)
            return result
        except Exception, e:
            root_logger.exception("notice_insert failed: %s", e)
            return

    # 系统更新说明---查询
    @staticmethod
    def system_find_list():
        data = notice_system_collection.find_one({"type": "systemUpdate"}, {'_id': False})
        return data

    # 系统更新说明---新增
    @staticmethod
    def system_insert(content, creator_id):
        try:
            system_entity = {
                'content': content,
                'create_date': datetime.datetime.utcnow(),
                'update_date': datetime.datetime.utcnow(),
                'creator_id': creator_id,
                'type': "systemUpdate"
            }
            result = notice_system_collection.insert_one(system_entity)
            return result
        except Exception, e:
            root_logger.exception("system_insert failed: %s", e)
            return

    # 系统更新说明---修改
    @staticmethod
    def system_update(content):
        try:
            result = notice_system_collection.update({"type": "systemUpdate"}, {"$set": {"content": content, "update_date": datetime.datetime.utcnow()}})
            return result
        except Exception, e:
            root_logger.exception("system_update failed: %s", e)
            return
