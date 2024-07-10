# -*- coding: utf8 -*-

import requests
from app import app
from app import out_logger


class CMDBAliyun(object):

    @staticmethod
    def slb_action(action, ecs_id, slb_id):
        try:
            url = ""
            if action == 'add':
                url = app.config.get('CMDB_ALIYUN_URL') + '/api/slb/add'
            elif action == 'rm':
                url = app.config.get('CMDB_ALIYUN_URL') + '/api/slb/rm'
            data = {'serverHost': ecs_id, 'slbHost': slb_id}
            out_logger.info(url)
            out_logger.info(data)
            token = app.config.get('CMDB_ALIYUN_TOKEN')
            response = requests.post(url, data=data, headers={'api': token})
            out_logger.info(response.content)
            if response.json().get('result') == 1:
                return True
        except Exception, e:
            out_logger.exception("slb action exception error: %s", e)
