# -*- coding: utf8 -*-

import re
import datetime
import json
import uuid
from pymongo import ASCENDING, DESCENDING

from app.services.operation.pool import get_func
from app.services.operation.operation_template_service import OperationTemplateService
from app.mongodb import operation_result_collection
from app.util import Util
from app import socketio, celery, root_logger


class OperationService(object):

    @staticmethod
    def start_operation(opid, operation_type, target, app_name, params, operator_id, flow_id=None):
        try:
            operation_result_collection.insert_one({'id': opid, 'flow_id': flow_id, 'type': operation_type, 'target': target,
                                                 'app_name': app_name, 'params': params, 'operator_id': operator_id,
                                                 'start_at': datetime.datetime.utcnow(), 'finish_at': None, 'status': 'running'})
            socketio.emit('notify_new', {}, namespace='/result', broadcast=True)
        except Exception, e:
            root_logger.exception("start operation error: %s", e)

    @staticmethod
    def mod_operation(opid, status):
        try:
            operation_result_collection.update_one({'id': opid},
                                                   {'$set': {'finish_at': datetime.datetime.utcnow(), 'status': status}})
        except Exception, e:
            root_logger.exception("mod operation error: %s", e)

    @staticmethod
    def list_operation_result(query, operation_type=None, flow_id=None, order_by='start_at', order_desc=None):
        regx = re.compile(query, re.IGNORECASE)
        pipeline = [
            {'$project': {
                '_id': False
            }},
            {'$match': {
                '$or': [
                    {'target': regx},
                    {'app_name': regx},
                    {'params': regx},
                ]
            }}
        ]
        if operation_type:
            pipeline.append({'$match': {
                'type': operation_type
            }})
        if flow_id:
            pipeline.append({'$match': {
                'flow_id': flow_id
            }})
        if order_desc:
            pipeline.append({'$sort': {order_by: DESCENDING}})
        else:
            pipeline.append({'$sort': {order_by: ASCENDING}})
        return pipeline, operation_result_collection

    @staticmethod
    def get_operation(opid):
        return operation_result_collection.find_one({'id': opid})

    @staticmethod
    def get_operation_progress(opid):
        data = Util.redis.hgetall(opid)
        if data:
            data['opid'] = opid
            return data
        else:
            return {
                'opid': opid,
                'step_name': 'complete',
                'step_desc': u'完成',
                'progress': 100,
                'step_status': 'done',
                'status': 'done'
            }

    operations = dict()
    type_list = [e for e in OperationTemplateService.list_template_type()]
    for template_type in type_list:
        one_operation = list()
        template_data = OperationTemplateService.list_template(template_type)
        for t in template_data:
            one_operation.append(t)
        operations[template_type] = one_operation

    @staticmethod
    def reload_template():
        type_list = [e for e in OperationTemplateService.list_template_type()]
        for template_type in type_list:
            one_operation = list()
            template_data = OperationTemplateService.list_template(template_type)
            for t in template_data:
                one_operation.append(t)
            OperationService.operations[template_type] = one_operation

    @staticmethod
    @celery.task
    def run_operation(operation_type, target, _app_name, operator_id, _flow_id=None, **kwargs):
        operation = OperationService.operations.get(operation_type)
        if operation:
            success = True
            opid = uuid.uuid1().hex
            params = json.dumps(kwargs)
            OperationService.start_operation(opid, operation_type, target, _app_name, params, operator_id, flow_id=_flow_id)
            Util.redis.hset(opid, 'opid', opid)
            Util.redis.hset(opid, 'status', 'running')
            sorted(operation, key=lambda step: step.get('order'))
            for step in operation:
                Util.redis.hset(opid, 'step_name', step.get('name'))
                Util.redis.hset(opid, 'step_desc', step.get('desc'))
                Util.redis.hincrby(opid, 'progress', step.get('progress'))
                Util.redis.hset(opid, 'step_status', 'running')
                kwargs['opid'] = opid
                kwargs['op_type'] = operation_type
                kwargs['step'] = step.get('name')
                socketio.emit('result', Util.redis.hgetall(opid), namespace='/result', broadcast=True)
                try:
                    func = get_func(step.get('func'))
                    result = func(**kwargs)
                    if result:
                        Util.redis.hset(opid, 'step_status', 'done')
                        if type(result).__name__ == 'dict':
                            kwargs.update(result)
                    else:
                        # 执行失败，停止退出
                        success = False
                        break
                except Exception, e:
                    # 执行失败，停止退出
                    root_logger.exception("func error: %s", e)
                    success = False
                    break
            if success:
                OperationService.mod_operation(opid, 'done')
                Util.redis.delete(opid)
                ret = {
                    'opid': opid,
                    'step_name': 'complete',
                    'step_desc': u'完成',
                    'progress': 100,
                    'step_status': 'done',
                    'status': 'done'
                }
                socketio.emit('result', ret, namespace='/result', broadcast=True)
                return True
            else:
                OperationService.mod_operation(opid, 'fail')
                Util.redis.delete(opid)
                socketio.emit('notify_new', {}, namespace='/result', broadcast=True)
                return False
