# -*- coding: utf8 -*-

from pymongo.errors import DuplicateKeyError

from app.services.jenkins_service import JenkinsService
from app.services.project.sql_scripts_project_service import SQLScriptsProjectService
from app.services.operation.operation_template_service import OperationTemplateService
from app.mongodb import result_detail_collection
from app import root_logger


class ResultService(object):

    @staticmethod
    def add_result_detail(opid, op_type, step, content=None, callback=None):
        try:
            rd = dict()
            rd['opid'] = opid
            rd['type'] = op_type
            rd['step'] = step
            rd['content'] = content
            rd['callback'] = callback
            obj_id = result_detail_collection.insert_one(rd).inserted_id
            return str(obj_id)
        except DuplicateKeyError:
            pass
        except Exception, e:
            root_logger.exception("add_result_detail error: %s", e)

    @staticmethod
    def mod_result_detail(opid, step, content=None, callback=None):
        try:
            change = dict()
            change['content'] = content
            change['callback'] = callback
            result_detail_collection.update_one({'opid': opid, 'step': step}, {'$set': change})
            return True
        except Exception, e:
            root_logger.exception("mod_result_detail error: %s", e)

    @staticmethod
    def get_result_detail(operation_type, opid):
        template_list = OperationTemplateService.list_template(operation_type)
        ret = list()
        for t in template_list:
            one = {'step': t.get('name'), 'order': t.get('order'), 'desc': t.get('desc')}
            rd = result_detail_collection.find_one({'opid': opid, 'step': t.get('name')})
            if rd:
                if rd.get('content'):
                    one['result'] = rd.get('content')
                elif rd.get('callback'):
                    one['result'] = eval(rd.get('callback'))
            ret.append(one)
        sorted(ret, key=lambda step: step.get('order'))
        return ret
