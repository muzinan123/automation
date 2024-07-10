# -*- coding:utf8 -*-
from flask import Blueprint, jsonify, request, abort
from app.decorators.access_controle import api
from app.services.framework.kafka_service import KafkaService
from app.services.project.project_service import ProjectService, ProjectRecordService
from app.services.project.project_participant_service import ProjectParticipantService
from app.services.project.sql_scripts_project_service import SQLScriptsProjectService
from app.services.app_branch_service import AppBranchService
from app.services.apprepo_service import ApprepoService
from app.util import Util
from app.services.framework.user_service import UserService
from app.services.flow.workflow import WorkflowService
from app.decorators.paginate import make_paging, make_paging_api_for_java
from app.mongodb import flow_data_collection
from app import app
import datetime

projectApiProfile = Blueprint('projectApiProfile', __name__)


@projectApiProfile.route("/<int:project_id>")
@api()
def query_project_by_id(project_id):
    # 根据id查询project信息,给zatest使用
    project = ProjectService.get_project(project_id)
    ret = dict()
    if project:
        ret['success'] = 1
        project_detail = project.serialize()
        project_detail['apps'] = AppBranchService.list_app_branch(str(project_id), ['app', 'module', 'open'])
        ret['data'] = project_detail
    else:
        ret['success'] = -1
    return jsonify(ret)


@projectApiProfile.route("/list", methods=['GET'])
@api()
@make_paging("projectList")
def list_project():
    # 根据用户名查询project List,对应分页
    # 查询publish_status = 0或者1
    user_name = request.values.get('user')
    name = request.values.get('name', None)
    user = UserService.get_user_by_name(user_name).first()
    if user:
        project = ProjectService.project_list(name=name, publish_status=[0, 1], begin_date_start=None,
                                              begin_date_end=None, publish_date_start=None, publish_date_end=None,
                                              participant_id=user.id, zatest_api=None)
    else:
        project = ProjectService.project_list(name=name, publish_status=[0, 1], begin_date_start=None,
                                              begin_date_end=None, publish_date_start=None, publish_date_end=None,
                                              participant_id=None, zatest_api=None)
    return project


# 对外查询
@projectApiProfile.route("/list.do", methods=['GET'])
@make_paging_api_for_java("resultList")
def list_project_api():
    # 根据用户名查询project List,对应分页
    # 查询publish_status = 0或者1
    user_name = request.values.get('user')
    name = request.values.get('projectName', None)
    dept_code = request.values.get("department")
    status = [0, 1, 2] if not request.values.get("status") else [int(request.values.get("status"))]
    begin_date_start = request.values.get("GmtModifiedStart")
    begin_date_end = request.values.get("GmtModifiedEnd")
    user = UserService.get_user_by_name(user_name).first()
    if user:
        project = ProjectService.project_list(name=name, publish_status=status, begin_date_start=begin_date_start,
                                              begin_date_end=begin_date_end, publish_date_start=None,
                                              publish_date_end=None,
                                              participant_id=user.id, dept_code=dept_code)
    else:
        project = ProjectService.project_list(name=name, publish_status=status, begin_date_start=None,
                                              begin_date_end=None, publish_date_start=None, publish_date_end=None,
                                              participant_id=None, dept_code=dept_code)
    return project


@projectApiProfile.route("/getProjectInfo", methods=['GET'])
def get_project_info():
    # 测试开发使用的接口
    # 该接口请数据格式以及字段请保留原样,参考如下：
    # http://10.253.22.207:8080/project/getProjectInfo.do?projectId=25695
    project_id = request.values.get('projectId')
    if not project_id:
        return jsonify({"success": 0, "data": u"project id can't null"})
    project = ProjectService.get_project(project_id)
    if project:
        project_info = project.brief()
        participants = ProjectParticipantService.query_participant(project_id)
        participant_list = list()
        for p in participants:
            participant_list.append(p.get("participant").get("name"))
        data = dict()
        data['department'] = project_info.get('dept_code')
        data['projectOwner'] = project_info.get('owner').get('real_name')
        sql_scripts_project = SQLScriptsProjectService.get_sql_scripts_project(project_id)
        if sql_scripts_project:
            data['sqlScriptUrl'] = sql_scripts_project.get('vcs_full_url')
        project_type = Util.change_project_type(project_info.get('type'))
        data['projectType'] = project_type
        data['expectPublishDate'] = project_info.get('expect_publish_date')
        data['projectId'] = project_id
        data['projectName'] = project_info.get('name')
        data['participants'] = list(set(participant_list))
        # codeModuleList
        code_module_list = list()
        branch_list = AppBranchService.list_app_branch(str(project_id), ['app', 'module', 'open'])
        for branch in branch_list:
            branch_dict = dict()
            app_name = branch.get('app_name')
            app = "{}/{}/{}".format(project_info.get('dept_code'), project_info.get('product_code'),
                                    branch.get('app_type'))
            order_no = branch.get('order')
            app_id = branch.get('app_id')
            repository = "{}/branch/{}".format(branch.get('vcs_full_url'), branch.get('branch'))
            app_type = Util.change_app_type(branch.get('app_type'))
            language = ''
            app_info = ApprepoService.get_app_info(app_id)
            if app_info:
                # apprepo http接口
                language = app_info.get('language')
            branch_dict['appName'] = app_name
            branch_dict['app'] = app
            branch_dict['order_no'] = order_no
            branch_dict['appId'] = app_id
            branch_dict['repository'] = repository
            branch_dict['appType'] = app_type
            branch_dict['language'] = language
            code_module_list.append(branch_dict)
        data['codeModuleList'] = code_module_list
        ret = dict()
        ret['success'] = 1
        ret['data'] = data
        return jsonify(ret)
    else:
        return jsonify({"success": 0, "data": u"no project is found by {}".format(project_id)})


