# -*- coding:utf-8 -*-

import datetime
import json
from sqlalchemy import or_,and_,desc
from task_pool import TaskPool
from app.models import db
from app.models.framework.Scheduler import DatabaseSchedulerEntry, CrontabSchedule, IntervalSchedule, SchedulerHistory, TaskResult

from app import celery


class SchedulerService:

    def __init__(self):
        pass

    @staticmethod
    def add_schedule(name, task, args, kwargs, enabled, every=None, period=None, minute=None, hour=None, day_of_week=None,
               day_of_month=None, month_of_year=None):
        dse = DatabaseSchedulerEntry()
        dse.name = name
        dse.task = task
        if not args:
            args='[]'
        if not kwargs:
            kwargs='{}'
        dse.arguments = args
        dse.keyword_arguments = kwargs
        dse.enabled=enabled
        if every and period:
            dse.interval = IntervalSchedule(every=every, period=period)
        elif minute or hour or day_of_week or day_of_month or month_of_year:
            if minute == "":
                minute = "*"
            if hour == "":
                hour = "*"
            if day_of_week == "":
                day_of_week = "*"
            if day_of_month == "":
                day_of_month = "*"
            if month_of_year == "":
                month_of_year = "*"
            dse.crontab = CrontabSchedule(minute=minute, hour=hour, day_of_week=day_of_week, day_of_month=day_of_month, month_of_year=month_of_year)
        db.session.add(dse)
        db.session.commit()

    @staticmethod
    def del_schedule(sid):
        dse = DatabaseSchedulerEntry.query.get(sid)
        if dse.interval:
            db.session.delete(dse.interval)
        if dse.crontab:
            db.session.delete(dse.crontab)
        db.session.delete(dse)
        db.session.commit()

    @staticmethod
    def mod_schedule(sid, name, task, args, kwargs, enabled, every=None, period=None, minute=None, hour=None, day_of_week=None,
               day_of_month=None, month_of_year=None):
        dse = DatabaseSchedulerEntry.query.get(sid)
        dse.name = name
        dse.task = task
        if not args:
            args = '[]'
        if not kwargs:
            kwargs = '{}'
        dse.arguments = args
        dse.keyword_arguments = kwargs
        dse.enabled = enabled
        if every and period:
            dse.interval = IntervalSchedule(every=every, period=period)
        elif minute or hour or day_of_week or day_of_month or month_of_year:
            dse.crontab = CrontabSchedule(minute=minute, hour=hour, day_of_week=day_of_week, day_of_month=day_of_month,
                                          month_of_year=month_of_year)
        db.session.commit()
        pass

    @staticmethod
    def get_schedule_list():
        ss = DatabaseSchedulerEntry.query.order_by(desc(DatabaseSchedulerEntry.date_changed)).all()
        return ss

    @staticmethod
    def get_schedule_detail(sid):
        dse = DatabaseSchedulerEntry.query.get(sid)
        return dse.detail()

    @staticmethod
    def get_task_list():
        ret = list()
        for t in celery.tasks:
            n = str(t)
            if n[0:6]!='celery':
                ret.insert(0, str(t))
        return ret

    @staticmethod
    def get_task_history(query, start_at):
        sh = SchedulerHistory.query.filter(or_(SchedulerHistory.schedule_name.like("%" + query + "%"),
                                           SchedulerHistory.task_name.like("%" + query + "%")) if query is not None else "",
                                           and_(SchedulerHistory.date_start >= start_at + ' 00:00:00',
                                                SchedulerHistory.date_start <= start_at + ' 23:59:59') if start_at is not None else "")\
            .order_by(desc(SchedulerHistory.date_start))
        return sh

    @staticmethod
    def get_task_history_detail(sh_id):
        ret = dict()
        sh = SchedulerHistory.query.get(sh_id)
        if sh:
            ret['id'] = sh.id
            ret['args'] = sh.arguments
            ret['kwargs'] = sh.keyword_arguments
            task_id = sh.task_id
            task = TaskResult.query.filter(TaskResult.task_id == task_id).first()
            if task:
                ret['result'] = unicode(task.result)
                if task.traceback:
                    ret['traceback'] = task.traceback.replace('\n','<br>')
                else:
                    ret['traceback'] = None
            else:
                ret['result'] = None
                ret['traceback'] = None
            return ret

    @staticmethod
    def run_task_once(task_name, args_json, kwargs_json):
        try:
            args = json.loads(args_json)
            kwargs = json.loads(kwargs_json)
            result = celery.tasks.get(task_name).apply_async(args=args,kwargs=kwargs)
            sh = SchedulerHistory(date_start=datetime.datetime.utcnow())
            sh.schedule_id = 0
            sh.schedule_name = u'手工调度'
            sh.task_id = result.id
            sh.task_name = task_name
            sh.arguments = args_json
            sh.keyword_arguments = kwargs_json
            db.session.add(sh)
            db.session.commit()
            return True
        except ValueError:
            return False
