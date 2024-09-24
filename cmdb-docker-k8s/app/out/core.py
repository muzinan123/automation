# -*- coding:utf8 -*-

import hashlib
import requests

from app.mongodb import resource_collection, tag_collection, res_type_collection, tag_type_collection
from app.util import Util
from app import app, out_logger


class Core(object):
    @staticmethod
    def register(is_tag, tag_name, tag_type, res_uuid, res_id, res_type):
        url = app.config['CMDB_CORE_URL'] + "/api/resource/register"
        api_token = app.config['CMDB_CORE_TOKEN']
        data = dict()
        data['module_id'] = app.config['CMDB_CORE_MODULE_ID']
        data['is_tag'] = is_tag
        data['tag_name'] = tag_name
        data['tag_type'] = ",".join(tag_type)
        data['res_uuid'] = res_uuid
        data['res_id'] = res_id
        data['res_type'] = res_type
        try:
            response = requests.post(url, data=data, headers={'api': api_token}, timeout=10)
            if response.json().get('result') == 1:
                return True
            else:
                out_logger.error("register error: %s" % response.json().get('info'))
        except Exception, e:
            out_logger.exception("register error: %s", e)

    @staticmethod
    def unregister(uuid):
        url = app.config['CMDB_CORE_URL'] + "/api/resource/{}/unregister".format(uuid)
        api_token = app.config['CMDB_CORE_TOKEN']
        try:
            response = requests.post(url, headers={'api': api_token}, timeout=10)
            if response.json().get('result') == 1:
                return True
            else:
                out_logger.error("unregister error: %s" % response.json().get('info'))
        except Exception, e:
            out_logger.exception("unregister error: %s", e)

    @staticmethod
    def add_tag(uuid, tag_type, tag_name):
        url = app.config['CMDB_CORE_URL'] + u"/api/resource/{}/add_tag/{}/{}".format(uuid, tag_type, tag_name)
        api_token = app.config['CMDB_CORE_TOKEN']
        try:
            response = requests.post(url, headers={'api': api_token}, timeout=10)
            if response.json().get('result') == 1:
                return True
            else:
                out_logger.error("add_tag error: %s" % response.json().get('info'))
        except Exception, e:
            out_logger.exception("add_tag error: %s", e)

    @staticmethod
    def remove_tag(uuid, tag_type, tag_name):
        url = app.config['CMDB_CORE_URL'] + u"/api/resource/{}/remove_tag/{}/{}".format(uuid, tag_type, tag_name)
        api_token = app.config['CMDB_CORE_TOKEN']
        try:
            response = requests.post(url, headers={'api': api_token}, timeout=10)
            if response.json().get('result') == 1:
                return True
            else:
                out_logger.error("remove_tag error: %s" % response.json().get('info'))
        except Exception, e:
            out_logger.exception("remove_tag error: %s", e)

    @staticmethod
    def addable_tag(res_type, tag_type_list=None):
        try:
            ret = list()
            addable_tag_type_list = res_type_collection.find_one({'type': res_type}).get('addable_tag_type')
            addable_tag_type = tag_type_collection.find({'type': {'$in': addable_tag_type_list}})
            tag_type_set = set([e.get('type') for e in addable_tag_type])
            if tag_type_list:
                tag_type_set &= set(tag_type_list)
            tag_type_list = list(tag_type_set)
            tags = tag_collection.find({'type': {'$in': tag_type_list}})
            for tag in tags:
                ret.append({'name': tag['name'], 'type': tag['type']})
            return ret
        except Exception, e:
            out_logger.exception("addable_tag error: %s", e)

    @staticmethod
    def list_tag(uuid, tag_type_list=None):
        try:
            res = resource_collection.find_one({'uuid': uuid})
            if res:
                tags = res.get('tags')
                match_list = list()
                for tag in tags:
                    if tag_type_list and tag.get('type') not in tag_type_list:
                        continue
                    match_list.append({'type': tag.get('type'), 'name': tag.get('name')})
                pipeline = [
                    {'$lookup': {
                        'from': 'module_collection',
                        'localField': 'module_id',
                        'foreignField': 'module_id',
                        'as': 'modules'
                    }},
                    {'$match': {
                        '$or': match_list
                    }}
                ]
                ret = list()
                for tag in tag_collection.aggregate(pipeline):
                    ret.append({
                        'tag_name': tag.get('name'),
                        'type': tag.get('type'),
                        'module_url': tag.get('modules')[0].get('url'),
                        'tag_url': tag.get('url'),
                        'tag_json_url': tag.get('json_url')
                    })
                return ret
        except Exception, e:
            out_logger.exception("list_tag error: %s", e)

    @staticmethod
    def list_resource_by_self_tag(uuid, tag_type):
        try:
            self_tag = tag_collection.find_one({'from_resource_uuid': uuid, 'type': tag_type})
            if self_tag:
                ret = list()
                pipeline = [
                    {'$lookup': {
                        'from': 'module_collection',
                        'localField': 'module_id',
                        'foreignField': 'module_id',
                        'as': 'modules'
                    }},
                    {'$match': {
                        'tags': {
                            '$elemMatch': {
                                'type': self_tag['type'],
                                'name': self_tag['name']
                            }
                        }
                    }}
                ]
                for res in resource_collection.aggregate(pipeline):
                    ret.append({
                        'uuid': res.get('uuid'),
                        'type': res.get('type'),
                        'url': res.get('url'),
                        'json_url': res.get('json_url'),
                        'module_id': res.get('module_id'),
                        'module_url': res.get('modules')[0].get('url')
                    })
                return ret
        except Exception, e:
            out_logger.exception("list_resource_by_self_tag error: %s", e)

    @staticmethod
    def get_resource_data(module_id, json_url):
        ext_token = app.config['EXT_TOKEN']
        token = ext_token.get(module_id)
        if token:
            try:
                response = requests.get(json_url, headers={'api': token})
                if response.status_code == 200:
                    data = response.json()
                    if data.get('result') == 1:
                        return data.get('data')
            except Exception, e:
                out_logger.exception("get_resource_data error: %s", e)

    @staticmethod
    def list_resource_by_tag(query_list, resource_type_list):
        try:
            if query_list:
                cache_key = "{}_{}".format(query_list, resource_type_list)
                cache_key = hashlib.md5(cache_key).hexdigest()
                ret = Util.redis.get("tlr_" + cache_key)
                if ret:
                    return eval(ret)
                sub_query_list = query_list.pop()
                ret = set()
                for query in sub_query_list:
                    reses = resource_collection.find({'type': {'$in': resource_type_list},
                                                      'tags': {'$elemMatch': {
                                                          'type': query['tag_type'], 'name': query['tag_name']}}
                                                      })
                    for res in reses:
                        ret.add({'res_id': res.get('res_id'), 'res_type': res.get('type')})
                if ret:
                    for sub_query_list in query_list:
                        temp = set()
                        for query in sub_query_list:
                            reses = resource_collection.find({'type': {'$in': resource_type_list},
                                                              'tags': {'$elemMatch': {
                                                                  'type': query['tag_type'], 'name': query['tag_name']}}
                                                              })
                            for res in reses:
                                temp.add({'res_id': res.get('res_id'), 'res_type': res.get('type')})
                        ret &= temp
                Util.redis.set("tlr_" + cache_key, list(ret), ex=30)
                return list(ret)
        except Exception, e:
            out_logger.exception("list_resource_by_tag error: %s", e)
