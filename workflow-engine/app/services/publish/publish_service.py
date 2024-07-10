# -*- coding: utf8 -*-

import time
import datetime
from collections import OrderedDict

from app.out.apprepo import Apprepo
from app.out.cmdb_core import CMDBCore
from app.services.flow.workflow import WorkflowService
from app.services.flow.workflow import Config
from app.services.app_branch_service import AppBranchService
from app.services.project.project_service import ProjectService
from app.services.publish.hot_pool_service import HotPoolService
from app.services.operation.operation_service import OperationService
from app.services.framework.user_service import UserService
from app.services.project.sql_scripts_project_service import SQLScriptsProjectService
from app.mongodb import flow_data_collection, publish_switch_collection
from app import app, root_logger


class PublishService(object):

    @staticmethod
    def get_publish_info(publish_id, with_project_data=True, with_flow_data=True, operator_id=None, project_type=None, publish_type=None, departments=None):
        ret = dict()
        ret['publish_id'] = publish_id

        if project_type and not publish_type:
            flow_data = flow_data_collection.find_one({"flow_id": publish_id, 'data.project_type': project_type},
                                                      {'_id': 0})
        elif not project_type and publish_type:
            flow_data = flow_data_collection.find_one({"flow_id": publish_id, 'data.publish_type': publish_type},
                                                      {'_id': 0})
        elif project_type and publish_type:
            flow_data = flow_data_collection.find_one(
                {"flow_id": publish_id, 'data.publish_type': publish_type, 'data.project_type': project_type},
                {'_id': 0})
        else:
            flow_data = flow_data_collection.find_one({"flow_id": publish_id}, {'_id': 0})
        if flow_data:
            publish_data = flow_data.get('data')
            if publish_data.get('scheduled_time') and type(publish_data['scheduled_time']).__name__ == 'datetime':
                publish_data['scheduled_time'] = publish_data['scheduled_time'].strftime('%Y-%m-%d %H:%M')
            project = None
            if with_project_data:
                project_id = publish_data.get("project_id")
                project = ProjectService.get_project(project_id)
                if departments and str(project.dept_id) not in departments:
                    return None
                else:
                    ret["project"] = project.serialize()
            if with_flow_data:
                workflow = WorkflowService.get(publish_id)
                current_flow_info = Config.get_flow_info(workflow.type, workflow.current_task_type)
                publish_data["current_flow_info"] = dict()
                publish_data["current_flow_info"]['key'] = current_flow_info['key']
                publish_data["current_flow_info"]['name'] = current_flow_info['name']
                publish_data["current_flow_info"]['env'] = current_flow_info['env']
                publish_data["current_flow_info"]['type'] = current_flow_info['type']
                publish_data["current_flow_info"]['order'] = current_flow_info['order']
                publish_data["current_flow_info"]['operation_type'] = current_flow_info.get('operation_type')
                publish_data["current_flow_info"]['trigger_type'] = current_flow_info.get('trigger_type')

                participants = workflow.current_task.participants
                publish_data['participants'] = [e.brief() for e in participants]

                if with_project_data:
                    prvgs = list()
                    for p in participants:
                        if p.user_id == operator_id:
                            prvgs.append(p.privilege_name)
                    direction_list = current_flow_info.get("directions")
                    if direction_list:
                        new_directions = OrderedDict()
                        for d, v in direction_list.items():
                            if v.get('prvg') and set(prvgs) & set(v.get('prvg')):
                                new_directions[d] = v

                        # 当打包或发布出错时，遍历发布应用，检查打包状态，并确定是否显示重新发布按钮，只有全部打包成功才会显示
                        if 'pre_republish' in new_directions or 'prd_republish' in new_directions:
                            for app_info in publish_data.get('app_info').values():
                                if not app_info.get('prd_built') and 'prd_republish' in new_directions:
                                    new_directions.pop('prd_republish')
                                    break
                                if not app_info.get('pre_built') and 'pre_republish' in new_directions:
                                    new_directions.pop('pre_republish')
                                    break
                        if project:
                            sql_project = SQLScriptsProjectService.get_sql_scripts_project(str(project.id))
                            if sql_project:
                                if 'cancel_sql' in new_directions and sql_project.get('status').get(current_flow_info['env']) != 'init':
                                    new_directions.pop('cancel_sql')
                                elif 'sql_executed' in new_directions and sql_project.get('status').get(current_flow_info['env']) == 'init':
                                    new_directions.pop('sql_executed')
                                if 'sql_execute' in new_directions and (sql_project.get('manual').get(current_flow_info['env']) or sql_project.get('status').get(current_flow_info['env']) != 'pass'):
                                    new_directions.pop('sql_execute')

                        pe_users = UserService.get_user_by_privilege('pe')
                        pe_user_ids = [user.id for user in pe_users]

                        sqa_user_ids = [e.get('user_id') if e.get('privilege_name') == 'sqa' else None for e in publish_data['participants']]

                        # 当前为人工参与节点+SQA或者PE
                        if publish_data['participants'] and (operator_id in sqa_user_ids or operator_id in pe_user_ids):
                            new_directions['app_sort'] = {'name': u'应用排序'}

                        # 设置了定时时间+环境是生产+PE或者Owner
                        if publish_data.get('scheduled_time') and current_flow_info['env'] == 'prd' and (operator_id in pe_user_ids or operator_id == project.owner_id or operator_id in sqa_user_ids):
                            new_directions['change_scheduled_time'] = {'name': u'修改定时发布时间'}
                            if 'prd_build' in new_directions.keys():
                                new_directions.pop('prd_build')
                            if 'prd_publish' in new_directions.keys():
                                new_directions.pop('prd_publish')

                        # 非生产环境，owner全程可以修改定时发布
                        if current_flow_info['env'] != 'prd' and operator_id == project.owner_id:
                            new_directions['change_scheduled_time'] = {'name': u'修改定时发布时间'}

                        # 预发环境-pre显示
                        if current_flow_info['env'] == 'pre' and (operator_id in sqa_user_ids or operator_id in pe_user_ids):
                            new_directions['pre_change_label'] = {'name': u'修改成功标签'}

                        # 生产环境-prd显示
                        if current_flow_info['env'] == 'prd' and (operator_id in sqa_user_ids or operator_id in pe_user_ids):
                            new_directions['prd_change_label'] = {'name': u'修改成功标签'}

                        publish_data["current_flow_info"]['directions'] = new_directions

            ret["publish"] = publish_data
        return ret

    @staticmethod
    def get_publish_switch_info():
        result = publish_switch_collection.find_one()
        if result:
            result.get("no_publish_date")['begin'] = datetime.date.strftime(result.get("no_publish_date")['begin'],
                                                                            '%Y-%m-%d %H:%M')
            result.get("no_publish_date")['end'] = datetime.date.strftime(result.get("no_publish_date")['end'],
                                                                          '%Y-%m-%d %H:%M')
            result.get("publish_date")['begin'] = datetime.date.strftime(result.get("publish_date")['begin'],
                                                                         '%Y-%m-%d %H:%M')
            result.get("publish_date")['end'] = datetime.date.strftime(result.get("publish_date")['end'],
                                                                       '%Y-%m-%d %H:%M')
            return result

    @staticmethod
    def change_scheduled_time(publish_id, scheduled_time):
        try:
            if scheduled_time:
                scheduled_time = datetime.datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M')
                earliest, latest = HotPoolService.get_change_window_prd_app(publish_id)
                if scheduled_time <= earliest or scheduled_time >= latest:
                    return False
                else:
                    HotPoolService.change_scheduled_prd_app(publish_id, scheduled_time)
            else:
                # 取消定时发布
                scheduled_time = None
                HotPoolService.cancel_scheduled_prd_app(publish_id)
            flow_data_collection.update_one({'flow_id': publish_id}, {'$set': {'data.scheduled_time': scheduled_time}})
            return True
        except Exception, e:
            root_logger.exception("change_scheduled_time error: %s", e)

    @staticmethod
    def mod_publish_switch_info(switch):
        try:
            switch.get("no_publish_date")['begin'] = datetime.datetime.strptime(switch.get("no_publish_date")['begin'],
                                                                                '%Y-%m-%d %H:%M')
            switch.get("no_publish_date")['end'] = datetime.datetime.strptime(switch.get("no_publish_date")['end'],
                                                                              '%Y-%m-%d %H:%M')
            switch.get("publish_date")['begin'] = datetime.datetime.strptime(switch.get("publish_date")['begin'],
                                                                             '%Y-%m-%d %H:%M')
            switch.get("publish_date")['end'] = datetime.datetime.strptime(switch.get("publish_date")['end'],
                                                                           '%Y-%m-%d %H:%M')
            publish_switch_collection.update({}, switch)
            return True
        except Exception, e:
            root_logger.exception("Query publish switch data failed: %s", e)

    @staticmethod
    def verify_publish_time(dept_code=None):
        now_timestamp = time.time()
        now_datetime = datetime.datetime.now()
        data = publish_switch_collection.find_one()
        no_publish_date_begin = data.get('no_publish_date').get('begin')
        no_publish_date_end = data.get('no_publish_date').get('end')
        publish_date_begin = data.get('publish_date').get('begin')
        publish_date_end = data.get('publish_date').get('end')
        if (now_datetime - no_publish_date_begin).total_seconds() >= 0 and (now_datetime - no_publish_date_end).total_seconds() <= 0:
            return False
        elif (now_datetime - publish_date_begin).total_seconds() >= 0 and (now_datetime - publish_date_end).total_seconds() <= 0:
            return True
        else:
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            days_index = datetime.date.today().weekday()
            day = days[days_index]
            dept_data = data.get('weekly_publish_date').get(dept_code)
            if not dept_data:
                dept_data = data.get('weekly_publish_date').get('default')
            begin = dept_data.get(day)['begin']
            end = dept_data.get(day)['end']
            date = datetime.date.today().strftime('%Y%m%d')
            full_begin_time_str = date + begin.replace(':', '') + '00'
            full_end_time_str = date + end.replace(':', '') + '00'
            full_begin_time = time.strptime(full_begin_time_str, '%Y%m%d%H%M%S')
            full_end_time = time.strptime(full_end_time_str, '%Y%m%d%H%M%S')
            full_begin_timestamp = time.mktime(full_begin_time)
            full_end_timestamp = time.mktime(full_end_time)
            if (now_timestamp-full_begin_timestamp) >= 0 and (full_end_timestamp-now_timestamp) >= 0:
                return True
            else:
                return False

    @staticmethod
    def skip_prd_app(app_id, publish_id):
        try:
            if app_id == app.config['DZBD_APP_ID']:
                flow_data_collection.update_one({"flow_id": publish_id},
                                                {'$set': {'data.dzbd.skip': True}})
                return True
            else:
                flow_data_collection.update_one({"flow_id": publish_id},
                                                {'$set': {'data.app_info.{}.skip'.format(app_id): True}})
                return True
        except Exception, e:
            root_logger.exception("skip_prd_app error: %s", e)

    @staticmethod
    def republish_pre_app(app_id, fixed_server_list, publish_id, operator_id):
        info = Apprepo.get_app_info(app_id)
        if info:
            app_name = info.get('name')
            org = info.get('company_code')
            ecs_list = CMDBCore.query_arrange('pre', app_id, 'ecs')
            slb_list = CMDBCore.query_arrange('pre', app_id, 'slb')
            if not ecs_list:
                root_logger.info("default_pre_publish fail, app({}) has no ecs".format(app_name))
                return "failed"
            for ecs in ecs_list:
                if "{}:{}".format(ecs.get('res_id'), ecs.get('port')) not in fixed_server_list:
                    continue
                data = dict()
                data['company'] = org
                data['env'] = 'pre'
                data['ip'] = ecs.get('ip')
                data['app_name'] = app_name
                port = int(ecs.get('port'))
                data['port'] = port
                data['hsf_port'] = port + 1
                data['hsf_timeout'] = 120
                data['check_url'] = info.get('check_url')
                data['pack_serv_url'] = "{}/release/app/{}/pre/{}/".format(app.config['PACKAGE_SERVER_URL'], app_id, publish_id)
                if slb_list:
                    data['ecs_id'] = ecs.get('res_id')
                    data['slb_id'] = slb_list[0].get('res_id')
                OperationService.run_operation.delay("pre_publish", ecs.get('ip'), app_name, operator_id, **data)
            return True

    @staticmethod
    def republish_prd_app(app_id, fixed_server_list, publish_id, operator_id):
        info = Apprepo.get_app_info(app_id)
        if info:
            app_name = info.get('name')
            org = info.get('company_code')
            ecs_list = CMDBCore.query_arrange('prd', app_id, 'ecs')
            slb_list = CMDBCore.query_arrange('prd', app_id, 'slb')
            if not ecs_list:
                root_logger.info("default_prd_publish fail, app({}) has no ecs".format(app_name))
                return "failed"
            for ecs in ecs_list:
                if "{}:{}".format(ecs.get('res_id'), ecs.get('port')) not in fixed_server_list:
                    continue
                data = dict()
                data['company'] = org
                data['env'] = 'prd'
                data['ip'] = ecs.get('ip')
                data['app_name'] = app_name
                port = int(ecs.get('port'))
                data['port'] = port
                data['hsf_port'] = port + 1
                data['hsf_timeout'] = 120
                data['check_url'] = info.get('check_url')
                data['app_owner_list'] = info.get('owner_list')
                data['app_contacts_list'] = info.get('contact_list')
                data['pack_serv_url'] = "{}/release/app/{}/prd/{}/".format(app.config['PACKAGE_SERVER_URL'], app_id, publish_id)
                if slb_list:
                    data['ecs_id'] = ecs.get('res_id')
                    data['slb_id'] = slb_list[0].get('res_id')
                OperationService.run_operation.delay("prd_publish", ecs.get('ip'), app_name, operator_id, **data)
            return True

    @staticmethod
    def sort_app(project_id, publish_id):
        try:
            share_list = AppBranchService.list_app_branch(project_id, ['open', 'module'])
            app_list = AppBranchService.list_app_branch(project_id, ['app'])
            share_order = [e.get('app_id') for e in share_list]
            app_order = [e.get('app_id') for e in app_list]
            flow_data_collection.update_one({'flow_id': publish_id}, {'$set': {'data.app_order': app_order, 'data.share_order': share_order}})
            return True
        except Exception, e:
            root_logger.exception("sort_app error: %s", e)

    @staticmethod
    def mod_publish_data(publish_id, flow_data=None, dzbd=None, env=None, app_list=None):
        try:
            change = dict()
            if dzbd:
                dzbd = list(set(dzbd))
                change.update({'data.dzbd.published_{}_servers'.format(env): dzbd})
            if app_list:
                for app_info in app_list:
                    published_server = app_info.get("published")
                    if published_server is not None:
                        published_server = list(set(published_server))
                        change.update({'data.app_info.{}.published_{}_servers'.format(app_info.get("app_id"), env): published_server})
                    change.update({'data.app_info.{}.{}_built'.format(app_info.get("app_id"), env): app_info.get("built")})
            if flow_data and not dzbd and not app_list:
                change['data'] = flow_data
            flow_data_collection.update({'flow_id': publish_id}, {'$set': change})
            return True
        except Exception,e:
            root_logger.exception('update flow_data_collection for flow_id {} failed: {}'.format(publish_id, e))
            return False