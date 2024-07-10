# -*- coding:utf8 -*-

import os
import datetime
from flask import Blueprint, render_template, request, session, jsonify, make_response, send_from_directory

from app.decorators.access_controle import require_login
from app.decorators.paginate import make_paging
from app.out.regulator import Regulator
from app.out.idb import iDB
from app.services.framework.user_service import UserService
from app.services.flow.workflow import Workflow, WorkflowService
from app.services.publish.precheck_service import PreCheckService
from app.services.project.project_service import ProjectService
from app.services.publish.publish_service import PublishService
from app.services.apprepo_service import ApprepoService
from app.services.framework.file_service import FileService
from app.services.framework.kafka_service import KafkaService
from app.services.project.project_participant_service import ProjectParticipantService
from app.services.project.project_record_service import ProjectRecordService
from app.services.project.sql_scripts_project_service import SQLScriptsProjectService
from app.util import Util
from app import app


projectProfile = Blueprint('projectProfile', __name__)


@projectProfile.route("/detail/<string:project_id>", methods=['GET', 'POST'])
@require_login()
def detail(project_id):
    return render_template('project/detail/detail.html', project_id=project_id)


@projectProfile.route("/detail/basic/<string:project_id>", methods=['GET'])
@require_login()
def detail_basic(project_id):
    project = ProjectService.get_project(project_id)
    ret = dict()
    if project:
        ret['result'] = 1
        ret['data'] = project.serialize()
    else:
        ret['result'] = -1
    return jsonify(ret)


@projectProfile.route("/precheck/<string:project_id>", methods=['POST'])
@require_login()
def precheck(project_id):
    data = request.form
    oa_img = request.files.get('oa_img')
    dept_code = data.get('dept_code')
    type = data.get('type')
    publish_type = data.get('publish_type')
    issue_id = data.get('issue_id')
    oa_id = data.get('oa_id')
    scheduled_time = data.get('scheduled_time')
    publish_comment = data.get('publish_comment')
    ret = dict()
    if publish_type == 'regular':
        # 检查时间
        result = PublishService.verify_publish_time(dept_code=dept_code)
        if not result:
            ret['message'] = u'该发布不在常规发布时间段内'
            ret['result'] = -1
            return jsonify(ret)
    else:
        if len(data) > 2:
            if publish_type == 'urgent':
                if oa_id != app.config.get('SPECIAL_OA_ID') and (not oa_id or not oa_img):
                    ret['message'] = u'缺少OA单号或者OA截图'
                    ret['result'] = -1
                    return jsonify(ret)
            else:
                # 检查时间
                result = PublishService.verify_publish_time(dept_code=dept_code)
                if not result:
                    ret['message'] = u'该发布不在常规发布时间段内'
                    ret['result'] = -1
                    return jsonify(ret)
            if issue_id:
                # 检查单号
                result, msg = Regulator.queryFault(issue_id)
                ret['message'] = msg
                if not result:
                    ret['result'] = -1
                    return jsonify(ret)
    data = PreCheckService.apply_publish_precheck(project_id, issue_id, oa_id)
    if data.get('oa_id_ok') and oa_id != app.config.get('SPECIAL_OA_ID'):
        file_name = FileService.upload(oa_img, oa_id, 'oa')
        data['oa_img'] = file_name
    data['project_type'] = type
    data['publish_type'] = publish_type
    data['scheduled_time'] = scheduled_time
    data['publish_comment'] = publish_comment
    ret['result'] = 1
    ret['data'] = data
    return jsonify(ret)


