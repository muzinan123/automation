# -*- coding: utf-8 -*-

import datetime
import json
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
import sqlalchemy.event
from sqlalchemy.types import PickleType
from celery import schedules
from app.models import db
from app.util import Util


class CrontabSchedule(db.Model):
    __tablename__ = 'celery_crontabs'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    minute = db.Column(db.String(64), default='*')
    hour = db.Column(db.String(64), default='*')
    day_of_week = db.Column(db.String(64), default='*')
    day_of_month = db.Column(db.String(64), default='*')
    month_of_year = db.Column(db.String(64), default='*')

    @property
    def schedule(self):
        return schedules.crontab(minute=self.minute,
                                 hour=self.hour,
                                 day_of_week=self.day_of_week,
                                 day_of_month=self.day_of_month,
                                 month_of_year=self.month_of_year)

    @classmethod
    def from_schedule(cls, dbsession, schedule):
        spec = {'minute': schedule._orig_minute,
                'hour': schedule._orig_hour,
                'day_of_week': schedule._orig_day_of_week,
                'day_of_month': schedule._orig_day_of_month,
                'month_of_year': schedule._orig_month_of_year}
        try:
            query = dbsession.query(CrontabSchedule)
            query = query.filter_by(**spec)
            existing = query.one()
            return existing
        except NoResultFound:
            return cls(**spec)
        except MultipleResultsFound:
            query = dbsession.query(CrontabSchedule)
            query = query.filter_by(**spec)
            query.delete()
            dbsession.commit()
            return cls(**spec)


class IntervalSchedule(db.Model):
    __tablename__ = 'celery_intervals'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    every = db.Column(db.Integer, nullable=False)
    period = db.Column(db.String(24))

    @property
    def schedule(self):
        return schedules.schedule(datetime.timedelta(**{self.period: self.every}))

    @classmethod
    def from_schedule(cls, dbsession, schedule, period='seconds'):
        every = max(schedule.run_every.total_seconds(), 0)
        try:
            query = dbsession.query(IntervalSchedule)
            query = query.filter_by(every=every, period=period)
            existing = query.one()
            return existing
        except NoResultFound:
            return cls(every=every, period=period)
        except MultipleResultsFound:
            query = dbsession.query(IntervalSchedule)
            query = query.filter_by(every=every, period=period)
            query.delete()
            dbsession.commit()
            return cls(every=every, period=period)


class DatabaseSchedulerEntry(db.Model):
    __tablename__ = 'celery_schedules'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    task = db.Column(db.String(255))
    interval_id = db.Column(db.Integer, db.ForeignKey('celery_intervals.id'))
    crontab_id = db.Column(db.Integer, db.ForeignKey('celery_crontabs.id'))
    arguments = db.Column(db.String(255), default='[]')
    keyword_arguments = db.Column(db.String(255), default='{}')
    queue = db.Column(db.String(255))
    exchange = db.Column(db.String(255))
    routing_key = db.Column(db.String(255))
    expires = db.Column(db.DateTime)
    enabled = db.Column(db.Boolean, default=True)
    last_run_at = db.Column(db.DateTime)
    total_run_count = db.Column(db.Integer, default=0)
    date_changed = db.Column(db.DateTime)

    interval = db.relationship(IntervalSchedule)
    crontab = db.relationship(CrontabSchedule)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'task': self.task,
            'run_type': 'crontab' if self.crontab_id else 'interval',
            'enabled': 'Yes' if self.enabled == 1 else 'No',
            'run_count': self.total_run_count,
            'last_update': datetime.datetime.strftime(Util.utc2local(self.date_changed), '%Y-%m-%d %H:%M:%S')
        }

    def detail(self):
        if self.crontab_id:
            return {
                'id': self.id,
                'name': self.name,
                'task': self.task,
                'args': self.arguments,
                'kwargs': self.keyword_arguments,
                'enabled': self.enabled,
                'run_type': 'crontab' if self.crontab_id else 'interval',
                'minute': self.crontab.minute,
                'hour': self.crontab.hour,
                'day_of_week': self.crontab.day_of_week,
                'day_of_month': self.crontab.day_of_month,
                'month_of_year': self.crontab.month_of_year,
            }
        else:
            return {
                'id': self.id,
                'name': self.name,
                'task': self.task,
                'args': self.arguments,
                'kwargs': self.keyword_arguments,
                'enabled': self.enabled,
                'run_type': 'crontab' if self.crontab_id else 'interval',
                'every': self.interval.every,
                'period': self.interval.period
            }

    @property
    def args(self):
        return json.loads(self.arguments)

    @args.setter
    def args(self, value):
        self.arguments = json.dumps(value)

    @property
    def kwargs(self):
        return json.loads(self.keyword_arguments)

    @kwargs.setter
    def kwargs(self, kwargs_):
        self.keyword_arguments = json.dumps(kwargs_)

    @property
    def schedule(self):
        if self.interval:
            return self.interval.schedule
        if self.crontab:
            return self.crontab.schedule


