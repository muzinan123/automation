# -*- coding: utf8 -*-

from app.services.framework.notification_service import NotificationService
from app.services.framework.mail_service import MailService


class MessageService(object):

    @staticmethod
    def code_review(datas, to_list):
        subject = u'项目CodeReview通知'
        template_file = 'project_code_review.txt'
        url = datas['url']
        content = '''<a href="''' + url + '''">您有一个代码评审需要处理</a>'''
        message_type = "code_review"
        mail_user_list = dict()
        for u in set(to_list):
            if u.send_mail:
                mail_user_list[u.real_name] = u.email
        MailService.send_mail(mail_user_list, subject, template_file, datas)
        NotificationService.add(content, message_type, [u.id for u in to_list])

    #发布完成后，调用邮箱
    @staticmethod
    def release_success(datas, to_list):
        subject = u'项目发布完成通知'
        template_file = 'project_release_success.txt'
        mail_user_list = dict()
        mail_user_list[to_list.get('real_name')] = to_list.get('email')
        MailService.send_mail(mail_user_list, subject, template_file, datas)

    @staticmethod
    def sql_review(datas):
        subject = u'项目SQLReview通知'
        template_file = 'project_sql_review.txt'
        MailService.send_mail({'DBA': 'dba@zhongan.com'}, subject, template_file, datas)

    @staticmethod
    def test_verify(datas, to_list):
        subject = u'项目测试验证通知'
        template_file = 'project_test.txt'
        url = datas['url']
        content = '''<a href="''' + url + '''">您有一个测试验证需要处理</a>'''
        message_type = "test_verify"
        mail_user_list = dict()
        for u in set(to_list):
            if u.send_mail:
                mail_user_list[u.real_name] = u.email
        MailService.send_mail(mail_user_list, subject, template_file, datas)
        NotificationService.add(content, message_type, [u.id for u in to_list])

    @staticmethod
    def apply_publish(datas, to_list):
        subject = u'项目待申请发布'
        template_file = 'project_ready.txt'
        url = datas['url']
        content = '''<a href="''' + url + '''">您有一个项目待申请发布</a>'''
        message_type = "apply_publish"
        mail_user_list = dict()
        for u in set(to_list):
            if u.send_mail:
                mail_user_list[u.real_name] = u.email
        MailService.send_mail(mail_user_list, subject, template_file, datas)
        NotificationService.add(content, message_type, [u.id for u in to_list])

    @staticmethod
    def publish_abandon(datas, to_list):
        subject = u'发布废弃通知'
        template_file = 'publish_abandon.txt'
        url = datas['url']
        content = '''<a href="''' + url + '''">您有一个发布单废弃</a>'''
        message_type = 'publish_abandon'
        mail_user_list = dict()
        for u in set(to_list):
            if u.send_mail:
                mail_user_list[u.real_name] = u.email
        MailService.send_mail(mail_user_list, subject, template_file, datas)
        NotificationService.add(content, message_type, [u.id for u in to_list])

    @staticmethod
    def sql_review_timeout(datas):
        subject = u'项目SQLReview审核超时通知'
        template_file = 'project_sql_review_timeout.txt'
        MailService.send_mail({'DBA': 'dba@zhongan.com'}, subject, template_file, datas)

    @staticmethod
    def sql_execute_timeout(datas):
        subject = u'项目SQL执行超时通知'
        template_file = 'project_sql_execute_timeout.txt'
        MailService.send_mail({'DBA': 'dba@zhongan.com'}, subject, template_file, datas)

    @staticmethod
    def manual_sql_execute(datas):
        subject = u'项目SQL人工执行通知'
        template_file = 'project_manual_sql_review.txt'
        MailService.send_mail({'DBA': 'dba@zhongan.com'}, subject, template_file, datas)

    @staticmethod
    def sql_execute_failed(datas, to_list):
        subject = u'项目SQL执行失败'
        template_file = 'project_sql_execute_failed.txt'
        MailService.send_mail(to_list, subject, template_file, datas)


