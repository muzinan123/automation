# -*- coding:utf-8 -*-

from app import app, celery, out_logger
import requests


class Mail(object):

    @staticmethod
    @celery.task
    def send(to_list, subject, template_file, content):
        try:
            if app.config.get('SEND_MAIL'):
                url = app.config.get('MAIL_URL') + '/mail/send'
                headers = {"api": app.config.get('MAIL_API_TOKEN')}
                data = {"system": 'duang', "to_list": to_list, "subject": subject, "template_file": template_file,
                        "content": content}
                out_logger.info(u"data: {}".format(data))
                response = requests.post(url, headers=headers, json=data)
                out_logger.info(response.content)
        except Exception, e:
            out_logger.exception('send mail error: %s', e)