@projectProfile.route("/apply_publish/<string:project_id>", methods=['POST'])
@require_login()
def apply_publish(project_id):
    precheck_data = request.json
    result, data = ProjectService.apply_publish(project_id, precheck_data)
    ret = dict()
    if result:
        publish_id = data.get('flow_id')
        flow_type = data.get('flow_type')
        flow_data = data.get('flow_data')
        Workflow.new(publish_id, flow_type, flow_data=flow_data, creator_id=session['userId'])
        publish_type = precheck_data.get('publish_type')
        # 申请发布指向发布时url, 申请发布时添加如下comment
        comment = u"<a href=\"https://duang-engine.zhonganonline.com/publish/{}/detail\">查看发布单({})</a>".format(publish_id, publish_id)
        if publish_type == 'regular':
            # 记录常规发布
            ProjectRecordService.add_project_record(project_id, session['userId'], 'owner', 'PUBLISH',
                                                    'PUBLISH_NORMAL', comment, datetime.datetime.now())
        elif publish_type == 'urgent':
            # 记录紧急发布
            now_time = datetime.datetime.now()
            if 9 > now_time.hour >= 0:
                ProjectRecordService.add_project_record(project_id, session['userId'], 'owner',
                                                        'PUBLISH', 'PUBLISH_URGENCY_ZERO_POINTS', comment, now_time)
            elif 24 > now_time.hour >= 20:
                ProjectRecordService.add_project_record(project_id, session['userId'], 'owner', 'PUBLISH',
                                                        'PUBLISH_URGENCY_TWENTY_POINTS', comment, now_time)
            else:
                ProjectRecordService.add_project_record(project_id, session['userId'], 'owner', 'PUBLISH',
                                                        'PUBLISH_URGENCY_OTHERS', comment, now_time)
        ret['result'] = 1
        ret['data'] = publish_id
    else:
        ret['result'] = -1
    return jsonify(ret)


@projectProfile.route("/delete/<string:project_id>", methods=['POST'])
@require_login()
def delete(project_id):
    # 删除project成功发送kafka消息
    res = ProjectService.delete_project(project_id)
    ret = dict()
    if res:
        ret['result'] = 1
    else:
        ret['result'] = 0
    return jsonify(ret)


@projectProfile.route("/update/<string:project_id>", methods=['POST'])
@require_login()
def update(project_id):
    # 修改project修改信息
    # 如果发布时间更新需要kafka通知test
    name = request.values.get('name')
    alias = request.values.get('alias')
    project_type = request.values.get('type')
    system_id = request.values.get('app_system_id')
    product_id = request.values.get('product_id')
    product_code = request.values.get('product_code')
    product_label = request.values.get('product_label')
    summary = request.values.get('summary')
    owner_id = request.values.get('owner_id')
    ba_id = request.values.get('ba_id')
    begin_date = request.values.get('begin_date')
    expect_publish_date = request.values.get('expect_publish_date')
    sql_script_url = request.values.get('sql_script_url')
    qa = request.values.get('qa')
    developer = request.values.get('developer')
    code_review = request.values.get('code_review')
    company_id = request.values.get('company_id')
    company_code = request.values.get('company_code')
    company_label = request.values.get('company_label')
    dept_id = request.values.get('dept_id')
    dept_code = request.values.get('dept_code')
    dept_label = request.values.get('dept_label')
    ret = dict()

    res, msg_flag = ProjectService.update_project(project_id, name=name, alias=alias, project_type=project_type,
                                                  company_id=company_id, company_code=company_code,
                                                  company_label=company_label,
                                                  dept_id=dept_id, dept_code=dept_code, dept_label=dept_label,
                                                  product_id=product_id, product_code=product_code,
                                                  product_label=product_label, system_id=system_id,
                                                  summary=summary, owner_id=owner_id, ba_id=ba_id,
                                                  begin_date=begin_date, expect_publish_date=expect_publish_date,
                                                  sql_script_url=sql_script_url)

    if res:
        # 特定部门的测试人员为sqa角色
        if str(dept_id) in app.config['SQA_DEPT']:
            r1 = ProjectParticipantService.add_participant(project_id, qa, 'sqa')
        else:
            r1 = ProjectParticipantService.add_participant(project_id, qa, 'qa')
        r2 = ProjectParticipantService.add_participant(project_id, developer, 'dev')
        r3 = ProjectParticipantService.add_participant(project_id, code_review, 'code_review')
        if r1 and r2 and r3:
            if msg_flag:
                data = KafkaService.assemble_kafka_json(project_id, 'update_publish_date', env=None, publish_id=None)
                KafkaService.produce(data)
            ret['success'] = 1
            return jsonify(ret)

    ret['success'] = 0
    ret['error'] = u'project基本信息更新错误'
    return jsonify(ret)