@projectApiProfile.route("/getProjectTestInfo", methods=['POST'])
@api()
def get_project_test_info():
    # 获取前一天发布成功的5个配置部门的提测结果
    data = request.json
    begin_date = data.get('begin_date')
    end_date = data.get('end_date')
    workflow_data = WorkflowService.list('', list_all=True, order_by='modify_at', list_history=True, task_type=None,
                                         order_desc=None, begin_date=begin_date, end_date=end_date)
    workflow_data_list = [e.serialize() for e in workflow_data if e.current_task_type == 'prd_complete']
    ret = dict()
    ret['data'] = dict()
    for workflow_data in workflow_data_list:
        flow_id = workflow_data.get('id')
        project_id = flow_data_collection.find_one({'flow_id': flow_id}).get('data').get('project_id')
        project = ProjectService.get_project(int(project_id))
        if project_id not in ret['data'].keys() and project.dept_code in app.config['TEST_DEPT']:
            create_time = datetime.datetime.strftime(project.gmt_created, '%Y-%m-%d %H:%M:%S')
            owner = project.owner.real_name
            dept = project.dept_label
            total_test = ProjectRecordService.query_test_record_number(int(project_id), 'SUBMIT_TEST_VERIFY')
            total_test_reject = ProjectRecordService.query_test_record_number(int(project_id), 'TEST_REJECT')
            ret['data'][project_id] = {'department': dept, 'total_test': total_test,
                                       'total_test_reject': total_test_reject, 'owner': owner,
                                       'create_time': create_time}
    ret['result'] = 1
    return jsonify(ret)


@projectApiProfile.route('/check_regulator_info', methods=['POST'])
@api()
def check_regulator_info():
    regulator_id = request.json.get('regulator_id')
    ret = dict()
    if not regulator_id:
        ret['success'] = False
        ret['errorMsg'] = 'regulator_id is null'
        return jsonify(ret)
    project_id = ProjectService.query_project_by_regulator_id(regulator_id)
    ret['success'] = True
    ret['project_id'] = project_id
    return jsonify(ret)


@projectApiProfile.route('/sync_regulator_info', methods=['POST'])
@api()
def sync_regulator_info():
    regulator_id = request.json.get('regulator_id')
    ret = dict()
    if not regulator_id:
        ret['success'] = False
        ret['errorMsg'] = u'参数错误[regulator_id is null]'
        return jsonify(ret)
    project_name = request.json.get('name')
    summary = request.json.get('description')
    begin_date = request.json.get('start_date')
    creator_name = request.json.get('login_user')
    creator = UserService.get_user_by_name(creator_name).one_or_none()
    if creator:
        owner_id = creator.id
    else:
        ret['success'] = False
        ret['errorMsg'] = u'Duang系统中没有找到创建人信息，请联系core@zhongan.com进行检查'
        return jsonify(ret)
    project_id = ProjectService.add_project(name=project_name, project_type="system_fault", begin_date=begin_date,
                                            owner_id=owner_id, summary=summary, regulator_id=regulator_id)
    if project_id:
        ret = dict()
        data = KafkaService.assemble_jira_sync_duang_kafka_json(project_id, project_name, regulator_id=regulator_id)
        KafkaService.produce(data)
        ret['success'] = True
        ret['project_id'] = project_id
        return jsonify(ret)
    else:
        ret['success'] = False
        ret['errorMsg'] = u'创建项目失败，请稍后重试'
        return jsonify(ret)
