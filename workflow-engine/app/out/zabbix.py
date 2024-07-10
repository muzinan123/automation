# -*- coding: utf8 -*-
import requests
from app import app
from app.util import Util
from app import out_logger


class Zabbix(object):

    url = app.config.get('ZABBIX_URL')
    
    @staticmethod
    def query_token():
        try:
            token = Util.redis.get('zabbix_token')
            if token:
                return token
            user_name = app.config.get("ZABBIX_USER_NAME")
            password = app.config.get("ZABBIX_PASSWORD")
            login_info = {"user": user_name, "password": password}
            data = {"jsonrpc": "2.0", "method": "user.login", "id": 1, "params": login_info}
            out_logger.info("url: " + Zabbix.url)
            out_logger.info(u"data:{}".format(data))
            login_res = requests.post(Zabbix.url, json=data)
            out_logger.info(login_res.content)
            rst = login_res.json()
            token = rst.get('result')
            Util.redis.set('zabbix_token', token)
            Util.redis.expire('zabbix_token', 1800)
            return token
        except Exception, e:
            out_logger.exception("query zabbix(user.login) exception", e)

    @staticmethod
    def query_host_info(app_ip):
        try:
            token = Zabbix.query_token()
            hostid = ""
            params = {"filter": {"ip": [app_ip]}}
            data = {"jsonrpc": "2.0", "method": "host.get", "id": 1, "auth": token, "selectInterfaces": "extend", "params": params}
            out_logger.info("url: " + Zabbix.url)
            out_logger.info(u"data:{}".format(data))
            host_res = requests.post(Zabbix.url, json=data)
            out_logger.info(host_res.content)
            rst = host_res.json().get('result')
            if len(rst) > 0:
                hostid = host_res.json().get('result')[0].get("hostid")
            return hostid
        except Exception, e:
            out_logger.exception("query zabbix(host.get) exception", e)

    @staticmethod
    def query_httptest_info(hostid, port):
        try:
            httptest_id = ""
            token = Zabbix.query_token()
            params = {"output": "extend", "hostids": hostid, "selectSteps": "extend"}
            data = {"jsonrpc": "2.0", "method": "httptest.get", "id": 1, "auth": token, "params": params}
            out_logger.info("url: " + Zabbix.url)
            out_logger.info(u"data:{}".format(data))
            httptest_res = requests.post(Zabbix.url, json=data)
            out_logger.info(httptest_res.content)
            rst = httptest_res.json().get('result')
            for e in rst:
                lst = e.get("name").split('-')
                eport = e.get("name").split('-')[len(lst)-1]
                if eport == port:
                    httptest_id = e.get('httptestid')
            return httptest_id
        except Exception, e:
            out_logger.exception("query zabbix(httptest.get) exception", e)

    @staticmethod
    def httptest_update(httptest_id, status):
        try:
            token = Zabbix.query_token()
            params = {"httptestid": httptest_id, "status": status}
            data = {"jsonrpc": "2.0", "method": "httptest.update", "id": 1, "auth": token, "params": params}
            out_logger.info("url: " + Zabbix.url)
            out_logger.info(u"data:{}".format(data))
            update_res = requests.post(Zabbix.url, json=data)
            out_logger.info(update_res.content)
            return True
        except Exception, e:
            out_logger.exception("query zabbix(httptest.update) exception", e)
            return False

    @staticmethod
    def create_host(host_ip, group_id):
        try:
            token = Zabbix.query_token()
            params = {"host": host_ip, "interfaces": [{"type": 1, "main": 1, "useip": 1, "ip": host_ip, "dns": "", "port": app.config['ZABBIX_DEFAULT_PORT']}],
                      "groups": [{"groupid": group_id}], "templates": [{"templateid": app.config['ZABBIX_DEFAULT_TEMPLATE_ID']}]}
            data = {"jsonrpc": "2.0", "method": "host.create", "id": 1, "auth": token, "params": params}
            out_logger.info("url: " + Zabbix.url)
            out_logger.info(u"data:{}".format(data))
            host_add_res = requests.post(Zabbix.url, json=data)
            out_logger.info(host_add_res.content)
            host_id = host_add_res.json().get('result').get("hostids")[0]
            return host_id
        except Exception, e:
            out_logger.exception("query zabbix(host.create) exception", e)

    @staticmethod
    def create_httptest(app_ip, port, hostid, check_url):
        try:
            token = Zabbix.query_token()
            name = "WebChecker-" + port
            url = "http://" + app_ip + ":" + port + check_url
            params = {"name": name , "hostid": hostid, "steps": [{"name": "Testpage", "url": url, "status_codes": 200, "no": 1}]}
            data = {"jsonrpc": "2.0", "method": "httptest.create", "id": 1, "auth": token, "params": params}
            out_logger.info("url: " + Zabbix.url)
            out_logger.info(u"data:{}".format(data))
            httptest_add_res = requests.post(Zabbix.url, json=data)
            out_logger.info(httptest_add_res.content)
            httptest_id = httptest_add_res.json().get('result').get("httptestids")[0]
            return httptest_id
        except Exception, e:
            out_logger.exception("query zabbix(httptest.create) exception", e)

    @staticmethod
    def query_app_group_id(app_dpmt_name=None):
        try:
            token = Zabbix.query_token()
            if not app_dpmt_name:
                return app.config['ZABBIX_DEFAULT_DEPARTMENT']
            else:
                params = {"output": "extend", "filter": {"name": [app_dpmt_name]}}
                data = {"jsonrpc": "2.0", "method": "hostgroup.get", "id": 1, "auth": token, "params": params}
                out_logger.info("url: " + Zabbix.url)
                out_logger.info(u"data:{}".format(data))
                group_res = requests.post(Zabbix.url, json=data)
                out_logger.info(group_res.content)
                group_id = group_res.json().get('result')[0].get('groupid')
                return group_id
        except Exception, e:
            out_logger.exception("query zabbix(hostgroup.get) exception", e)
