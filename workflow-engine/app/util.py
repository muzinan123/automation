# -*- coding: utf8 -*-

import collections
import redis as redispy
from redis.sentinel import Sentinel
from flask import request
from app import app
from celery import Celery
import re
import pytz
import socket
import xlwt
import cStringIO, io
import rsa
import base64


class Util(object):

    if app.config.get('REDIS_CLUSTER'):
        sentinel = Sentinel(app.config['REDIS_SENTINEL_LIST'], socket_timeout=0.1)
        redis = sentinel.master_for(app.config['REDIS_CLUSTER_NAME'], db=app.config['REDIS_DB'], socket_timeout=2)
    else:
        redis = redispy.StrictRedis(app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=app.config['REDIS_DB'],
                                    password=app.config['REDIS_PASS'])

    @staticmethod
    def can_tune_to(v, t):
        try:
            t(v)
            return True
        except ValueError:
            return False

    @staticmethod
    def jsbool2pybool(val):
        if val == 'true':
            return True
        elif val == 'false':
            return False

    @staticmethod
    def make_celery(app):
        celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
        celery.conf.update(app.config)
        TaskBase = celery.Task

        class ContextTask(TaskBase):
            abstract = True

            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)

        celery.Task = ContextTask
        return celery

    @staticmethod
    def check_date_str(s):
        try:
            if re.match('\d\d\d\d-\d\d-\d\d', s):
                return s
        except:
            return None
        return None

    @staticmethod
    def utc2local(d):
        local_tz = pytz.timezone(app.config.get('TIMEZONE'))
        local_dt = d.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_tz.normalize(local_dt)

    @staticmethod
    def get_ip_addr():
        ip1 = request.headers.get('X-Forwarded-For')
        ip2 = request.headers.get('X-Real-Ip')
        ip3 = request.remote_addr
        if ip1:
            return ip1.split(',')[0]
        elif ip2:
            return ip2.split(',')[0]
        else:
            return ip3

    @staticmethod
    def check_port_open(ip, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((ip, int(port)))
            s.shutdown(2)
            return True
        except:
            return False

    @staticmethod
    def deep_update(d, u):
        for k, v in u.iteritems():
            if isinstance(v, collections.Mapping):
                d[k] = Util.deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    @staticmethod
    def change_project_type(type):
        project_type = ''
        if type == 'code_optimization':
            project_type = u'代码优化'
        elif type == 'system_fault':
            project_type = u'系统故障'
        elif type == 'bug_repairs':
            project_type = u'缺陷修复'
        elif type == 'requirement_change':
            project_type = u'需求变更'
        elif type == 'new_product':
            project_type = u'新产品'
        elif type == 'new_feature':
            project_type = u'新功能'
        elif type == 'others':
            project_type = u'其他'
        return project_type

    @staticmethod
    def change_app_type(type):
        app_type = 0
        if type == 'app':
            app_type = 0
        elif type == 'open':
            app_type = 1
        elif type == 'module':
            app_type = 2
        return app_type

    @staticmethod
    def export_excel(book):
        wbk = xlwt.Workbook(encoding='utf-8')
        style = xlwt.XFStyle()
        style.alignment.wrap = 1
        for sheet_name, sheet_content in book.items():
            sheet = wbk.add_sheet(sheet_name, cell_overwrite_ok=True)
            data = sheet_content['data']
            headers = sheet_content['headers']
            for i in xrange(len(headers)):
                sheet.write(0, i, headers[i]['name'])
                j = 1
                for d in data:
                    val = d.get(headers[i]['key'])
                    v = unicode(val if val is not None else '')
                    if str(type(d[headers[i]['key']])) == '<type \'list\'>':
                        v = ''
                        for l in d[headers[i]['key']]:
                            print l
                            v += unicode(l) + u'\r\n'
                    else:
                        if headers[i]['key'] == 'type':
                            if d.get('type') == 'code_optimization':
                                v = u'代码优化'
                            elif d.get('type') == 'system_fault':
                                v = u'系统故障'
                            elif d.get('type') == 'bug_repairs':
                                v = u'缺陷修复'
                            elif d.get('type') == 'requirement_change':
                                v = u'需求变更'
                            elif d.get('type') == 'new_product':
                                v = u'新产品'
                            elif d.get('type') == 'new_feature':
                                v = u'新功能'
                            elif d.get('type') == 'others':
                                v = u'其他'
                        elif headers[i]['key'] == 'publish_type':
                            if d.get('publish_type') == 'regular':
                                v = u'常规发布'
                            else:
                                v = u'紧急发布'
                        elif headers[i]['key'] == 'status':
                            if d.get('status') == 'prd_complete':
                                v = u'完成'
                            else:
                                v = u'废弃'
                        elif headers[i]['key'] == 'description':
                            if d.get('description') == 'prd_complete':
                                v = u'发布完成'
                            else:
                                v = u'发布回退'
                        elif headers[i]['key'] == 'abandon_reason':
                            if d.get('abandon_reason') == 'pre_not_pass_reason_exist_bug':
                                v = u'预发验证回退:存在Bug'
                            elif d.get('abandon_reason') == 'pre_not_pass_reason_publish_problem':
                                v = u'预发验证回退:发布问题'
                            elif d.get('abandon_reason') == 'pre_not_pass_reason_commit_problem':
                                v = u'预发验证回退:代码漏提交'
                            elif d.get('abandon_reason') == 'pre_not_pass_reason_code_conflict':
                                v = u'预发验证回退:代码冲突'
                            elif d.get('abandon_reason') == 'pre_not_pass_reason_code_stale':
                                v = u'预发验证回退:不是最新代码'
                            elif d.get('abandon_reason') == 'pre_not_pass_reason_other':
                                v = u'预发验证回退:其他'
                            if d.get('abandon_reason') == 'owner_rollback_reason_exist_bug':
                                v = u'项目owner自主回退:存在Bug'
                            elif d.get('abandon_reason') == 'owner_rollback_reason_publish_problem':
                                v = u'项目owner自主回退:发布问题'
                            elif d.get('abandon_reason') == 'owner_rollback_reason_commit_problem':
                                v = u'项目owner自主回退:代码漏提交'
                            elif d.get('abandon_reason') == 'owner_rollback_reason_code_conflict':
                                v = u'项目owner自主回退:代码冲突'
                            elif d.get('abandon_reason') == 'owner_rollback_reason_code_stale':
                                v = u'项目owner自主回退:不是最新代码'
                            elif d.get('abandon_reason') == 'owner_rollback_reason_other':
                                v = u'项目owner自主回退:其他'

                    sheet.write(j, i, v, style)
                    j += 1
        buf = cStringIO.StringIO()
        wbk.save(buf)
        return io.BytesIO(buf.getvalue())

    @staticmethod
    def rsa_encrypt(message):
        # load公钥和密钥
        p = app.config['RSA_PUB_PEM']
        pubkey = rsa.PublicKey.load_pkcs1(p)

        # 用公钥加密、再用私钥解密
        crypto = rsa.encrypt(message, pubkey)
        return base64.b64encode(crypto)

    @staticmethod
    def rsa_decrypt(base64_crypto):
        # load公钥和密钥
        p = app.config['RSA_PRI_PEM']
        privkey = rsa.PrivateKey.load_pkcs1(p)

        # 用公钥加密、再用私钥解密
        crypto = base64.b64decode(base64_crypto)
        message = rsa.decrypt(crypto, privkey)
        return message
