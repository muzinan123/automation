# -*- coding:utf8 -*-

import datetime
from flask import Blueprint, jsonify, render_template, request, session

from app.decorators.access_controle import require_login
from app.services.notice_system_service import noticeSystemService

noticeSystem = Blueprint('noticeSystem', __name__)


@noticeSystem.route("/notice_system", methods=['GET'])
@require_login()
def notice_system():
    return render_template('framework/notice_system.html')


@noticeSystem.route("/home_notice_system", methods=['GET'])
@require_login()
def home_notice_system():
    week_day = datetime.datetime.now().weekday()
    week_day += 1
    data = dict()
    data1 = noticeSystemService.home_notice(str(week_day))
    if data1:
        data["noticeContent"] = data1.get("content")
    data2 = noticeSystemService.home_systemupdate()
    if data2:
        data["systemContent"] = data2[0].get("content")
    ret = dict()
    ret['result'] = 1
    ret['data'] = data
    return jsonify(ret)


# 公告提示---操作
@noticeSystem.route("/notice_operation", methods=['GET', 'PUT', 'POST'])
@require_login()
def notice_operation():
    if request.method == 'GET':
        week_day = request.values.get('week_day')
        ret = dict()
        data = noticeSystemService.notice_find_list(week_day)
        ret['result'] = 1
        ret['data'] = [e for e in data]
        return jsonify(ret)
    elif request.method == 'PUT':
        week_day = request.values.get('week_day')
        ret = dict()
        content = request.values.get('content')
        result = noticeSystemService.notice_insert(content, week_day, session['userId'])
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    elif request.method == 'POST':
        week_day = request.values.get('week_day')
        ret = dict()
        content = request.values.get('content')
        result = noticeSystemService.notice_update(content, week_day)
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    return "error", 400


# 系统更新说明----操作
@noticeSystem.route("/system_operation", methods=['GET', 'PUT', 'POST'])
@require_login()
def system_operation():
    if request.method == 'GET':
        ret = dict()
        data = noticeSystemService.system_find_list()
        ret['result'] = 1
        ret['data'] = data
        return jsonify(ret)
    elif request.method == 'PUT':
        ret = dict()
        content = request.values.get('content')
        result = noticeSystemService.system_insert(content, session['userId'])
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    elif request.method == 'POST':
        ret = dict()
        content = request.values.get('content')
        result = noticeSystemService.system_update(content)
        if result:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    return "error", 400
