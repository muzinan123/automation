# -*- coding:utf-8 -*-

import json
import datetime
from sqlalchemy import desc

from app.services.flow.config import Config
from app.services.flow.wrap_operation import WrapOperation
from app.services.flow.auto_trigger import AutoTrigger
from app.services.flow.go_action import GoAction
from app.services.framework.user_service import UserService
from app.models.WorkFlow import WorkFlowInstance, WorkFlowTaskInstance, TaskParticipant
from app.models.Project import Project, ProjectParticipant
from app.models import db
from app.mongodb import flow_data_collection
from app import socketio, celery, workflow_logger


class WorkflowService(object):

    @staticmethod
    def user_participated_in(task_id, user_id, privilege_name):
        """操作前的权限判断"""
        result = TaskParticipant.query.filter(TaskParticipant.task_instance_id == task_id,
                                              TaskParticipant.user_id == user_id, TaskParticipant.active == True, TaskParticipant.privilege_name == privilege_name)
        if result.first():
            return True

    @staticmethod
    def list_participated_in_user(flow_id):
        """列出当前参与人，返回的是User"""
        ret = list()
        workflow_instance = db.session.query(WorkFlowInstance).get(flow_id)
        if workflow_instance:
            current_task_id = workflow_instance.current_task_id
            if current_task_id:
                participate_tasks = db.session.query(TaskParticipant).filter(
                    TaskParticipant.task_instance_id == current_task_id,
                    TaskParticipant.active == True)
                for p in participate_tasks:
                    ret.append(p.user)
        return ret

    @staticmethod
    def list_participated_flow_id(user_id, privilege_list=None):
        tasks = TaskParticipant.query.filter(TaskParticipant.active == True, TaskParticipant.user_id == user_id,
                                             TaskParticipant.privilege_name.in_(privilege_list) if privilege_list else "")
        return [e.workflow_instance_id for e in tasks]

    @staticmethod
    def list(query, list_all=True, order_by='create_at', list_history=False, task_type=None, order_desc=None, begin_date=None, end_date=None):
        result = WorkFlowInstance.query.filter(
            WorkFlowInstance.id.like("%" + query + "%") if query else "",
            WorkFlowInstance.current_task_type.notin_(('prd_complete', 'abandon')) if not list_all else "",
            WorkFlowInstance.current_task_type.in_(('prd_complete', 'abandon')) if list_history else "",
            WorkFlowInstance.current_task_type == task_type if task_type else "",
            WorkFlowInstance.modify_at >= datetime.datetime.strptime(begin_date, '%Y-%m-%d %H:%M:%S') if begin_date else "",
            WorkFlowInstance.modify_at <= datetime.datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S') if end_date else ""
        ).order_by(
            desc(eval('WorkFlowInstance.' + order_by)) if order_desc else (eval('WorkFlowInstance.' + order_by)))
        return result

    @staticmethod
    def get(flow_id):
        return WorkFlowInstance.query.get(flow_id)

    @staticmethod
    def query(start_day, end_day):
        work_flows = WorkFlowInstance.query.filter(WorkFlowInstance.modify_at > start_day,
                                                   WorkFlowInstance.modify_at < end_day)
        return work_flows


class Workflow(object):

    @staticmethod
    def new(flow_id, flow_type, flow_data_str=None, flow_data=None, creator_id='system'):
        try:
            if flow_data_str and not flow_data:
                flow_data = json.loads(flow_data_str)
            if flow_data is not None:
                workflow_logger.info("create new flow type: " + flow_type)
                workflow_logger.info("create new flow id: " + flow_id)
                init_task_type = Config.flow.get(flow_type).keys()[0]
                instance = WorkFlowInstance(id=flow_id, type=flow_type, current_task_type=init_task_type,
                                            create_at=datetime.datetime.now(), modify_at=datetime.datetime.now())
                db.session.add(instance)
                db.session.commit()
                new_task_id = WorkflowTask.new(instance.id, init_task_type, flow_type, creator_id=creator_id)

                instance.current_task_id = new_task_id
                instance.init_task_id = new_task_id
                db.session.commit()

                flow_data_collection.insert_one({'flow_id': flow_id, 'flow_type': flow_type, 'data': flow_data})

                WorkflowTask.trigger.delay(flow_id, flow_type, new_task_id, init_task_type, operator_id='system')

                return instance.id
        except Exception, e:
            workflow_logger.exception("new error: %s", e)

    @staticmethod
    def save_flow_data(flow_id, flow_data_change_str=None, flow_data_change=None):
        try:
            if flow_data_change_str and not flow_data_change:
                flow_data_change = json.loads(flow_data_change_str, strict=False)
            if flow_data_change is not None:
                flow_data_collection.update_one({'flow_id': flow_id}, {'$set': flow_data_change})
                return True
        except Exception, e:
            workflow_logger.exception("save_flow_data error: %s", e)

    @staticmethod
    def go(flow_id, direction, operator_id='system'):
        workflow_instance = db.session.query(WorkFlowInstance).get(flow_id)
        flow_type = workflow_instance.type
        current_task_type = workflow_instance.current_task_type
        flow_id = workflow_instance.id

        workflow_logger.info("workflow " + flow_id + " go " + direction + " from " + current_task_type)

        if Config.flow.get(flow_type):
            i = Config.flow.get(flow_type).keys().index(current_task_type)

            directions = Config.flow.get(flow_type).get(current_task_type).get('directions')
            if directions is None or directions.get(direction) is None:
                return
            new_task_type = directions.get(direction).get('go')
            if new_task_type in Config.flow.get(flow_type).keys():
                # update current task node
                current_task_id = workflow_instance.current_task_id
                result = WorkflowTask.go(current_task_id, direction, modifier_id=operator_id)
                if not result:
                    return

                # deactive participants
                WorkflowTask.deactive_participants(current_task_id)

                # add new task node
                new_task_id = WorkflowTask.new(flow_id, new_task_type, flow_type, creator_id=operator_id)

                # update workflow
                workflow_instance.current_task_type = new_task_type
                workflow_instance.current_task_id = new_task_id
                workflow_instance.modify_at = datetime.datetime.now()

                db.session.commit()

                WorkflowTask.trigger.delay(flow_id, flow_type, new_task_id, new_task_type, operator_id=operator_id)

                return True

    @staticmethod
    def get(flow_id):
        return flow_data_collection.find_one({"flow_id": flow_id}, {"_id": False})


