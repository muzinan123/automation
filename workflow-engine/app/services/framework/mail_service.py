# -*- coding:utf-8 -*-

from app.out.mail import Mail
from app import app, task_logger, celery


class MailService(object):

    @staticmethod
    def send_mail(mail_user_list, subject, template_file, datas):
        try:
            if app.config.get('SEND_MAIL'):
                Mail.send.delay(mail_user_list, subject, template_file, datas)
        except Exception as e:
            task_logger.exception("send mail failed: %s", e)