@projectProfile.route("/approve/<string:project_id>", methods=['POST'])
@require_login()
def approve(project_id):
    data = request.form
    action = data.get('action')
    operator_id = data.get('operator_id')
    dept_code = data.get("dept_code", None)

    ret = dict()
    if action == 'project_submit':
        sql_res, info = ProjectService.sql_review(project_id, session['userId'], session['userInfo']['name'], dept_code, env_list=['pre', 'prd'], first_submit=True)
    res, message = ProjectService.approve_project(project_id, action, operator_id)
    if res:
        ret['success'] = 1
        if action == 'project_submit' and info != "ok":
            ret['message'] = '<br>'.join(info)
    else:
        ret['success'] = 0
        ret['message'] = message
    return jsonify(ret)


@projectProfile.route("/todo-list", methods=['GET'])
@require_login()
def todo_list():
    return render_template('project/todo-list.html')


@projectProfile.route("/todo-project-list", methods=['GET'])
@require_login()
def todo_project_list():
    privileges = session.get('userPrivileges')
    user_id = session.get('userId')
    begin_date_start = datetime.date.today() - datetime.timedelta(days=30)
    query = request.values.get('query')
    privilege_list = list()
    for pn, rw in privileges.items():
        if rw > 0:
            privilege_list.append(pn)
    data = dict()
    data.update(ProjectService.list_project_by_privilege(query, ['0', '1'], begin_date_start, None, None, None, user_id, privilege_list))
    if privileges.get('dba') > 0:
        # 作为SQL Review的未完成项目（状态展示：待Code Review）
        sql_project_list = SQLScriptsProjectService.list_sql_scripts_project(['review', 'not_pass'])
        project_id_list = [e.get('project_id') for e in sql_project_list]
        project_list = list()
        for one in project_id_list:
            project = ProjectService.get_project(one)
            if project:
                data[one] = {'data': project.brief(), 'prvg': ['dba']}
        data.update(project_list)
    ret = dict()
    ret['result'] = 1
    ret['data'] = data
    return jsonify(ret)


@projectProfile.route("/todo-publish-list", methods=['GET'])
@require_login()
def todo_publish_list():
    privileges = session.get('userPrivileges')
    user_id = session.get('userId')
    data = dict()
    publish_id_dict = dict()
    if privileges.get('qa') > 0 or privileges.get('sqa') > 0:
        # 发布中的待测试执行的发布单
        flow_id_list = WorkflowService.list_participated_flow_id(user_id, privilege_list=['qa', 'sqa'])
        for one in flow_id_list:
            if one not in publish_id_dict:
                publish_id_dict[one] = list()
            publish_id_dict[one].append('qa')
    if privileges.get('dba') > 0:
        # 发布中的待DBA执行的发布单
        flow_id_list = WorkflowService.list_participated_flow_id(user_id, privilege_list=['dba'])
        for one in flow_id_list:
            if one not in publish_id_dict:
                publish_id_dict[one] = list()
            publish_id_dict[one].append('dba')
    if privileges.get('pe') > 0:
        # 发布中的待PE执行的发布单
        flow_id_list = WorkflowService.list_participated_flow_id(user_id, privilege_list=['pe'])
        for one in flow_id_list:
            if one not in publish_id_dict:
                publish_id_dict[one] = list()
            publish_id_dict[one].append('pe')
    if privileges.get('monitor') > 0:
        # 发布中的待监控执行的发布单
        flow_id_list = WorkflowService.list_participated_flow_id(user_id, privilege_list=['monitor'])
        for one in flow_id_list:
            if one not in publish_id_dict:
                publish_id_dict[one] = list()
            publish_id_dict[one].append('monitor')
    # 发布中的待owner执行的发布单
    flow_id_list = WorkflowService.list_participated_flow_id(user_id, privilege_list=['owner'])
    for one in flow_id_list:
        if one not in publish_id_dict:
            publish_id_dict[one] = list()
        publish_id_dict[one].append('owner')
    for publish_id, prvg_list in publish_id_dict.items():
        d = PublishService.get_publish_info(publish_id, with_project_data=True, with_flow_data=False)
        data[publish_id] = {'data': d, 'prvg': prvg_list}
    ret = dict()
    ret['result'] = 1
    ret['data'] = data
    return jsonify(ret)


