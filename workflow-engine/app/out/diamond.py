# -*- coding: utf8 -*-

import requests

from app import app
from app import out_logger


class Diamond(object):

    @staticmethod
    def query_diamond(env, data_id):
        try:
            diamond_url = app.config.get('DIAMOND_{}_URL'.format(env.upper()))
            url = diamond_url + '/diamond-server/config.do?dataId={}&group='.format(data_id)
            out_logger.info(url)
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.content.decode('gbk')
        except Exception, e:
            out_logger.exception("query diamond exception: %s", e)
        return None

    @staticmethod
    def save_diamond(env, data_id, content, group='DEFAULT_GROUP'):
        try:
            diamond_url = app.config.get('DIAMOND_{}_URL'.format(env.upper()))
            url = diamond_url + '/diamond-server/basestone.do?method=syncUpdateAll'
            out_logger.info(url)
            data = dict()
            data['dataId'] = data_id
            data['group'] = group
            data['content'] = content.encode('gbk')
            out_logger.debug(data)
            response = requests.post(url, data, timeout=30)
            out_logger.info(response.content)
            if response.status_code == 200:
                return True
        except Exception, e:
            out_logger.exception("save diamond exception: %s", e)