class WorkflowTask(object):

    @staticmethod
    def new(flow_id, task_type, flow_type, creator_id='system'):
        workflow_logger.info("create new task: " + task_type + "@" + flow_id + " in " + flow_type)
        task_instance = WorkFlowTaskInstance(workflow_instance_id=flow_id, type=task_type, workflow_type=flow_type,
                                             create_at=datetime.datetime.now(), modify_at=datetime.datetime.now(),
                                             creator_id=creator_id)
        db.session.add(task_instance)
        db.session.commit()
        return task_instance.id

    @staticmethod
    def go(task_id, go, modifier_id="system"):
        workflow_task_instance = db.session.query(WorkFlowTaskInstance).get(task_id)
        flow_id = workflow_task_instance.workflow_instance_id
        flow_type = workflow_task_instance.workflow_type
        task_type = workflow_task_instance.type
        result = WorkflowTask.action(flow_id, flow_type, task_type, go, operator_id=modifier_id)
        workflow_logger.info("action result: {}".format(result))
        if not result:
            return False
        workflow_task_instance.go = go
        workflow_task_instance.modifier_id = modifier_id
        workflow_task_instance.modify_at = datetime.datetime.now()
        db.session.commit()
        return True

    @staticmethod
    def add_participants(task_id, task_type, flow_id, flow_type):
        try:
            directions = Config.flow.get(flow_type).get(task_type).get('directions')
            if directions:
                privileges = set()
                for d in directions.values():
                    if d.get('prvg') is not None:
                        privileges |= set(d.get('prvg'))
                project_id = None
                if {'owner', 'sqa', 'qa'} & privileges:
                    project_id = flow_id[:-2]
                for p in privileges:
                    user_list = set()
                    if p not in ['owner', 'sqa', 'qa']:
                        users = UserService.get_user_by_privilege(p)
                        user_list |= set([e.id for e in users])
                    elif p in ['sqa', 'qa']:
                        # 根据项目内角色关联
                        pp_list = ProjectParticipant.query.filter(ProjectParticipant.project_id == project_id,
                                                                  ProjectParticipant.privilege_name == p)
                        user_list |= set([e.participant_id for e in pp_list])
                    elif p in ['owner']:
                        # 根据项目内角色关联
                        project = Project.query.get(project_id)
                        user_list.add(project.owner_id)
                    for user_id in user_list:
                        tp = TaskParticipant(task_instance_id=task_id, workflow_instance_id=flow_id,
                                             workflow_type=flow_type, task_type=task_type, user_id=user_id,
                                             privilege_name=p, active=True)
                        db.session.add(tp)
                db.session.commit()
        except Exception, e:
            workflow_logger.exception("add_participant error: %s", e)

    @staticmethod
    def deactive_participants(task_id):
        participants = db.session.query(TaskParticipant).filter(TaskParticipant.task_instance_id == task_id)
        for p in participants:
            p.active = False
        db.session.commit()

    @staticmethod
    @celery.task
    def trigger(flow_id, flow_type, task_id, task_type, operator_id="system"):
        # trigger_type 的优先级比 operation_type 高
        trigger_type = Config.flow.get(flow_type).get(task_type).get('trigger_type')
        operation_type = Config.flow.get(flow_type).get(task_type).get('operation_type')
        direction = None
        if trigger_type:
            direction = AutoTrigger.pull_trigger(flow_type, trigger_type, flow_id, operator_id)
            workflow_logger.info("flow {} get direction from trigger: {}".format(flow_id, direction))
        if operation_type and direction is None:
            direction = WrapOperation.wrap_operation(flow_type, operation_type, flow_id, operator_id)
            workflow_logger.info("flow {} get direction from operation: {}".format(flow_id, direction))
        if direction:
            Workflow.go(flow_id, direction, operator_id='system')
        else:
            # add participants
            WorkflowTask.add_participants(task_id, task_type, flow_id, flow_type)
        socketio.emit('notify_new_task', {'flow_id': flow_id}, namespace='/workflow', broadcast=True)

    @staticmethod
    def action(flow_id, flow_type, task_type, direction, operator_id="system"):
        # 由go操作触发的同步执行的操作，会在下一个节点的trigger触发前执行
        workflow_logger.info("run action {}.{} in direction {}".format(flow_type, task_type, direction))
        directions = Config.flow.get(flow_type).get(task_type).get('directions')
        if directions and directions.get(direction) and directions.get(direction).get('action'):
            action = directions.get(direction).get('action')
            result = GoAction.run(flow_type, action, flow_id, operator_id)
            return result
        return True

