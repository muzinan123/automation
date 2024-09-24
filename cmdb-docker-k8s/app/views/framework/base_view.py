# -*- coding:utf-8 -*-

from flask import Blueprint, request, session, make_response, url_for, render_template, jsonify
from app.services.framework.role_service import RoleService
from app.services.framework.sso_service import SsoService
from app.services.framework.user_service import UserService
from app.services.framework.privilege_service import PrivilegeService
from app.services.framework.login_service import LoginService
from app.services.framework.scheduler_service import SchedulerService
from app.services.framework.notification_service import NotificationService
from app.services.framework.api_service import ApiService
from app.decorators.access_control import require_login, privilege
from app.decorators.paginate import make_paging
from app.util import Util
from app import app

baseProfile = Blueprint('baseProfile', __name__)


@app.route('/logout', methods=['GET'])
def logout():
    if session.has_key('token'):
        session.pop('token')
    response = make_response(SsoService.sso_logout(url_for('cover', _external=True)))
    response.set_cookie('token', '')
    return response


@app.route('/', methods=['GET'])
def cover():
    return render_template('framework/cover.html')


@app.route('/home', methods=['GET'])
@require_login()
def home():
    #show index
    return render_template('framework/index.html', title=u'首页')


@app.route('/admin-user', methods=['GET'])
@require_login()
@privilege('admin_user')
def admin_user():
    #show admin-user
    return render_template('framework/admin-user.html',title=u'用户管理')


@app.route('/admin-user/user', methods=['PUT', 'DELETE', 'POST', 'GET'])
@make_paging('userList')
@require_login()
@privilege('admin_user')
def admin_user__user():
    if request.method == 'GET':
        query = request.values.get('query')
        data = UserService.get_users(query=query)
        return data
    elif request.method == 'DELETE':
        id = request.values.get('id')
        enabled = request.values.get('enabled')
        if id and Util.can_tune_to(enabled, int):
            UserService.mod_user(id, None, None, None, enabled)
            ret = dict()
            ret['result'] = 1
            return jsonify(ret)
    elif request.method == 'POST':
        id = request.values.get('id')
        phone = request.values.get('phone')
        email = request.values.get('email')
        role_id = request.values.get('roleId')
        if id and Util.can_tune_to(role_id, int):
            UserService.mod_user(id, phone, email, role_id, None)
            ret = dict()
            ret['result'] = 1
            return jsonify(ret)
    return "error", 400


@app.route('/admin-role', methods=['GET'])
@require_login()
@privilege('admin_user')
def admin_role():
    return render_template('framework/admin-role.html',title=u'权限管理')


@app.route('/admin-role/role', methods=['PUT', 'DELETE', 'POST', 'GET', 'LINK'])
@require_login()
@privilege('admin_user')
def admin_role__role():
    if request.method == 'GET':
        ret = dict()
        ret['result'] = 1
        role_list = RoleService.get_role()
        ret['data'] = [e.serialize() for e in role_list]
        return jsonify(ret)
    elif request.method == 'PUT':
        name = request.values.get('name')
        alias = request.values.get('alias')
        if name and alias:
            ret = dict()
            if not RoleService.is_exist(name):
                RoleService.add_role(name,alias)
                ret['result'] = 1
            else:
                ret['result'] = 2
            return jsonify(ret)
    elif request.method == 'DELETE':
        id = request.values.get('id')
        if id and Util.can_tune_to(id, int):
            RoleService.del_role(int(id))
            ret = dict()
            ret['result'] = 1
            return jsonify(ret)
    elif request.method == 'POST':
        id = request.values.get('id')
        alias = request.values.get('alias')
        if id and Util.can_tune_to(id, int) and alias:
            RoleService.mod_role(int(id), alias)
            ret = dict()
            ret['result'] = 1
            return jsonify(ret)
    elif request.method == 'LINK':
        user_id = request.values.get('userId')
        role_id = request.values.get('roleId')
        if user_id and Util.can_tune_to(user_id, int) and role_id and Util.can_tune_to(role_id, int):
            RoleService.link_user_role(user_id, role_id)
            ret = dict()
            ret['result'] = 1
            return jsonify(ret)
    return "error", 400


