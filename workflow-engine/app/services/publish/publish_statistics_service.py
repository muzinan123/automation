# -*- coding:utf8 -*-

from app.services.flow.workflow import WorkflowService
from app.services.project.project_service import ProjectService
from app.services.framework.user_service import UserService
from app.mongodb import flow_data_collection, product_publish_statistics_collection, publish_abandon_statistics_collection, project_publish_statistics_collection
from app import app, root_logger
from operator import itemgetter
import datetime
from pymongo import DESCENDING


class PublishStatisticsService(object):

    # 按部门及产品模块统计完成以及废弃的发布
    @staticmethod
    def add_product_publish_statistics(begin_date, end_date):
        flow_data = WorkflowService.list('', list_all=True, order_by='create_at', list_history=True, task_type=None, order_desc=None, begin_date=begin_date, end_date=end_date)
        flow_data_list = [ e.serialize() for e in flow_data]
        for f in flow_data_list:
            flow_id = f.get('id')
            publish_data = flow_data_collection.find_one({'flow_id': flow_id})
            f['project_id'] = int(publish_data.get('data').get('project_id'))

        ret = dict()
        for e in flow_data_list:
            app = ProjectService.get_project(e.get('project_id')).brief()
            key = app.get('dept_code') + '_' + str(app.get('product_id'))
            if not key in ret.keys():
                ret[key] = dict()
                ret[key]['department'] = app.get('dept_label')
                ret[key]['product'] = app.get('product_label')
                ret[key]['complete'] = 0
                ret[key]['abandon'] = 0

            if e.get('current_task_type') == 'prd_complete':
                ret[key]['complete'] = ret[key]['complete'] + 1
            elif e.get('current_task_type') == 'abandon':
                    ret[key]['abandon'] = ret[key]['abandon'] + 1
        for val in ret.values():
            department = val.get('department')
            product = val.get('product')
            complete = val.get('complete')
            abandon = val.get('abandon')
            total = complete+abandon
            try:
                product_publish_statistics_collection.insert_one({'department': department, 'product': product, 'complete': complete, 'abandon': abandon, 'total': total, 'date': datetime.datetime.strptime(begin_date, '%Y-%m-%d %H:%M:%S')})
            except Exception, e:
                root_logger.exception("insert to product_publish_statistics_collection error, %s", e)
                return False
        return True

    # 统计不同发布回退原因的次数
    @staticmethod
    def add_publish_abandon_statistics(begin_date, end_date):
        workflow_data = WorkflowService.list('', list_all=True, order_by='create_at', list_history=True, task_type=None,
                                         order_desc=None, begin_date=begin_date, end_date=end_date)
        workflow_data_list = [e.serialize() for e in workflow_data if e.current_task_type == 'abandon']

        reasons = dict()
        reasons['owner_rollback_reason'] = dict()
        reasons['pre_not_pass_reason'] = dict()
        for workflow_data in workflow_data_list:
            flow_data = flow_data_collection.find_one({'flow_id': workflow_data.get('id')})
            if 'owner_rollback_reason' in flow_data.get('data').keys():
                reason = flow_data.get('data').get('owner_rollback_reason')
                if reason in reasons.get('owner_rollback_reason').keys():
                    reasons['owner_rollback_reason'][reason] = reasons['owner_rollback_reason'][reason] + 1
                else:
                    reasons['owner_rollback_reason'][reason] = 1
            elif 'pre_not_pass_reason' in flow_data.get('data').keys():
                reason = flow_data.get('data').get('pre_not_pass_reason')
                if reason in reasons.get('pre_not_pass_reason').keys():
                    reasons['pre_not_pass_reason'][reason] = reasons['pre_not_pass_reason'][reason] + 1
                else:
                    reasons['pre_not_pass_reason'][reason] = 1

        for key, val in reasons.items():
            if len(val) > 0:
                exist_bug = val.get('exist_bug', 0)
                publish_problem = val.get('publish_problem', 0)
                commit_problem = val.get('commit_problem', 0)
                code_conflict = val.get('code_conflict', 0)
                code_stale = val.get('code_stale', 0)
                other = val.get('other', 0)
                try:
                    publish_abandon_statistics_collection.insert_one({'rollback_name':key, 'exist_bug': exist_bug, 'publish_problem': publish_problem, 'commit_problem': commit_problem, 'code_conflict': code_conflict, 'code_stale': code_stale, 'other': other, 'date': datetime.datetime.strptime(begin_date, '%Y-%m-%d %H:%M:%S')})
                except Exception, e:
                    root_logger.exception("insert to publish_abandon_statistics_collection error, %s", e)
                    return False
        return True

    # 按项目统计发布成功及回退的次数
    @staticmethod
    def add_project_publish_statistics(begin_date, end_date):
        workflow_data = WorkflowService.list('', list_all=True, order_by='create_at', list_history=True, task_type=None,
                                         order_desc=None, begin_date=begin_date, end_date=end_date)
        workflow_data_list = [e.serialize() for e in workflow_data]

        projects_publish_data = dict()
        for workflow in workflow_data_list:
            flow_id = workflow.get('id')
            publish_data = flow_data_collection.find_one({'flow_id': flow_id})
            project_id = publish_data.get('data').get('project_id')
            if not project_id in projects_publish_data:
                projects_publish_data[project_id] = dict()
                projects_publish_data[project_id]['complete'] = 0
                projects_publish_data[project_id]['abandon'] = 0

            if workflow.get('current_task_type') == 'prd_complete':
                projects_publish_data[project_id]['complete'] = projects_publish_data[project_id]['complete'] + 1
            elif workflow.get('current_task_type') == 'abandon':
                projects_publish_data[project_id]['abandon'] = projects_publish_data[project_id]['abandon'] + 1

        for k,v in projects_publish_data.items():
            app = ProjectService.get_project(int(k)).brief()
            project_id = k
            name = app.get('name')
            department = app.get('dept_label')
            product = app.get('product_label')
            type = app.get('type')
            owner = app.get('owner').get('real_name')
            owner_id = app.get('owner').get('name')
            complete = v.get('complete', 0)
            abandon = v.get('abandon', 0)
            total = complete+abandon
            try:
                project_publish_statistics_collection.insert_one({'project_id': project_id, 'name': name, 'department': department, 'product': product, 'type': type, 'owner': owner, 'owner_id': owner_id,
                                                                  'complete': complete,  'abandon': abandon, 'total': total, 'date': datetime.datetime.strptime(begin_date, '%Y-%m-%d %H:%M:%S')})
            except Exception, e:
                root_logger.exception("insert to project_publish_statistics_collection error, %s", e)
                return False
        return True

    # 按产品模块统计发布成功率
    @staticmethod
    def get_publish_statistics(begin_date, end_date, group, query):
        begin_date = datetime.datetime.strptime(begin_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        if group == 'department' and query is not None:
            group_by = {'department': '$department', 'product': '$product'}
            match = {'date': {'$gte': begin_date, '$lte': end_date}, 'department': query}
        else:
            group_by = {'department': '$department', 'product': '$product'}
            match = {'date':{'$gte': begin_date, '$lte': end_date}}
        pipeline = [{'$match': match},
                    {'$group': {'_id': group_by, 'total':{'$sum': '$total'}, 'complete': {'$sum': '$complete'}, 'abandon':{'$sum': '$abandon'}}}]
        result = product_publish_statistics_collection.aggregate(pipeline, allowDiskUse=True)
        records = [r for r in result]
        total = 0
        for e in records:
            e['department'] = e['_id']['department']
            e['product'] = e['_id']['product']
            e['success'] = round(float(e['complete'])/e['total'], 2)
            e['success_str'] = format(float(e['complete'])/e['total'], '.0%')
            total = total + e['total']
            e.pop('_id')
        records = sorted(records, key=itemgetter('success'), reverse=True)
        return records, total

    # 发布项目回退原因统计
    @staticmethod
    def get_abandon_statistics(begin_date, end_date):
        begin_date = datetime.datetime.strptime(begin_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        pipeline = [{'$match': {'date': {'$gte': begin_date, '$lte': end_date}}},
                    {'$group': {'_id': {'rollback_name': '$rollback_name'}, 'exist_bug': {'$sum': '$exist_bug'}, 'publish_problem': {'$sum': '$publish_problem'}, 'commit_problem': {'$sum': '$commit_problem'},
                                 'code_conflict': {'$sum': '$code_conflict'}, 'code_stale': {'$sum': '$code_stale'}, 'other': {'$sum': '$other'}}}]

        result = publish_abandon_statistics_collection.aggregate(pipeline, allowDiskUse=True)
        records = [r for r in result]
        ret = dict()
        for r in records:
            rollback_name = r['_id']['rollback_name']
            r.pop('_id')
            ret[rollback_name] = r
        return ret

    # 发布项目退回次数前10统计
    @staticmethod
    def get_project_abandon_statistics(begin_date, end_date):
        begin_date = datetime.datetime.strptime(begin_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        pipeline = [{'$match': {'date': {'$gte': begin_date, '$lte': end_date}}},
                    {'$group': {'_id': {'project_id': '$project_id', 'name': '$name', 'department': '$department', 'product': '$product', 'type': '$type', 'owner': '$owner'}, 'total_abandon': {'$sum': '$abandon'}}},
                    {'$sort': {'total_abandon': -1}},
                    {'$limit': 10}
                    ]
        result = project_publish_statistics_collection.aggregate(pipeline, allowDiskUse=True)
        records = [r for r in result]
        new_list = list()
        for record in records:
            if record['total_abandon'] == 0:
                continue
            else:
                for key, val in record['_id'].items():
                    record[key] = val
                record.pop('_id')
                new_list.append(record)
        return new_list

    # 按部门以及项目负责人统计发布成功率
    @staticmethod
    def get_project_statistics(query_by, query, begin_date, end_date):
        begin_date = datetime.datetime.strptime(begin_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        if query_by == 'owner':
            group_by = {'product': '$product', 'department': '$department'}
            match = {'date': {'$gte': begin_date, '$lte': end_date}, 'owner': query}
        else:
            group_by = {'owner': '$owner'}
            match = {'date': {'$gte': begin_date, '$lte': end_date}, 'department': query}
        pipeline = [{'$match': match},
                    {'$group': {'_id': group_by, 'total': {'$sum': '$total'}, 'complete': {'$sum': '$complete'}, 'abandon':{'$sum': '$abandon'}}}]
        result = project_publish_statistics_collection.aggregate(pipeline, allowDiskUse=True)
        records =  [r for r in result]
        total = 0
        complete = 0
        abandon = 0
        ret = dict()
        for record in records:
            if query_by == 'owner':
                total = total + record['total']
                complete = complete + record['complete']
                abandon = abandon + record['abandon']
            record['success'] = round(float(record['complete']) / record['total'], 2)
            record['success_str'] = format(float(record['complete']) / record['total'], '.0%')
            for key, val in record['_id'].items():
                record[key] = val
            record.pop('_id')
        sorted_records = sorted(records, key=itemgetter('success'), reverse=True)
        ret['owner_record'] = dict()
        ret['owner_product_record'] = list()
        if query_by == 'owner' and len(records) > 0:
            ret['owner_record']['success'] = round(float(complete) /total, 2)
            ret['owner_record']['success_str'] = format(float(complete) /total, '.0%')
            ret['owner_record']['owner'] = query
            ret['owner_record']['total'] = total
            ret['owner_record']['complete'] = complete
            ret['owner_record']['abandon'] = abandon
            ret['owner_product_record'] = sorted_records
            ret['total'] = total
        else:
            ret['owner_record'] = sorted_records
        return ret

    # 获取在指定时间内完成发布的项目的owner
    @staticmethod
    def get_project_owners(begin_date, end_date):
        begin_date = datetime.datetime.strptime(begin_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        result = project_publish_statistics_collection.find({'date':{'$gte': begin_date, '$lte': end_date}})
        record_list = [r for r in result]
        owners = list()
        for record in record_list:
            name = record.get('owner_id')
            user = UserService.get_user_by_name(name).first()
            if user:
                is_exist = False
                for owner in owners:
                    if owner.get('name') == user.name:
                        is_exist = True
                        break
                if not is_exist:
                    owners.append({'name': name, 'real_name': user.real_name})
        return owners