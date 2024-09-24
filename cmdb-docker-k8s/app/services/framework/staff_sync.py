# -*- coding:utf-8 -*-

import hashlib
import json
import time
from datetime import datetime
import requests
from app.models.framework.User import User

from app import app
from app.models import db
from app.models.framework.Department import Department
from app.services.framework.recycle_service import RecycleService


class StaffSync(object):

    department_list_url = 'http://staff.zhonganonline.com/staff/api/zfl/department/query/all'
    user_list_url = 'http://staff.zhonganonline.com/staff/api/query/all'

    @staticmethod
    def sync_department():
        payload = dict()
        payload['app'] = app.config['STAFF_APP']
        staff_appkey = app.config['STAFF_APPKEY']
        payload['time'] = int(time.time()*1000)
        unsign = str(payload['app']) + str(staff_appkey) + str(payload['time'])
        payload['sign'] = hashlib.sha1(unsign).hexdigest()
        result = requests.get(StaffSync.department_list_url, params=payload)
        r = result.json()
        if r['result']['code'] == 200:
            if r.get('data'):
                for dept_info in r['data']:
                    d = Department(id=dept_info['id'], name=dept_info['name'], parent_id=dept_info['parentId'],
                                   created_at=datetime.strptime(dept_info['gmtCreatedDate'], '%Y-%m-%d %H:%M:%S'),
                                   modified_at=datetime.strptime(dept_info['gmtModifiedDate'], '%Y-%m-%d %H:%M:%S'))
                    db.session.merge(d)
                db.session.commit()

    @staticmethod
    def sync_user():
        payload = dict()
        payload['app'] = app.config['STAFF_APP']
        staff_appkey = app.config['STAFF_APPKEY']
        payload['time'] = int(time.time() * 1000)
        unsign = str(payload['app']) + str(staff_appkey) + str(payload['time'])
        payload['sign'] = hashlib.sha1(unsign).hexdigest()

        result = requests.get(StaffSync.user_list_url, params=payload)
        r = json.loads(result.content)
        if r.get('result').get('code') == 200:
            if 'data' in r:
                User.query.filter(User.id != 'system').update(dict(sync=False))
                for user_info in r['data']:
                    u = User(id=user_info['no'], name=user_info['userName'], email=user_info['email'],
                             real_name=user_info['name'], work_no=user_info['no'], phone=user_info['phone'],
                             sex=user_info['sex'], department_id=user_info['departmentId'], enabled=True, sync=True)
                    db.session.merge(u)
                db.session.commit()
                User.query.filter(User.id != 'system', User.sync == False).update(dict(enabled=False))
                db.session.commit()