@app.route('/admin-role/privilege', methods=['PUT', 'DELETE', 'POST', 'GET', 'LINK'])
@require_login()
@privilege('admin_user')
def admin_role__privilege():
    if request.method == 'GET':
        role_id = request.values.get('roleId')
        if role_id:
            if Util.can_tune_to(role_id, int):
                ret = dict()
                ret['result'] = 1
                privilege_list = PrivilegeService.get_role_privileges(role_id)
                ret['data'] = [e.serialize() for e in privilege_list]
                return jsonify(ret)
        else:
            ret = dict()
            ret['result'] = 1
            privilege_list = PrivilegeService.get_privileges()
            ret['data'] = [e.serialize() for e in privilege_list]
            return jsonify(ret)
    elif request.method == 'PUT':
        name = unicode(request.values.get('name'))
        alias = unicode(request.values.get('alias'))
        if name and alias:
            ret = dict()
            if not PrivilegeService.is_exist(name):
                PrivilegeService.add_privilege(name, alias)
                ret['result'] = 1
            else:
                ret['result'] = 2
            return jsonify(ret)
    elif request.method == 'DELETE':
        id = request.values.get('id')
        if id and Util.can_tune_to(id, int):
            PrivilegeService.del_privilege(int(id))
            ret = dict()
            ret['result'] = 1
            return jsonify(ret)
    elif request.method == 'POST':
        id = request.values.get('id')
        alias = request.values.get('alias')
        if id and alias and Util.can_tune_to(int(id), int):
            PrivilegeService.mod_privilege(id, alias)
            ret = dict()
            ret['result'] = 1
            return jsonify(ret)
    elif request.method == 'LINK':
        role_id = request.values.get('roleId')
        privilege_id = request.values.get('privilegeId')
        read = unicode(request.values.get('read'))
        write = unicode(request.values.get('write'))
        if role_id and privilege_id and read and write and Util.can_tune_to(role_id, int) \
                and Util.can_tune_to(privilege_id, int):
            PrivilegeService.link_role_privilege(int(role_id), int(privilege_id), read == '1', write == '1')
            ret = dict()
            ret['result'] = 1
            return jsonify(ret)
    return "error", 400


@app.route('/login-his', methods=['GET'])
@require_login()
@privilege('admin_user')
def login_his():
    return render_template('framework/login-his.html',title=u'登录记录')


@app.route('/login-his/his', methods=['GET'])
@make_paging('hisList')
@require_login()
@privilege('admin_user')
def login_his__his():
    query = request.values.get('query')
    login_at = Util.check_date_str(request.values.get('loginAt'))
    data = LoginService.get_login_history(query, login_at)
    return data


@app.route('/task-runonce', methods=['GET'])
@require_login()
@privilege('task_config')
def task_runonce():
    return render_template('framework/task-runonce.html', title=u'手工调度')


@app.route('/task-runonce/runonce', methods=['POST'])
@require_login()
@privilege('task_config')
def task_runonce__runonce():
    task = request.values.get('task')
    args = request.values.get('args', '[]')
    kwargs = request.values.get('kwargs', '{}')
    if not args:
        args = '[]'
    if not kwargs:
        kwargs = '{}'
    if task:
        ret = dict()
        if SchedulerService.run_task_once(task, args, kwargs):
            ret['result'] = 1
            return jsonify(ret)
    return "error", 400


@app.route('/task-config', methods=['GET'])
@require_login()
@privilege('task_config')
def task_config():
    return render_template('framework/task-config.html', title=u'任务配置')


