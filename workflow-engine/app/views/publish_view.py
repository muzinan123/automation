# -*- coding:utf8 -*-

import os
from flask import Blueprint, jsonify, render_template, request, session, make_response, send_from_directory, send_file

from app.out.cmdb_core import CMDBCore
from app.decorators.paginate import make_paging_mongo
from app.decorators.access_controle import require_login, privilege
from app.services.flow.workflow import WorkflowService
from app.services.project.project_record_service import ProjectRecordService
from app.services.publish.publish_service import PublishService
from app.services.publish.publish_statistics_service import PublishStatisticsService
from app.services.publish.experienced_app_list_service import ExperiencedAppListService
from app.services.publish.hot_pool_service import HotPoolService
from app.util import Util
from app import app

publishProfile = Blueprint('publishProfile', __name__)


@publishProfile.route("/manage", methods=['GET'])
@require_login()
def publish_list():
    return render_template('publish/manage/manage.html')


@publishProfile.route("/switch", methods=['GET'])
@require_login()
def publish_switch():
    return render_template('publish/switch.html')


@publishProfile.route("/<string:flow_id>/detail", methods=['GET'])
@require_login()
def publish_detail(flow_id):
    flow = WorkflowService.get(flow_id)
    if flow:
        return render_template('publish/publish-detail.html', flow_id=flow_id, current_task_type=flow.current_task_type)
    else:
        return "error", 404


@publishProfile.route("/<string:publish_id>/data", methods=['GET'])
@require_login()
def publish_data(publish_id):
    return jsonify(PublishService.get_publish_info(publish_id, with_project_data=True, with_flow_data=False))


@publishProfile.route("/<string:publish_id>/change_scheduled_time", methods=['POST'])
@require_login()
def publish_change_scheduled_time(publish_id):
    scheduled_time = request.values.get('scheduled_time')
    result = PublishService.change_scheduled_time(publish_id, scheduled_time)
    ret = dict()
    if result:
        ret['result'] = 1
    else:
        ret['result'] = -1
    return jsonify(ret)


@publishProfile.route("/manage/list/ids", methods=['GET'])
@require_login()
def list_publish_ids():
    # 获取发布单中各环境中各个项目信息
    ret = dict()
    ret_data = list()
    data = WorkflowService.list(query=None, list_all=False)
    ret_data = [e.id for e in data]
    ret['result'] = 1
    ret['data'] = ret_data
    return jsonify(ret)


@publishProfile.route("/manage/publish/info", methods=['POST'])
@require_login()
def get_publish_info():
    # 获取发布单中各环境中各个项目信息
    ret = dict()
    ret_data = list()
    ids = request.json
    for publish_id in ids:
        info = PublishService.get_publish_info(publish_id, with_project_data=True, with_flow_data=True, operator_id=session['userId'])
        ret_data.append(info)
    ret['result'] = 1
    ret['data'] = ret_data
    return jsonify(ret)


@publishProfile.route("/switch/info", methods=['GET'])
@require_login()
def publish_switch_info():
    ret = dict()
    data = PublishService.get_publish_switch_info()
    data.pop('_id')
    ret['result'] = 1
    ret['data'] = data
    return jsonify(ret)


@publishProfile.route("/switch/save", methods=['POST'])
@require_login()
@privilege('pe')
def save_switch_info():
    ret = dict()
    data = request.json
    result = PublishService.mod_publish_switch_info(data)
    if result:
        ret['result'] = 1
    else:
        ret['result'] = -1
    return jsonify(ret)


@publishProfile.route("/app/list", methods=['GET'])
@require_login()
def publish_app_list():
    return render_template('publish/experienced-app-list.html')


@publishProfile.route("/app/list/list", methods=['GET'])
@require_login()
@make_paging_mongo('appList')
def publish_app_list__list():
    query = request.values.get('query', None)
    pipeline, collection = ExperiencedAppListService.list_experience(query)
    return pipeline, collection


