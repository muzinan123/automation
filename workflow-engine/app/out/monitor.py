# -*- coding: utf8 -*-
import requests
from app import app
from app import out_logger
from app.out.apprepo import Apprepo


class Monitor(object):

    @staticmethod
    def monitor_start(host, port, check_url, app_name, app_owner_list, app_contacts_list):
        monitor_url = app.config.get('MONITOR_HEALTH_CHECK_URL') + "/startHealthCheck"
        try:
            emails = list()
            if app_contacts_list:
                for contact in app_contacts_list:
                    emails.append(contact['email'])
            if app_owner_list:
                for owner in app_owner_list:
                    emails.append(owner['email'])
            emails.extend(app.config.get('MONITOR_HEALTH_CHECK_DEFAULT'))
            emails = list(set(emails))
            full_check_url = "http://{}:{}{}".format(host, port, check_url)
            data = {"appName": app_name, "checkUrl": full_check_url, "contacts": ','.join(emails), "cron": 300}
            # 下线健康检查
            # out_logger.info("url: " + monitor_url)
            # out_logger.info(u"data:{}".format(data))
            # monitor_res = requests.post(monitor_url, json=data)
            # out_logger.info(monitor_res.content)
            return True
        except Exception, e:
            out_logger.exception("process enabling monitor health check failed %s ", e)
            return False

    @staticmethod
    def monitor_stop(host, port, app_name, check_url):
        monitor_url = app.config.get('MONITOR_HEALTH_CHECK_URL') + "/closeHealthCheck"
        try:
            full_check_url = "http://{}:{}{}".format(host, port, check_url)
            data = {"appName": app_name, "checkUrl": full_check_url}
            # 下线健康检查
            # out_logger.info("url: " + monitor_url)
            # out_logger.info(u"data:{}".format(data))
            # monitor_res = requests.post(monitor_url, json=data)
            # out_logger.info(monitor_res.content)
            return True
        except Exception, e:
            out_logger.exception("process enabling monitor health check failed %s", e)
            return False
