# -*- coding: utf8 -*-

import requests

from app import app, out_logger


class CMDBCore(object):

    @staticmethod
    def query_arrange(env, app_id, res_type):
        try:
            url = app.config['CMDB_CORE_URL'] + "/api/arrange/query"
            data = dict()
            data['env'] = env
            data['app_id'] = app_id
            data['type'] = res_type
            out_logger.info(url)
            out_logger.info(data)
            response = requests.post(url, data=data, headers={'api': app.config['CMDB_CORE_TOKEN']})
            out_logger.info(response.content)
            if response.status_code == 200:
                if response.json().get('result') == 1:
                    return response.json().get('data')
        except Exception, e:
            out_logger.exception("query arrange error: %s", e)
