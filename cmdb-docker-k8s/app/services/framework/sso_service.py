# -*- coding:utf-8 -*-

import json
import urllib2
from urllib import urlencode

from flask import redirect

from app.util import Util
from login_service import LoginService
from user_service import UserService
from app import app


class SsoService(object):

    @staticmethod
    def validate_service( ticket):
        query = dict()
        query['service'] = app.config['SSO_SERVER_URL']
        query['ticket'] = ticket
        url = '{}?{}'.format(
            app.config['SSO_VALIDATE'],
            urlencode(query),
        )
        res = urllib2.urlopen(url).read()
        user = json.loads(res)
        if user.get('username'):
            valid = SsoService.sso_login(user)
            return valid
        else:
            return False

    @staticmethod
    def redirect_to_sso(target_url):
        return redirect('{}?{}'.format(
            app.config['SSO_LOGIN'],
            urlencode({'service': app.config['SSO_SERVER_URL'], 'target': target_url})
        ))

    @staticmethod
    def sso_logout(target_url):
        return redirect('{}?{}'.format(
            app.config['SSO_LOGOUT'],
            urlencode({'target': target_url})
        ))

    @staticmethod
    def sso_login(user):
        name = user.get('username')
        user_id = UserService.is_exist(name)
        if not user_id:
            real_name = user.get('name')
            work_no = user.get('no')
            phone = user.get('phone')
            department = user.get('department')
            sex = user.get('sex')
            email = user.get('email')
            user_id = UserService.add_sso_user(name, email, real_name, work_no, phone, department, sex)

        token = LoginService.give_token(user_id)
        if token:
            login_ip = Util.get_ip_addr()
            LoginService.add_login_history(name, login_ip)
            LoginService.add_user_login_count(user_id)


            valid = dict()
            valid['user_id'] = user_id
            valid['token'] = token
            return valid