@projectProfile.route("/list", methods=['GET'])
@require_login()
def project():
    return render_template('project/list.html')


@projectProfile.route("/project_list", methods=['GET'])
@require_login()
@make_paging("projectList")
def project_list():
    participant = request.values.get('participant')
    name = request.values.get('name')
    publish_status_str = request.values.get('publish_status')
    begin_date_start = request.values.get('begin_date_start')
    begin_date_end = request.values.get('begin_date_end')
    publish_date_start = request.values.get('publish_date_start')
    publish_date_end = request.values.get('publish_date_end')
    department_id_list_str = request.values.get('department_id_list')
    if department_id_list_str:
        department_id_list = department_id_list_str.split(',')
    else:
        department_id_list = list()
    if publish_status_str:
        publish_status = publish_status_str.split(',')
    else:
        publish_status = [0, 1]
    participant_id = None
    if participant:
        participant_id = UserService.get_user_id(participant)
    return ProjectService.project_list(name, publish_status, begin_date_start, begin_date_end, publish_date_start, publish_date_end, participant_id, None, department_id_list)


@projectProfile.route("/record/info/<int:project_id>", methods=['GET'])
@require_login()
def record_list(project_id):
    # project日志记录列表，按照project id倒叙排列
    records = ProjectRecordService.query_project_record(project_id)
    ret = dict()
    ret['success'] = 1
    ret['data'] = records
    return jsonify(ret)


@projectProfile.route("/test/info/<string:project_id>", methods=['GET'])
@require_login()
def get_test_details(project_id):
    test_details = ProjectService.get_test_details(project_id)
    ret = dict()
    ret['result'] = 1
    ret['data'] = test_details
    return jsonify(ret)


@projectProfile.route("/test/info/save/<string:project_id>", methods=['POST'])
@require_login()
def update_project_test(project_id):
    ret = dict()
    data = request.form
    test_request = data.get('request')
    api = data.get('api')
    smoke = data.get('smoke')
    keynote = data.get('keynote')
    if len(request.files) > 0:
        test_file = request.files.get('test_file')
        file_name = FileService.upload(test_file, project_id, 'test')
    else:
        file_name = data.get('test_file')
    result = ProjectService.update_test_details(project_id, test_request, api, smoke, keynote, file_name)
    if result:
        ret['result'] = 1
    else:
        ret['result'] = -1
    return jsonify(ret)


@projectProfile.route("/test/download/<filename>", methods=['GET'])
@require_login()
def download_test_file(filename):
    directory = os.path.join(app.config.get('UPLOAD_FOLDER'), 'test')
    response = make_response(send_from_directory(directory, filename, as_attachment=True))
    response.headers["Content-Disposition"] = "attachment; filename={}".format(filename.encode().decode('latin-1'))
    return response


@projectProfile.route("/list_all_participant", methods=['GET'])
@require_login()
def list_all_participant():
    project_id = request.values.get('project_id')
    data = ProjectService.query_participant(project_id)
    ret = dict()
    ret['data'] = data
    return jsonify(ret)


@projectProfile.route("/change_bad_man", methods=['POST'])
@require_login()
def change_bad_man():
    record_id = request.values.get('record_id')
    publish_id = request.values.get('publish_id')
    operator_id = request.values.get('operator_id')
    reason = request.values.get('reason')
    bad_man = request.values.get('bad_man')
    rollback_type = request.values.get('rollback_type')
    result = ProjectService.change_bad_man(record_id, publish_id, operator_id, reason, bad_man, rollback_type)
    ret = dict()
    if result:
        ret['result'] = 1
    else:
        ret['result'] = -1
    return jsonify(ret)


