# -*- coding: utf8 -*-

import requests

from app import app, out_logger


class Regulator(object):

    @staticmethod
    def queryFault(issue_id):
        if issue_id != app.config.get('SPECIAL_ISSUE_ID'):
            url = app.config.get('REGULATOR_URL') + '/api/mission'
            data = {'id': issue_id}
            out_logger.info('url: ' + url)
            out_logger.info(u'data:{} '.format(data))
            try:
                response = requests.get(url, data=data)
                out_logger.info(response.content)
                if response.status_code == 200:
                    result = response.json()
                    if result['success']:
                        status = result['data']['status']
                        if status >= 3:
                            return False, u'您输入的故障单号已关闭，请重新输入'
                        else:
                            return True, u'故障单号验证通过'
                    else:
                        return False, u'您输入的故障单号不存在'
                else:
                    return False, u'查找故障单号失败'
            except Exception, e:
                out_logger.exception('query fault data error: %s', e)
                return False, u'调用故障单号接口异常'
        else:
            return True, u'缺省故障单号免验证'
