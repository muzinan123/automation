# -*- coding:utf-8 -*-

import pytz
from datetime import datetime
from pymongo import ASCENDING, DESCENDING

from app.mongodb import hot_pool_pre_server_collection, hot_pool_diamond_collection, hot_pool_prd_app_collection, flow_data_collection
from app import root_logger


class HotPoolService(object):

    @staticmethod
    def allocate_pre_server(res_id, ip, port, app_id, publish_id):
        try:
            result = hot_pool_pre_server_collection.insert_one({'res_id': res_id, 'ip': ip, 'port': port,
                                                                'app_id': app_id, 'publish_id': publish_id})
            if result.inserted_id:
                return True
        except Exception, e:
            root_logger.exception("allocate error: %s", e)

    @staticmethod
    def release_pre_server(publish_id):
        try:
            hot_pool_pre_server_collection.delete_many({'publish_id': publish_id})
            return True
        except Exception, e:
            root_logger.exception("releases error: %s", e)

    @staticmethod
    def check_free_pre_server(res_id, port):
        one = hot_pool_pre_server_collection.find_one({'res_id': res_id, 'port': port})
        if one:
            return False
        else:
            return True

    @staticmethod
    def allocate_diamond(data_id, env, publish_id):
        try:
            result = hot_pool_diamond_collection.insert_one({'data_id': data_id, 'env': env, 'publish_id': publish_id})
            if result.inserted_id:
                return True
        except Exception, e:
            root_logger.exception("allocate error: %s", e)

    @staticmethod
    def releases_diamond(publish_id, env):
        try:
            hot_pool_diamond_collection.delete_many({'env': env, 'publish_id': publish_id})
            return True
        except Exception, e:
            root_logger.exception("releases error: %s", e)

    @staticmethod
    def check_hot_diamond(data_id, env):
        one = hot_pool_diamond_collection.find_one({'data_id': data_id, 'env': env})
        if one:
            return one.get('publish_id')
        else:
            return False

    @staticmethod
    def add_prd_app(app_id, publish_id, project_id, app_name, tag_revision, up_time, scheduled_time, ready):
        try:
            local = pytz.timezone("Asia/Shanghai")
            naive = datetime.strptime(up_time, '%Y-%m-%d %H:%M:%S.%f')
            local_dt = local.localize(naive, is_dst=None)
            up_time = local_dt.astimezone(pytz.utc)
            result = hot_pool_prd_app_collection.insert_one({'app_id': app_id, 'publish_id': publish_id,
                                                             'project_id': project_id, 'app_name': app_name,
                                                             'tag_revision': tag_revision, 'up_time': up_time,
                                                             'running': False, 'ready': ready, 'skip': False,
                                                             'scheduled_time': scheduled_time})
            if result.inserted_id:
                return True
        except Exception, e:
            root_logger.exception("add error: %s", e)

    @staticmethod
    def release_prd_app(publish_id):
        try:
            hot_pool_prd_app_collection.delete_many({'publish_id': publish_id})
            return True
        except Exception, e:
            root_logger.exception("releases error: %s", e)

    @staticmethod
    def start_run_prd_app(publish_id):
        try:
            hot_pool_prd_app_collection.update_many({'publish_id': publish_id}, {'$set': {'running': True}})
        except Exception, e:
            root_logger.exception("start run prd app error: %s", e)

    @staticmethod
    def stop_run_prd_app(publish_id):
        try:
            hot_pool_prd_app_collection.update_many({'publish_id': publish_id}, {'$set': {'running': False}})
        except Exception, e:
            root_logger.exception("stop run prd app error: %s", e)

    @staticmethod
    def check_hot_prd_app(app_id):
        # 按up_time倒序获取最新的一个记录
        records = hot_pool_prd_app_collection.find({'app_id': app_id}).sort([('up_time', DESCENDING)]).limit(1)
        for one in records:
            return one

    @staticmethod
    def get_change_window_prd_app(publish_id):
        # 获取可以修改的时间区间
        flow_data = flow_data_collection.find_one({'flow_id': publish_id})
        app_id_list = flow_data.get('data').get('app_order')
        app_id_list.extend(flow_data.get('data').get('share_order'))
        if flow_data.get('data').get('dzbd'):
            app_id_list.append(flow_data.get('data').get('dzbd').get('app_id'))

        earliest = datetime.now()
        latest = datetime.strptime('2099-01-01', '%Y-%m-%d')
        for app_id in app_id_list:
            earliest_scheduled_prd_app = HotPoolService.get_latest_scheduled_prd_app(app_id)
            if earliest_scheduled_prd_app and earliest_scheduled_prd_app.get('publish_id') != publish_id and earliest_scheduled_prd_app.get('scheduled_time') > earliest:
                earliest = earliest_scheduled_prd_app.get('scheduled_time')
        return earliest, latest

    @staticmethod
    def get_latest_scheduled_prd_app(app_id):
        # 获取某个app_id应用+定时发布时间最晚的记录
        records = hot_pool_prd_app_collection.find({'app_id': app_id, 'scheduled_time': {'$ne': None}}).sort(
            [('scheduled_time', DESCENDING)]).limit(1)
        for one in records:
            return one

    @staticmethod
    def get_earliest_scheduled_prd_app(app_id):
        # 获取某个app_id应用+定时发布时间最早的记录
        records = hot_pool_prd_app_collection.find({'app_id': app_id, 'scheduled_time': {'$ne': None}}).sort(
            [('scheduled_time', ASCENDING)]).limit(1)
        for one in records:
            return one

    @staticmethod
    def cancel_scheduled_prd_app(publish_id):
        # 取消某个发布单的定时发布
        try:
            hot_pool_prd_app_collection.update_many({'publish_id': publish_id}, {'$set': {'scheduled_time': None}})
            return True
        except Exception, e:
            root_logger.exception("cancel scheduled prd app error: %s", e)

    @staticmethod
    def change_scheduled_prd_app(publish_id, scheduled_time):
        try:
            hot_pool_prd_app_collection.update_many({'publish_id': publish_id}, {'$set': {'scheduled_time': scheduled_time}})
            return True
        except Exception, e:
            root_logger.exception("change scheduled prd app error: %s", e)

    @staticmethod
    def has_before_scheduled_prd_app(app_id, scheduled_time):
        count = hot_pool_prd_app_collection.find({'app_id': app_id, 'scheduled_time': {'$lt': scheduled_time}}).count()
        if count:
            return True

    @staticmethod
    def get_running_hot_prd_app(app_id):
        one = hot_pool_prd_app_collection.find_one({'app_id': app_id, 'running': True}, {'_id': 0})
        if one:
            return one

    @staticmethod
    def set_hot_prd_app_ready(publish_id):
        try:
            hot_pool_prd_app_collection.update_many({'publish_id': publish_id}, {'$set': {'ready': True}})
        except Exception, e:
            root_logger.exception("set hot prd app ready error: %s", e)

    @staticmethod
    def skip_hot_prd_app(app_id, publish_id):
        try:
            hot_pool_prd_app_collection.update_one({'publish_id': publish_id, 'app_id': app_id}, {'$set': {'skip': True}})
            return True
        except Exception, e:
            root_logger.exception("set hot prd app ready error: %s", e)

    @staticmethod
    def list_up_hot_prd_app(app_id, publish_id):
        hot_prd_app = hot_pool_prd_app_collection.find_one({'app_id':app_id, 'publish_id': publish_id})
        if hot_prd_app:
            records = hot_pool_prd_app_collection.find(
                {'app_id': app_id, 'publish_id': {'$ne': publish_id}, 'up_time': {'$gte': hot_prd_app.get('up_time')}, 'skip': False},
                {'_id': 0}).sort([('up_time', DESCENDING)])
            return [e for e in records]
        return []

    @staticmethod
    def list_down_hot_prd_app(app_id, publish_id):
        hot_prd_app = hot_pool_prd_app_collection.find_one({'app_id':app_id, 'publish_id': publish_id})
        if hot_prd_app:
            records = hot_pool_prd_app_collection.find(
                {'app_id': app_id, 'publish_id': {'$ne': publish_id}, 'up_time': {'$lte': hot_prd_app.get('up_time')}, 'skip': False},
                {'_id': 0}).sort([('up_time', DESCENDING)])
            return [e for e in records]
        return []
