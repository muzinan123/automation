# -*- coding: utf8 -*-

import base64
from functools import wraps
from urlparse import urlparse
from flask import session, redirect, request, make_response
from flask_socketio import disconnect

from app.services.framework.sso_service import SsoService
from app.services.framework.user_service import UserService
from app.services.framework.api_service import ApiService
from app.util import Util
from app import app, api_logger, api_list


def api():
    def decorator(f):
        api_list.add(f.__name__)
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('api')
            ip = Util.get_ip_addr()
            func_name = f.__name__
            if ApiService.check_acl(token, ip, func_name):
                api_logger.info("api request with: {}, {}, {}".format(token, ip, func_name))
                return f(*args, **kwargs)
            else:
                return "error", 401
        return decorated_function
    return decorator


def require_login():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'ticket' in request.args:
                valid = SsoService.validate_service(request.args['ticket'])
                if valid:
                    user_id = valid['user_id']
                    user_info = UserService.get_user_info(user_id)
                    user_privileges = UserService.get_user_privileges(user_id)
                    session['token'] = valid['token']
                    session['userId'] = user_id
                    session['userInfo'] = user_info
                    session['userPrivileges'] = user_privileges
                    o = urlparse(request.url)
                    response = make_response(redirect('{}://{}{}'.format(o.scheme, o.netloc, o.path)))
                    response.set_cookie('token', valid['token'])
                    return response
                else:
                    return u"您当前SSO登录的账号没有本系统的使用权限，请发邮件至core@zhongan.com联系开通。",401

            if session.get('token') is None:
                if request.cookies.get('token') is None:
                    return SsoService.redirect_to_sso(request.url)
                else:
                    # app.logger.debug('get token from cookie,make a check')
                    token = request.cookies.get('token')
                    user_id = UserService.check_token(token)
                    if user_id:
                        user_info = UserService.get_user_info(user_id)
                        user_privileges = UserService.get_user_privileges(user_id)
                        # app.logger.debug('token ok,get login')
                        session['token'] = token
                        session['userId'] = user_id
                        session['userInfo'] = user_info
                        session['userPrivileges'] = user_privileges
                        return f(*args, **kwargs)
                    else:
                        # app.logger.debug('token not existes,goto login')
                        return SsoService.redirect_to_sso(request.url)
            else:
                return f(*args, **kwargs)
        return decorated_function
    return decorator


def privilege(privilegeName):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session['userId']
            if request.method=='GET':
                if UserService.has_privilege(user_id, privilegeName, 1):
                    return f(*args, **kwargs)
                else:
                    return u'权限不足',401
            elif request.method == 'POST' or request.method == 'PUT' or request.method == 'DELETE' \
                    or request.method == 'LINK' or request.method == 'UNLINK':
                if UserService.has_privilege(user_id, privilegeName, 2):
                    return f(*args, **kwargs)
                else:
                    return u'权限不足',401
        return decorated_function
    return decorator


def ws_require_login():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('userId') is not None:
                return f(*args, **kwargs)
            else:
                disconnect()
        return decorated_function
    return decorator


def allow_cross_domain():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            rst = make_response(f(*args, **kwargs))
            rst.headers['Access-Control-Allow-Origin'] = '*'
            rst.headers['Access-Control-Allow-Methods'] = 'PUT,GET,POST,DELETE'
            rst.headers['Access-Control-Allow-Headers'] = "Referer,Accept,Origin,User-Agent"
            return rst
        return decorated_function
    return decorator