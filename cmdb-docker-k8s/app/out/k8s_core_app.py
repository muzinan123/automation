# -*- coding:utf8 -*-

import requests, json
from app import app, out_logger, rds_logger


class K8SCoreApp(object):

    @staticmethod
    def select_rds_by_app_name(app_id, app_name, res_type, env, org):
        try:
            data = dict()
            data['app_name'] = app_name
            data['res_type'] = res_type
            data['env'] = env
            data['org'] = org
            data['app_id'] = app_id
            url = app.config['CMDB_CORE_URL'] + "/api/arrange/select_rds_by_app_name"
            api_token = app.config['CMDB_CORE_TOKEN']
            response = requests.post(url, data=data, headers={'api': api_token}, timeout=10)
            rds_logger.info("select_rds_by_app_name {} {}".format(url, json.dumps(data)))
            if response.json().get('result') == 1:
                return response.json().get('result'), response.json().get('data')
            else:
                rds_logger.error("select_rds_by_app_name error")
                return response.json().get('result'), u'查询应用对应的RDS信息失败'
        except Exception, e:
            rds_logger.exception("select_rds_by_app_name error: %s", e)

    @staticmethod
    def get_app_company(app_id):
        try:
            data = dict()
            data['app_id'] = app_id
            url = app.config['APPREPO_URL'] + "/api/app/company/get_app_company"
            api_token = app.config['CMDB_APPREPO_TOKEN']
            response = requests.get(url, data=data, headers={'api': api_token}, timeout=10)
            rds_logger.info("get_app_company {} {}".format(url, json.dumps(data)))
            if response.json().get('result') == 1:
                return response.json().get('result'), response.json().get('code')
            else:
                rds_logger.error("select_rds_by_app_name error")
                return response.json().get('result'), response.json().get('msg')
        except Exception, e:
            rds_logger.exception("select_rds_by_app_name error: %s", e)

    @staticmethod
    def add_aliyun_rds_white_ip(action, rds_id, group_name, ips, operator, source):
        try:
            data = dict()
            data['rds_id'] = rds_id
            data['group_name'] = group_name
            data['ips'] = ips
            data['operator'] = operator
            data['source'] = source
            url = app.config['CMDB_ALIYUN_URL'] + "/api/core/aliyun/rds/white/" + action
            api_token = app.config['CMDB_ALIYUN_TOKEN']
            response = requests.post(url, data=data, headers={'api': api_token}, timeout=10)
            rds_logger.info("add_aliyun_rds_white_ip {} {}".format(url, json.dumps(data)))
            if response.json().get('result') == 1:
                return response.json().get('result')
            else:
                rds_logger.error("select_rds_by_app_name error")
                return response.json().get('result')
        except Exception, e:
            rds_logger.exception("select_rds_by_app_name error: %s", e)

    @staticmethod
    def get_aliyun_rds_white_groups(rds_id):
        try:
            data = dict()
            data['rds_id'] = rds_id
            url = app.config['CMDB_ALIYUN_URL'] + "/api/core/aliyun/rds/white/groups"
            api_token = app.config['CMDB_ALIYUN_TOKEN']
            response = requests.get(url, data=data, headers={'api': api_token}, timeout=10)
            if response.json().get('result') == 1:
                return response.json().get('data')
            else:
                rds_logger.error("get_aliyun_rds_white_groups error")
                return response.json().get('result')
        except Exception, e:
            rds_logger.exception("get_aliyun_rds_white_groups error: %s", e)


if __name__ == '__main__':
     flag, msg = K8SCoreApp.select_rds_by_app_name('14', 'java-test@ZA', 'rds', 'prd', 'ZA')
     print flag, msg


