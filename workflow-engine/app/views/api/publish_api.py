# -*- coding:utf8 -*-

from flask import Blueprint, jsonify, request

from app.decorators.access_controle import api
from app.services.flow.workflow import WorkflowService
from app.services.publish.publish_service import PublishService
from app.services.project.project_record_service import ProjectRecordService
from app.services.publish.publish_statistics_service import PublishStatisticsService


publishApiProfile = Blueprint('publishApiProfile', __name__)


@publishApiProfile.route("/statistic", methods=['GET'])
@api()
def get_publish_statistic():
    # zatest质量大盘
    # 所有的操作记录都保存到project_record表中
    # 统计某个时间段产品发布的成功率和失败率
    begin_date = request.values.get('begin_date')
    end_date = request.values.get('end_date')

    department_statistic, total = PublishStatisticsService.get_publish_statistics(begin_date, end_date, "department", None)
    reason_statistic = PublishStatisticsService.get_abandon_statistics(begin_date, end_date)
    project_list = PublishStatisticsService.get_project_abandon_statistics(begin_date, end_date)
    ret = dict()
    ret['result'] = 1
    ret['department_statistic'] = department_statistic
    ret['reason_statistic'] = reason_statistic
    ret['project_list'] = project_list
    return jsonify(ret)


@publishApiProfile.route('/history/list', methods=['GET'])
@api()
def get_publish_history():
    change_begin_date = request.values.get('change_begin_date', None)
    change_end_date = request.values.get('change_end_date', None)
    project_type = request.values.get('project_type', None)
    publish_type = request.values.get('publish_type', None)
    current_task_type = request.values.get('status')
    departments = request.values.get('departments')
    if departments:
        departments = departments.split(',')
    change_begin_date += " 00:00:00"
    change_end_date += " 00:00:00"
    workflow_list = WorkflowService.list('', list_all=True, order_by='create_at', list_history=True, task_type=current_task_type, order_desc=True, begin_date=change_begin_date, end_date=change_end_date)
    data_list = list()
    ret = dict()
    for workflow in [w.serialize() for w in workflow_list]:
        data = dict()
        flow_id = workflow.get('id')
        publish_data = PublishService.get_publish_info(flow_id, with_project_data=True, with_flow_data=True, operator_id=None, project_type=project_type, publish_type=publish_type, departments=departments)
        if publish_data:
            project = publish_data.get('project')
            if project:
                records = ProjectRecordService.query_project_record(project.get('id'))
                last_operator = ''
                if records:
                    last_operator = records[0].get('operator')
                project['last_operator'] = last_operator
            if publish_data.get('publish'):
                publish_data['publish']['id'] = flow_id
                publish_data['publish']['status'] = workflow.get('current_task_type')
                publish_data['publish']['last_change_date'] = workflow.get('modify_at')
                data['flow_data'] = publish_data['publish']
                data['project'] = project
                data_list.append(data)
    ret['result'] = 1
    ret['data'] = data_list
    return jsonify(ret)
