# -*- coding: utf8 -*-

import requests

from app import app, out_logger


class Jaguar(object):

    @staticmethod
    def check_working_status():
        try:
            response = requests.get("{}/default-topology/working-status/query".format(app.config['JAGUAR_MAKEUP_URL']))
            out_logger.info(response.content)
            if response.status_code == 200:
                return response.json().get('canKillTopology')
        except Exception, e:
            out_logger.exception("check_working_status error: %s", e)