@sqlalchemy.event.listens_for(DatabaseSchedulerEntry, 'before_insert')
def _set_entry_changed_date(mapper, connection, target):
    target.date_changed = datetime.datetime.utcnow()


class TaskResult(db.Model):
    """Task result/status."""
    __tablename__ = 'celery_taskmeta'
    __bind_key__ = 'main'
    __table_args__ = {
        'sqlite_autoincrement': True,
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = db.Column(db.Integer, db.Sequence('task_id_sequence'),
                   primary_key=True,
                   autoincrement=True)
    task_id = db.Column(db.String(255), unique=True)
    status = db.Column(db.String(50), default='PENDING')
    result = db.Column(PickleType, nullable=True)
    date_done = db.Column(db.DateTime, default=datetime.datetime.utcnow,
                          onupdate=datetime.datetime.utcnow, nullable=True)
    traceback = db.Column(db.Text, nullable=True)

    def __init__(self, task_id):
        self.task_id = task_id

    def to_dict(self):
        return {'task_id': self.task_id,
                'status': self.status,
                'result': self.result,
                'traceback': self.traceback,
                'date_done': self.date_done}

    def __repr__(self):
        return '<Task {0.task_id} state: {0.status}>'.format(self)


class TaskSetResult(db.Model):
    """TaskSet result"""
    __tablename__ = 'celery_tasksetmeta'
    __bind_key__ = 'main'
    __table_args__ = {
        'sqlite_autoincrement': True,
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer, db.Sequence('taskset_id_sequence'),
                   autoincrement=True, primary_key=True)
    taskset_id = db.Column(db.String(255), unique=True)
    result = db.Column(PickleType, nullable=True)
    date_done = db.Column(db.DateTime, default=datetime.datetime.utcnow,
                          nullable=True)

    def __init__(self, taskset_id, result):
        self.taskset_id = taskset_id
        self.result = result

    def to_dict(self):
        return {'taskset_id': self.taskset_id,
                'result': self.result,
                'date_done': self.date_done}

    def __repr__(self):
        return '<TaskSet: {0.taskset_id}>'.format(self)


class SchedulerHistory(db.Model):
    __tablename__ = 'celery_schedules_history'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_start = db.Column(db.DateTime, default=datetime.datetime.utcnow,
                          onupdate=datetime.datetime.utcnow, nullable=True)
    schedule_id = db.Column(db.Integer)
    schedule_name = db.Column(db.String(255))
    task_id = db.Column(db.String(255))
    task_name = db.Column(db.String(255))
    arguments = db.Column(db.String(255))
    keyword_arguments = db.Column(db.String(255))

    def serialize(self):
        """Return object data in easily serializeable format"""
        result = TaskResult.query.filter(TaskResult.task_id == self.task_id).first()
        if result:
            return {
                'id': self.id,
                'schedule_id': self.schedule_id,
                'schedule_name': self.schedule_name,
                'task_id': self.task_id,
                'task_name': self.task_name,
                'date_start': datetime.datetime.strftime(Util.utc2local(self.date_start), '%Y-%m-%d %H:%M:%S'),
                'date_done': datetime.datetime.strftime(Util.utc2local(result.date_done), '%Y-%m-%d %H:%M:%S'),
                'status': result.status,
            }
        else:
            return {
                'id': self.id,
                'schedule_id': self.schedule_id,
                'schedule_name': self.schedule_name,
                'task_id': self.task_id,
                'task_name': self.task_name,
                'date_start': datetime.datetime.strftime(Util.utc2local(self.date_start), '%Y-%m-%d %H:%M:%S'),
                'date_done': None,
                'status': 'PENDING',
            }


class TaskHistory(db.Model):
    __tablename__ = 'celery_task_history'
    __bind_key__ = 'main'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    date_start = db.Column(db.DateTime, default=datetime.datetime.utcnow,
                           onupdate=datetime.datetime.utcnow, nullable=True)
    task = db.Column(db.String(255))
    arguments = db.Column(db.String(255), default='[]')
    keyword_arguments = db.Column(db.String(255), default='{}')