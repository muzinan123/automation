# -*- coding:utf8 -*-

import requests
import json
from app import app, out_logger


class Aliyun(object):

    @staticmethod
    def list_docker_ecs():
        try:
            data = dict()
            data['query_list'] = json.dumps([[{'tag_type': 'is_docker', 'tag_name': 'Y'}]])
            url = app.config['CMDB_ALIYUN_URL'] + "/api/aliyun/ecs/list"
            api_token = app.config['CMDB_ALIYUN_TOKEN']
            response = requests.post(url, data=data, headers={'api': api_token}, timeout=10)
            if response.json().get('result') == 1:
                return response.json().get('data')
            else:
                out_logger.error("list_docker_ecs error")
        except Exception, e:
            out_logger.exception("list_docker_ecs error: %s", e)

    @staticmethod
    def find_ecs_by_ip(ip):
        try:
            url = app.config['CMDB_ALIYUN_URL'] + "/api/find_res_by_ip/{}".format(ip)
            api_token = app.config['CMDB_ALIYUN_TOKEN']
            response = requests.get(url, headers={'api': api_token}, timeout=10)
            if response.json().get('result') == 1 and response.json().get('type') == "ecs":
                return response.json().get('data')
            else:
                out_logger.error("find_res_by_ip error")
        except Exception, e:
            out_logger.exception("find_res_by_ip error: %s", e)