@projectProfile.route("/sql_review/list/<string:project_id>", methods=['GET'])
@require_login()
def list_sql_review(project_id):
    ret = dict()
    result = ProjectService.get_sql_review(project_id)
    ret["result"] = 1
    ret["data"] = result
    return jsonify(ret)


@projectProfile.route("/sql_review/add/<string:project_id>", methods=['POST'])
@require_login()
def add_sql_review(project_id):
    data = request.json
    server_id = data.get("company_id")
    sql_execute_config = data.get("sql_execute_config")
    result, message = ProjectService.add_sql_review(project_id, sql_execute_config, server_id)
    ret = dict()
    if result:
        ret['result'] = 1
    else:
        ret['result'] = -1
        ret['message'] = message
    return jsonify(ret)


@projectProfile.route("/sql_review/delete/<string:project_id>", methods=['POST'])
@require_login()
def del_sql_review(project_id):
    result = SQLScriptsProjectService.del_sql_scripts_project(project_id)
    if result:
        return jsonify({"result": 1})
    else:
        return jsonify({"result": -1})


@projectProfile.route("/sql_review/update/<string:project_id>", methods=['POST'])
@require_login()
def mod_sql_review(project_id):
    data = request.json
    result = SQLScriptsProjectService.mod_sql_scripts_project(project_id, sql_execution_config=data)
    if result:
        return jsonify({"result": 1})
    else:
        return jsonify({"result": -1})


@projectProfile.route("/sql_review/<string:project_id>", methods=['POST'])
@require_login()
def sql_review(project_id):
    ret = dict()
    dept_code = request.values.get("dept_code")
    env = request.values.get("env")
    sql_res, info = ProjectService.sql_review(project_id, session['userId'], session['userInfo']['name'], dept_code, env_list=[env])
    if sql_res:
        ret['result'] = 1
    else:
        ret['result'] = -1
        ret['error'] = '<br>'.join(info)
    return jsonify(ret)


@projectProfile.route("/sql_review/status/update/<string:project_id>", methods=['POST'])
@require_login()
def update_sql_review_status(project_id):
    env = request.values.get("env")
    status = request.values.get("status")
    remark = request.values.get("remark", None)
    manual = request.values.get('manual')
    manual = Util.jsbool2pybool(manual)

    result, msg = ProjectService.update_sql_review_status(project_id, session['userId'], env, status, remark=remark, manual=manual)
    ret = dict()
    if result:
        ret['result'] = 1
    else:
        ret['result'] = -1
        ret['message'] = msg
    return jsonify(ret)


@projectProfile.route("/sql_review/detail", methods=['POST'])
@require_login()
def get_sql_review_detail():
    sql_svn_path = request.values.get("sql_svn_path")
    revision = request.values.get("revision")
    result, detail = iDB.get_sql_review_detail(sql_svn_path, revision)
    ret = dict()
    if result:
        ret['result'] = 1
        ret['data'] = detail
    else:
        ret['result'] = -1
        ret['info'] = detail
    return jsonify(ret)


@projectProfile.route("/<int:project_id>/code-review/status", methods=['GET'])
@require_login()
def list_project_code_review_status(project_id):
    data = ApprepoService.list_project_code_review_status(project_id)
    ret = dict()
    if data is not None:
        ret['result'] = 1
        ret['data'] = data
    else:
        ret['result'] = -1
    return jsonify(ret)


@projectProfile.route("/sql_execute/disable/<string:project_id>", methods=['POST'])
@require_login()
def disable_sql_execute(project_id):
    env = request.values.get('env')
    project = SQLScriptsProjectService.get_sql_scripts_project(project_id)
    result = SQLScriptsProjectService.mod_sql_status(project_id, env, 'init', project.get('publish_id'))
    ProjectRecordService.add_project_record(project_id, session['userId'], 'owner', '-',
                                            'CANCLE_{}_SQL_EXECUTE'.format(env.upper()), None, datetime.datetime.now())
    ret = dict()
    if result:
        ret['result'] = 1
    else:
        ret['result'] = -1
    return jsonify(ret)