@publishProfile.route("/arrange/query", methods=['GET'])
@require_login()
def publish_arrange_query():
    env = request.values.get('env')
    app_id = request.values.get('app_id')
    res_type = request.values.get('res_type')
    data = CMDBCore.query_arrange(env, app_id, res_type)
    ret = dict()
    if data:
        ret['result'] = 1
        ret['data'] = data
    else:
        ret['result'] = -1
    return jsonify(ret)


@publishProfile.route("/republish", methods=['POST'])
@require_login()
@privilege('pe')
def publish_republish():
    data =request.json
    app_id = data.get('app_id')
    env = data.get('env')
    fixed_server_list = data.get('fixed_server_list')
    publish_id = data.get('publish_id')
    operator_id = session['userId']
    if env == 'pre':
        PublishService.republish_pre_app(app_id, fixed_server_list, publish_id, operator_id)
    elif env == 'prd':
        PublishService.republish_prd_app(app_id, fixed_server_list, publish_id, operator_id)
    ret = dict()
    ret['result'] = 1
    return jsonify(ret)


@publishProfile.route("/<string:publish_id>/check_prd_hot_app", methods=['POST'])
@require_login()
def publish_check_prd_hot_app(publish_id):
    app_id_list = request.json
    ret = dict()
    running_data = list()
    for app_id in app_id_list:
        running_one = HotPoolService.get_running_hot_prd_app(app_id)
        if running_one:
            running_data.append(running_one)

    if running_data:
        # 存在冲突，无法同时进行打包操作
        ret['running_data'] = running_data
        ret['flag'] = 'has_running'
        return jsonify(ret)

    up_data = list()
    for app_id in app_id_list:
        hot_app_list = HotPoolService.list_up_hot_prd_app(app_id, publish_id)
        up_data.extend(hot_app_list)

    down_data = list()
    for app_id in app_id_list:
        hot_app_list = HotPoolService.list_down_hot_prd_app(app_id, publish_id)
        down_data.extend(hot_app_list)

    if False in [e.get('ready') for e in down_data]:
        # 存在低版本应用，但是没有ready
        ret['not_ready_data'] = list()
        for d in down_data:
            if not d.get('ready'):
                ret['not_ready_data'].append(d)
        ret['flag'] = 'has_not_ready'
        return jsonify(ret)

    ret['down_data'] = down_data
    ret['up_data'] = up_data
    if down_data and not up_data:
        # 存在低版本应用，会skip
        ret['flag'] = 'has_down'
    elif not down_data and up_data:
        # 存在高版本应用，推荐打包高版本的应用
        ret['flag'] = 'has_up'
    elif down_data and up_data:
        # 同时存在高版本和低版本应用
        ret['flag'] = 'has_up_and_down'
    else:
        ret['flag'] = 'ok'

    return jsonify(ret)


@publishProfile.route("/skip_prd_app", methods=['POST'])
@require_login()
def publish_skip_prd_app():
    skip_app_list = request.json
    for skip_app in skip_app_list:
        app_id = skip_app.get('app_id')
        publish_id = skip_app.get('publish_id')
        HotPoolService.skip_hot_prd_app(app_id, publish_id)
        PublishService.skip_prd_app(app_id, publish_id)
    # TODO: 完善一下结果判断
    ret = dict()
    ret['result'] = 1
    return jsonify(ret)


@publishProfile.route("/oa/download/<filename>", methods=['GET'])
@require_login()
def download_oa_image(filename):
    directory = os.path.join(app.config.get('UPLOAD_FOLDER'), 'oa')
    response = make_response(send_from_directory(directory, filename, as_attachment=False))
    return response


@publishProfile.route('/history', methods=['GET'])
@require_login()
def publish_history():
    return render_template('publish/publish-history.html')


@publishProfile.route('/history/list', methods=['GET'])
@require_login()
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