@app.route('/task-config/schedule', methods=['GET', 'PUT', 'DELETE', 'POST'])
@require_login()
@privilege('task_config')
def task_config__schedule():
    if request.method == 'GET':
        sid = request.values.get('id')
        if sid and Util.can_tune_to(sid, int):
            ret = dict()
            ret['result'] = 1
            ret['data'] = SchedulerService.get_schedule_detail(int(sid))
            return jsonify(ret)
        else:
            ret = dict()
            ret['result'] = 1
            ss = SchedulerService.get_schedule_list()
            ret['data'] = [e.serialize() for e in ss]
            return jsonify(ret)
    elif request.method == 'DELETE':
        sid = request.values.get('id')
        if sid and Util.can_tune_to(sid, int):
            ret = dict()
            ret['result'] = 1
            SchedulerService.del_schedule(int(sid))
            return jsonify(ret)
    elif request.method == 'PUT':
        name = request.values.get('name')
        task = request.values.get('task')
        args = request.values.get('args')
        kwargs = request.values.get('kwargs')
        enabled = request.values.get('enabled')
        every = request.values.get('every')
        period = request.values.get('period')
        minute = request.values.get('minute')
        hour = request.values.get('hour')
        day_of_week = request.values.get('day_of_week')
        day_of_month = request.values.get('day_of_month')
        month_of_year = request.values.get('month_of_year')
        if every and Util.can_tune_to(every, int):
            ret = dict()
            ret['result'] = 1
            SchedulerService.add_schedule(name, task, args, kwargs, enabled, every=every, period=period)
            return jsonify(ret)
        elif minute or hour or day_of_week or day_of_month or month_of_year:
            ret = dict()
            ret['result'] = 1
            SchedulerService.add_schedule(name, task, args, kwargs, enabled, minute=minute, hour=hour,
                                          day_of_week=day_of_week, day_of_month=day_of_month,
                                          month_of_year=month_of_year)
            return jsonify(ret)
    elif request.method == 'POST':
        sid = request.values.get('id')
        if sid and Util.can_tune_to(sid, int):
            name = request.values.get('name')
            task = request.values.get('task')
            args = request.values.get('args')
            kwargs = request.values.get('kwargs')
            if request.values.get('enabled') == 'true':
                enabled = True
            else:
                enabled = False
            every = request.values.get('every')
            period = request.values.get('period')
            minute = request.values.get('minute')
            hour = request.values.get('hour')
            day_of_week = request.values.get('day_of_week')
            day_of_month = request.values.get('day_of_month')
            month_of_year = request.values.get('month_of_year')
            if every and Util.can_tune_to(every, int):
                ret = dict()
                ret['result'] = 1
                SchedulerService.mod_schedule(sid, name, task, args, kwargs, enabled, every=every, period=period)
                return jsonify(ret)
            elif minute or hour or day_of_week or day_of_month or month_of_year:
                ret = dict()
                ret['result'] = 1
                SchedulerService.mod_schedule(sid, name, task, args, kwargs, enabled, minute=minute, hour=hour,
                                              day_of_week=day_of_week, day_of_month=day_of_month,
                                              month_of_year=month_of_year)
                return jsonify(ret)
    return "error", 400


@app.route('/task-config/task', methods=['GET'])
@require_login()
@privilege('task_config')
def task_config__task():
    ret = dict()
    ret['result'] = 1
    ts = SchedulerService.get_task_list()
    ret['data'] = ts
    return jsonify(ret)


@app.route('/task-his', methods=['GET'])
@require_login()
@privilege('task_config')
def task_his():
    return render_template('framework/task-his.html', title=u'执行记录')


@app.route('/task-his/his', methods=['GET'])
@make_paging('hisList')
@require_login()
@privilege('task_config')
def task_his__his():
    query = request.values.get('query', '')
    start_at = Util.check_date_str(request.values.get('startAt'))
    data = SchedulerService.get_task_history(query, start_at)
    return data


@app.route('/task-his/his/detail', methods=['GET'])
@require_login()
@privilege('task_config')
def task_his__his_detail():
    sh_id = request.values.get('id')
    if sh_id and Util.can_tune_to(sh_id, int):
        td = SchedulerService.get_task_history_detail(int(sh_id))
        ret = dict()
        if td:
            ret['result'] = 1
            ret['data'] = td
        else:
            ret['result'] = 2
        return jsonify(ret)
    return "error", 400