@publishProfile.route('/history/export/export-history-list.xls', methods=['GET'])
@require_login()
def export_publish_history():
    headers = [{'key': 'id', 'name': '发布单号'}, {'key': 'name', 'name':'项目名称' },
               {'key': 'project_id', 'name': '项目编号'}, {'key': 'jira_key', 'name':'jira_编号' },
               {'key': 'jira_id', 'name': 'jira_id'}, {'key': 'type', 'name': '项目类型'},
               {'key': 'publish_type', 'name': '发布类型'}, {'key': 'app_info', 'name': '发布应用'},
               {'key': 'status', 'name': '发布状态'}, {'key': 'expect_publish_date', 'name': '期望发布日'},
               {'key': 'qa', 'name': '测试验证人员'}, {'key': 'owner', 'name': 'Owner'},
               {'key': 'ba', 'name': 'BA'}, {'key': 'operator', 'name': '最后操作'},
               {'key': 'last_change_date', 'name': '变更时间'}, {'key': 'description', 'name': '说明'},
               {'key': 'dept_label', 'name': '部门名称'}, {'key': 'product_label', 'name': '产品线名称'}
               ]
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
    workflow_list = WorkflowService.list('', list_all=True, order_by='create_at', list_history=True,
                                         task_type=current_task_type, order_desc=True, begin_date=change_begin_date,
                                         end_date=change_end_date)
    data_list = list()
    ret = dict()
    for workflow in [w.serialize() for w in workflow_list]:
        data = dict()
        flow_id = workflow.get('id')
        publish_data = PublishService.get_publish_info(flow_id, with_project_data=True, with_flow_data=True,
                                                       operator_id=None, project_type=project_type,
                                                       publish_type=publish_type, departments=departments)
        if publish_data:
            project = publish_data.get('project')
            flow_data = publish_data.get('publish')
            last_operator = ''
            if project:
                records = ProjectRecordService.query_project_record(project.get('id'))
                if records:
                    last_operator = records[0].get('operator')
                data['id'] = flow_id
                data['name'] = project.get('name')
                data['project_id'] = flow_data.get('project_id')
                if project.get('jira_issue_id'):
                    data['jira_id'] = "issue_id:{}".format(project.get('jira_issue_id'))
                    data['jira_key'] = "issue_key:{}".format(project.get('jira_issue_key'))
                elif project.get('jira_version_id'):
                    data['jira_id'] = "version_id:{}".format(project.get('jira_version_id'))
                    data['jira_key'] = "version_id:{}".format(project.get('jira_version_id'))
                data['type'] = project.get('type')
                data['publish_type'] = flow_data.get('publish_type')
                apps = list()
                for key, val in flow_data.get('app_info').items():
                    apps.append(val.get('name'))
                data['app_info'] = apps
                data['status'] = workflow.get('current_task_type')
                data['expect_publish_date'] = project.get('expect_publish_date')
                data['qa'] = flow_data.get('qa')
                data['owner'] = project.get('owner').get('real_name')
                data['ba'] = project.get('ba').get('real_name')
                data['last_change_date'] = workflow.get('modify_at')
                data['description'] = workflow.get('current_task_type')
                data['dept_label'] = project.get('dept_label')
                data['product_label'] = project.get('product_label')
                data['operator'] = last_operator
                data_list.append(data)

    book = dict()
    book['history'] = dict()
    book['history']['data'] = data_list
    book['history']['headers'] = headers
    excel_file = Util.export_excel(book)
    return send_file(excel_file, mimetype='application/vnd.ms-excel')


@publishProfile.route('/app-sort', methods=['POST'])
@require_login()
def app_sort():
    project_id = request.json.get('project_id')
    publish_id = request.json.get('publish_id')
    if project_id and publish_id:
        resutl = PublishService.sort_app(project_id, publish_id)
        ret = dict()
        if resutl:
            ret['result'] = 1
        else:
            ret['result'] = -1
        return jsonify(ret)
    return "error", 400


@publishProfile.route('/data/update', methods=['POST'])
@privilege('pe')
@require_login()
def update_flow_data():
    flow_id = request.json.get('flow_id')
    flow_data = request.json.get('flow_data')
    dzbd = request.json.get('dzbd')
    env = request.json.get('env')
    app_list = request.json.get('app_list')
    result = PublishService.mod_publish_data(flow_id, flow_data, dzbd, env, app_list)
    if result:
        return jsonify({'result': 1})
    else:
        return jsonify({'result': -1})