@app.route('/user-center', methods=['GET', 'POST'])
@require_login()
def user_center():
    if request.method == 'GET':
        u = UserService.get_user(session['userId'])
        return render_template('framework/user-center.html', title=u'用户中心', user=u)
    elif request.method == 'POST':
        user_id = session['userId']
        phone = request.values.get('phone')
        email = request.values.get('email')
        UserService.mod_user(user_id, phone, email, None, None)
        ret = dict()
        ret['result'] = 1
        return jsonify(ret), 200
    return "error", 400


@app.route('/notification/check', methods=['GET'])
@require_login()
def notification_check():
    user_id = session['userId']
    data = dict()
    data['unreaded'] = NotificationService.get_unreaded(user_id)
    ret = dict()
    ret['result'] = 1
    ret['data'] = data
    return jsonify(ret)


@app.route('/notification/list', methods=['GET'])
@require_login()
def notification_list():
    return render_template('framework/notification-list.html', title=u'通知列表')


@app.route('/notification/list/list', methods=['GET', 'POST'])
@make_paging('msgList')
@require_login()
def notification_list__list():
    if request.method == 'GET':
        query = request.values.get('query', '')
        create_at = Util.check_date_str(request.values.get('createAt'))
        user_id = session.get('userId')
        data = NotificationService.list_by_user(user_id, query, create_at)
        return data
    elif request.method == 'POST':
        msg_id = request.values.get('id', '')
        all = request.values.get('all', False)
        if all:
            NotificationService.all_readed(session.get('userId'))
            ret = dict()
            ret['result'] = 1
            return jsonify(ret)
        if Util.can_tune_to(msg_id, int):
            NotificationService.readed(msg_id)
            ret = dict()
            ret['result'] = 1
            return jsonify(ret)
    return "error", 400


@app.route('/health', methods=['GET'])
def health():
    return "ok", 200


@app.route('/api/list', methods=['GET'])
@privilege('admin_user')
def api_list():
    return render_template('framework/admin-api.html', title=u'API管理')


@app.route('/api/list__acl', methods=['GET', 'PUT', 'DELETE', 'POST'])
@make_paging('aclList')
@privilege('admin_user')
def api_list__acl():
    if request.method == 'GET':
        query = request.values.get('query')
        data = ApiService.list_acl(query)
        return data
    elif request.method == 'PUT':
        app_name = request.values.get('app')
        token = request.values.get('token')
        ip = request.values.get('ip')
        api_name = request.values.get('api_name')
        result = ApiService.add_acl(app_name, token, ip, api_name, session.get('userId'))
        ret = dict()
        if result:
            ret['result'] = 1
            return jsonify(ret)
        else:
            ret['result'] = -1
            return jsonify(ret)
    elif request.method == 'DELETE':
        acl_id = request.values.get('acl_id')
        result = ApiService.del_acl(acl_id)
        ret = dict()
        if result:
            ret['result'] = 1
            return jsonify(ret)
        else:
            ret['result'] = -1
            return jsonify(ret)
    elif request.method == 'POST':
        acl_id = request.values.get('acl_id')
        app_name = request.values.get('app')
        token = request.values.get('token')
        ip = request.values.get('ip')
        api_name = request.values.get('api_name')
        enabled = request.values.get('enabled') == 'true'
        if acl_id:
            result = ApiService.mod_acl(acl_id, app_name, token, ip, api_name, enabled)
            ret = dict()
            if result:
                ret['result'] = 1
                return jsonify(ret)
            else:
                ret['result'] = -1
                return jsonify(ret)
    return "error", 400


@app.route('/api/list__api', methods=['GET'])
@privilege('admin_user')
def api_list__api():
    ret = dict()
    ret['result'] = 1
    ret['data'] = ApiService.list_api()
    return jsonify(ret)
