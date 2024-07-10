# -*- coding: utf8 -*-

from datetime import datetime
from pymongo import DESCENDING
from sqlalchemy import and_, desc, or_, union_all

from app.out.idb import iDB
from app.services.app_branch_service import AppBranchService
from app.services.apprepo_service import ApprepoService
from app.services.project.project_participant_service import ProjectParticipantService
from app.services.project.project_record_service import ProjectRecordService
from app.services.project.sql_scripts_project_service import SQLScriptsProjectService
from app.services.framework.kafka_service import KafkaService
from app.services.framework.recycle_service import RecycleService
from app.services.framework.message_service import MessageService
from app.services.operation.operation_service import OperationService
from app.services.diamond_service import DiamondService
from app.services.antx_service import AntxService
from app.models.Project import Project
from app.models.ProjectRecord import ProjectRecord
from app.models import db
from app.mongodb import app_branch_collection, project_test_collection, flow_data_collection, \
    operation_result_collection
from app.util import Util
from app import app, root_logger


class ProjectService(object):

    @staticmethod
    def apply_publish(project_id, precheck_data):
        project = Project.query.get(project_id)
        if not project:
            return False, None

        # 拼装数据
        app_list = AppBranchService.list_app_branch(project_id, ['app'])
        share_list = AppBranchService.list_app_branch(project_id, ['open', 'module'])
        dzbd_list = AppBranchService.list_app_branch(project_id, ['dzbd'])

        flow_data = {
            "project_id": project_id,
            "share_order": [e.get('app_id') for e in share_list],
            "app_order": [e.get('app_id') for e in app_list],
            "pre_sql_before_executed": False,
            "pre_sql_after_executed": False,
            "prd_sql_before_executed": False,
            "prd_sql_after_executed": False,
        }

        if precheck_data.get('sql_status'):
            for env, status in precheck_data.get('sql_status').items():
                if status == 'success':
                    if precheck_data.get('sql_execute_config').get(env).get('sql_before'):
                        flow_data[env + '_sql_before_executed'] = True
                    else:
                        flow_data[env + '_sql_after_executed'] = True

        if dzbd_list:
            dzbd = dzbd_list[0]
            dzbd_info = {
                "app_id": dzbd.get('app_id'),
                "branch_name": dzbd.get('branch'),
                "vcs_full_url": dzbd.get('vcs_full_url'),
                "branch_revision": 0
            }
            flow_data['dzbd'] = dzbd_info
        app_info = dict()
        for one_app in share_list:
            one_app_info = {
                "name": one_app.get('app_name'),
                "type": one_app.get('app_type'),
                "branch_name": one_app.get('branch'),
                "branch_revision": one_app.get('submit_test'),
                "fixed_pre_server": list(),
                "fixed_prd_server": list(),
                "pre_has_slb": False,
                "prd_has_slb": False,
                "commited": False,
            }
            app_info[str(one_app.get('app_id'))] = one_app_info
        for one_app in app_list:
            one_app_info = {
                "name": one_app.get('app_name'),
                "type": one_app.get('app_type'),
                "branch_name": one_app.get('branch'),
                "fixed_pre_server": list(),
                "fixed_prd_server": list(),
                "commited": False,
            }
            app_info[str(one_app.get('app_id'))] = one_app_info
        flow_data['app_info'] = app_info

        if precheck_data.get('scheduled_time'):
            precheck_data['scheduled_time'] = datetime.strptime(precheck_data['scheduled_time'], '%Y-%m-%d %H:%M')
        else:
            precheck_data['scheduled_time'] = None

        flow_data = Util.deep_update(flow_data, precheck_data)

        # 根据条件判断流程
        # 包含app，且所有的app的pre_server_amount都是0，就跳过预发
        flow_type = 'default'
        if precheck_data.get('app_info'):
            skip_pre = True
            has_app = False
            for one_app in precheck_data.get('app_info').values():
                if one_app.get('type') == 'app':
                    has_app = True
                    if one_app.get('pre_server_amount') is None or one_app.get('pre_server_amount') != 0:
                        skip_pre = False
                        break
            if has_app and skip_pre:
                flow_type = 'nopre'

        # 创建流程
        project.times += 1
        project.publish_status = 1
        flow_id = "{}{}".format(project_id, str(project.times).zfill(2))
        data = {'flow_id': flow_id, 'flow_type': flow_type, 'flow_data': flow_data}
        SQLScriptsProjectService.mod_sql_scripts_project(project_id, publish_id=flow_id)
        return True, data

    @staticmethod
    def approve_project(project_id, action, operator_id):
        # kafka 测试验证通过、测试验证不通过、code/sql review都通过时发送kafka消息
        try:
            project = Project.query.get(project_id)
            if project:
                datas = dict()
                datas['url'] = app.config.get('SERVER_URL') + '/project/detail/' + str(project.id)
                datas['project_id'] = str(project.id)
                datas['project_name'] = project.name
                if action == "project_submit":
                    # 提交review app_revision_dict为应用对应revision的字典
                    res, app_revision_dict = ProjectService.froze_version(project_id)
                    if res:
                        app_revision_str = ''
                        if app_revision_dict:
                            for app_name in app_revision_dict.keys():
                                app_revision_str += u"<div>应用名称: <b>{}</b> 提测版本号: <b>{}</b></div>".format(app_name,
                                                                                                          app_revision_dict.get(
                                                                                                              app_name))
                        project.code_review_status = 1
                        to_list = [p.participant for p in project.code_review_list]
                        MessageService.code_review(datas, to_list)
                        # 记录Record
                        record = ProjectRecord(project_id=project_id, operator_id=operator_id, role='owner',
                                               process='PROJECT_SUBMIT', action='OWNER_SUBMIT', remark=app_revision_str,
                                               gmt_modified=datetime.now())
                        db.session.add(record)
                        sql_scripts_project = SQLScriptsProjectService.get_sql_scripts_project(project_id)
                elif action == "project_rollback":
                    # 项目撤回
                    project.code_review_status = 0
                    project.test_status = 0
                    project.publish_status = 0
                    # 记录Record
                    record = ProjectRecord(project_id=project_id, operator_id=operator_id, role='owner',
                                           process='PROJECT_ROLLBACK', action='OWNER_ROLLBACK',
                                           gmt_modified=datetime.now())
                    db.session.add(record)
                    diamond_list = DiamondService.list_project_diamond(project_id)
                    antx_list = AntxService.list_project_antx(project_id)
                    for one in diamond_list:
                        DiamondService.mod_project_diamond(project_id, one.get('env'), one.get('data_id'),
                                                           review_status='init')
                    for one in antx_list:
                        AntxService.mod_project_antx(project_id, one.get('app_id'), one.get('env'),
                                                     review_status='init')
                elif action == "code_review_pass":
                    # code review通过
                    if project.code_review_status == 1:
                        project.code_review_status = 2
                        # 记录Record
                        record = ProjectRecord(project_id=project_id, operator_id=operator_id, role='code_review',
                                               process='CODE_REVIEW', action='CODE_REVIEW_PASS',
                                               gmt_modified=datetime.now())
                        db.session.add(record)
                        project.test_status = 1
                        to_list = [p.participant for p in project.qa_list]
                        MessageService.test_verify(datas, to_list)
                        record = ProjectRecord(project_id=project_id, operator_id='system', role='auto',
                                               process='TEST_VERIFY', action='SUBMIT_TEST_VERIFY',
                                               gmt_modified=datetime.now())
                        db.session.add(record)
                        data = KafkaService.assemble_kafka_json(project_id, 'prepare_test', env=None, publish_id=None)
                        KafkaService.produce(data)
                        root_logger.info(
                            "kafka project_id:{} action:prepare_test at {}".format(project_id, datetime.now()))
                    else:
                        return False, u'Code Review已审批，请勿重复审批。'
                elif action == "code_review_reject":
                    # code review不通过
                    if project.code_review_status == 1:
                        project.code_review_status = 0
                        project.test_status = 0
                        project.publish_status = 0
                        # 记录Record
                        record = ProjectRecord(project_id=project_id, operator_id=operator_id, role='code_review',
                                               process='CODE_REVIEW', action='CODE_REVIEW_REJECT',
                                               gmt_modified=datetime.now())
                        db.session.add(record)
                        diamond_list = DiamondService.list_project_diamond(project_id)
                        antx_list = AntxService.list_project_antx(project_id)
                        for one in diamond_list:
                            DiamondService.mod_project_diamond(project_id, one.get('env'), one.get('data_id'),
                                                               review_status='init')
                        for one in antx_list:
                            AntxService.mod_project_antx(project_id, one.get('app_id'), one.get('env'),
                                                         review_status='init')
                    else:
                        return False, u'Code Review已审批，请勿重复审批。'
                elif action == "test_verify_pass":
                    # 测试验证通过
                    if project.test_status == 1:
                        project.test_status = 2
                        to_list = [project.owner]
                        MessageService.apply_publish(datas, to_list)
                        data = KafkaService.assemble_kafka_json(project_id, action, env=None, publish_id=None)
                        KafkaService.produce(data)
                        root_logger.info(
                            "kafka project_id:{} action:test_verify_pass at {}".format(project_id, datetime.now()))
                        # 记录Record
                        record = ProjectRecord(project_id=project_id, operator_id=operator_id, role='qa',
                                               process='TEST_VERIFY', action='TEST_PASS', gmt_modified=datetime.now())
                        db.session.add(record)
                    else:
                        return False, u'测试验证已审批，请勿重复审批。'
                elif action == "test_verify_reject":
                    # 测试验证不通过
                    if project.test_status == 1:
                        project.code_review_status = 0
                        project.test_status = 0
                        project.publish_status = 0
                        data = KafkaService.assemble_kafka_json(project_id, action, env=None, publish_id=None)
                        KafkaService.produce(data)
                        root_logger.info(
                            "kafka project_id:{} action:test_verify_reject at {}".format(project_id, datetime.now()))
                        # 记录Record TEST_VERIFY:测试验证 TEST_REJECT:测试验证不通过
                        record = ProjectRecord(project_id=project_id, operator_id=operator_id, role='qa',
                                               process='TEST_VERIFY', action='TEST_REJECT', gmt_modified=datetime.now())
                        db.session.add(record)
                    else:
                        return False, u'测试验证已审批，请勿重复审批。'
                db.session.commit()
                return True, 'ok'
        except Exception, e:
            root_logger.exception("approve project exception: %s", e)

    @staticmethod
    def update_project(project_id, name=None, alias=None, project_type=None, company_id=None, company_code=None,
                       company_label=None, dept_id=None, dept_code=None, dept_label=None,
                       product_id=None, product_code=None, product_label=None, system_id=None, summary=None,
                       owner_id=None, ba_id=None, begin_date=None,
                       expect_publish_date=None, completed_date=None, sql_script_url=None,
                       jira_issue_id=None, jira_issue_key=None, jira_version_id=None):
        try:
            project = Project.query.get(project_id)
            if not project:
                return False
            flag = False
            if name:
                project.name = name
            if alias is not None:
                project.alias = alias
            if project_type:
                project.type = project_type
            if company_id:
                project.company_id = company_id
            if company_code:
                project.company_code = company_code
            if company_label:
                project.company_label = company_label
            if dept_id:
                project.dept_id = dept_id
            if dept_code:
                project.dept_code = dept_code
            if dept_label:
                project.dept_label = dept_label
            if product_id:
                project.product_id = product_id
            if product_code:
                project.product_code = product_code
            if product_label:
                project.product_label = product_label
            if system_id:
                project.system_id = system_id
            if summary is not None:
                project.summary = summary
            if owner_id:
                project.owner_id = owner_id
            if ba_id:
                project.ba_id = ba_id
            if begin_date:
                begin_date = datetime.strptime(begin_date, '%Y-%m-%d').date()
                project.begin_date = begin_date
            if expect_publish_date:
                if project.expect_publish_date != expect_publish_date:
                    flag = True
                expect_publish_date = datetime.strptime(expect_publish_date, '%Y-%m-%d').date()
                project.expect_publish_date = expect_publish_date
            if completed_date:
                completed_date = datetime.strptime(completed_date, '%Y-%m-%d').date()
                project.completed_date = completed_date
            if jira_issue_id:
                project.issue_id = jira_issue_id
            if jira_issue_key:
                project.issue_key = jira_issue_key
            if jira_version_id:
                project.jira_version_id = jira_version_id
            if sql_script_url is not None:
                project.sql_script_url = sql_script_url

            db.session.commit()
            return True, flag
        except Exception, e:
            root_logger.exception("project update error: %s ", e)
        return False, False

    @staticmethod
    def delete_project(project_id):
        try:
            p = Project.query.get(project_id)
            RecycleService.recycle(p)
            db.session.delete(p)
            db.session.commit()
            data = KafkaService.assemble_kafka_json(project_id, 'delete_project', env=None, publish_id=None)
            KafkaService.produce(data)
            root_logger.info("kafka project_id:{} delete_project at {}".format(project_id, datetime.now()))
            return True
        except Exception, e:
            root_logger.exception("project delete error: %s", e)

    @staticmethod
    def get_project(project_id):
        project = Project.query.get(project_id)
        return project

    @staticmethod
    def add_project(name=None, alias=None, project_type=None, company_id=None, dept_id=None, product_id=None,
                    system_id=None,
                    summary=None, owner_id=None, ba_id=None, begin_date=None, expect_publish_date=None,
                    completed_date=None, sql_script_url=None, jira_issue_id=None, jira_issue_key=None,
                    jira_version_id=None, jira_project_key=None, regulator_id=None):
        try:
            p = Project(name=name, alias=alias, type=project_type, company_id=company_id, dept_id=dept_id,
                        product_id=product_id, system_id=system_id, summary=summary, owner_id=owner_id, ba_id=ba_id,
                        begin_date=begin_date, expect_publish_date=expect_publish_date, completed_date=completed_date,
                        sql_script_url=sql_script_url, jira_issue_id=jira_issue_id, jira_issue_key=jira_issue_key,
                        jira_version_id=jira_version_id, jira_project_key=jira_project_key, regulator_id=regulator_id)
            db.session.add(p)
            db.session.commit()
            return p.id
        except Exception, e:
            root_logger.exception("project insert error: %s", e)

    @staticmethod
    def query_project_by_issue_info(issue_id, issue_key):
        # 根据issue_id issue_key查询project表,无记录则返回0
        p = Project.query.filter(Project.jira_issue_id == issue_id, Project.jira_issue_key == issue_key).first()
        if p:
            return p.id
        return 0

    @staticmethod
    def query_project_by_regulator_id(regulator_id):
        # 根据regulator_id查询project表,无记录则返回0
        p = Project.query.filter(Project.regulator_id == regulator_id).first()
        if p:
            return p.id
        return 0

    @staticmethod
    def query_project_by_version_info(version_id):
        # 根据issue_id issue_key查询project表,无记录则返回0
        p = Project.query.filter(Project.jira_version_id == version_id).first()
        if p:
            return p.id
        return 0

    @staticmethod
    def project_list(name, publish_status, begin_date_start, begin_date_end, publish_date_start, publish_date_end,
                     participant_id, zatest_api=None, department_id_list=None, dept_code=None):
        project1 = Project.query.filter(
            or_(
                Project.ba_id == participant_id,
                Project.owner_id == participant_id
            ) if participant_id else "",
            Project.name.like("%" + name + "%") if name else "",
            Project.publish_status.in_(publish_status) if publish_status else "",
            Project.publish_status.in_([0, 1]) if zatest_api else "",
            Project.begin_date >= begin_date_start if begin_date_start else "",
            Project.begin_date <= begin_date_end if begin_date_end else "",
            Project.expect_publish_date >= publish_date_start if publish_date_start else "",
            Project.expect_publish_date <= publish_date_end if publish_date_end else "",
            Project.dept_code == dept_code if dept_code else "",
            Project.is_deleted == "N",
            Project.dept_id.in_(department_id_list) if department_id_list else "",
        ).order_by(desc(Project.id))
        if participant_id:
            project_id_list = ProjectParticipantService.list_project_id_by_participant(participant_id)
            project_id_list = [e.project_id for e in project_id_list]
            project2 = Project.query.filter(
                Project.id.in_(project_id_list) if participant_id else "",
                Project.name.like("%" + name + "%") if name else "",
                Project.publish_status.in_(publish_status) if publish_status else "",
                Project.begin_date >= begin_date_start if begin_date_start else "",
                Project.begin_date <= begin_date_end if begin_date_end else "",
                Project.expect_publish_date >= publish_date_start if publish_date_start else "",
                Project.expect_publish_date <= publish_date_end if publish_date_end else "",
                Project.dept_code == dept_code if dept_code else "",
                Project.is_deleted == "N",
                Project.dept_id.in_(department_id_list) if department_id_list else "",
            ).order_by(desc(Project.id))
            projects = project1.union(project2)
            return projects
        else:
            return project1

    @staticmethod
    def list_project_by_privilege(name, publish_status, begin_date_start, begin_date_end, publish_date_start,
                                  publish_date_end, participant_id, privilege_list):
        ret = dict()
        projects = Project.query.filter(
            Project.owner_id == participant_id if participant_id else "",
            Project.name.like("%" + name + "%") if name else "",
            Project.publish_status.in_(publish_status) if publish_status else "",
            Project.begin_date >= begin_date_start if begin_date_start else "",
            Project.begin_date <= begin_date_end if begin_date_end else "",
            Project.expect_publish_date >= publish_date_start if publish_date_start else "",
            Project.expect_publish_date <= publish_date_end if publish_date_end else "",
            Project.is_deleted == "N"
        ).order_by(desc(Project.id))
        for one in projects:
            ret[one.id] = {'data': one.brief(), 'prvg': ['owner']}

        if participant_id and set(privilege_list) & {'dev', 'sqa', 'qa', 'code_review'}:
            participant_list = ProjectParticipantService.list_project_id_by_participant(participant_id,
                                                                                        privilege_list=privilege_list)
            prvg_project_id_dict = dict()
            for one in participant_list:
                if one.project_id not in prvg_project_id_dict:
                    prvg_project_id_dict[one.project_id] = list()
                prvg_project_id_dict[one.project_id].append(one.privilege_name)
            project_id_list = prvg_project_id_dict.keys()

            projects = Project.query.filter(
                Project.id.in_(project_id_list) if project_id_list else "",
                Project.name.like("%" + name + "%") if name else "",
                Project.publish_status.in_(publish_status) if publish_status else "",
                Project.begin_date >= begin_date_start if begin_date_start else "",
                Project.begin_date <= begin_date_end if begin_date_end else "",
                Project.expect_publish_date >= publish_date_start if publish_date_start else "",
                Project.expect_publish_date <= publish_date_end if publish_date_end else "",
                Project.is_deleted == "N"
            ).order_by(desc(Project.id))
            for one in projects:
                if ret.get(one.id):
                    prvg = prvg_project_id_dict.get(one.id)
                    prvg.append('owner')
                    ret[one.id] = {'data': one.brief(), 'prvg': prvg_project_id_dict.get(one.id)}
                else:
                    ret[one.id] = {'data': one.brief(), 'prvg': prvg_project_id_dict.get(one.id)}
        return ret

    @staticmethod
    def list_project_by_status(name, code_review_status, test_status, publish_status, begin_date_start, begin_date_end,
                               publish_date_start, publish_date_end):
        projects = Project.query.filter(
            Project.name.like("%" + name + "%") if name else "",
            Project.code_review_status.in_(code_review_status) if code_review_status else "",
            Project.test_status.in_(test_status) if test_status else "",
            Project.publish_status.in_(publish_status) if publish_status else "",
            Project.begin_date >= begin_date_start if begin_date_start else "",
            Project.begin_date <= begin_date_end if begin_date_end else "",
            Project.expect_publish_date >= publish_date_start if publish_date_start else "",
            Project.expect_publish_date <= publish_date_end if publish_date_end else "",
            Project.is_deleted == "N"
        ).order_by(desc(Project.id))
        return projects

    @staticmethod
    def froze_version(project_id):
        try:
            app_list = app_branch_collection.find({'project_id': project_id, "enabled": True})
            app_revision_dict = dict()
            for one_app in app_list:
                if one_app.get('vcs_type') == 'svn':
                    app_id = one_app.get('app_id')
                    branch_name = one_app.get('branch')
                    app_name = one_app.get('app_name')
                    revision = ApprepoService.get_current_revision_or_commit(app_id, branch_name=branch_name,
                                                                             directory='branch')
                    app_branch_collection.update_one({"project_id": project_id, "app_id": app_id, "enabled": True},
                                                     {"$set": {"submit_test": revision}})
                    app_revision_dict[app_name] = revision
            return True, app_revision_dict
        except Exception, e:
            root_logger.exception("froze version error: %s", e)
            return False, e.message

    @staticmethod
    def reset_project(project_id):
        try:
            project = Project.query.get(project_id)
            if not project:
                return False
            project.code_review_status = 0
            project.test_status = 0
            project.publish_status = 0
            db.session.commit()
        except Exception, e:
            root_logger.exception("project reset error: %s ", e)

    @staticmethod
    def complete_publish_project(project_id):
        try:
            project = Project.query.get(project_id)
            if not project:
                return False
            project.publish_status = 2
            db.session.commit()
        except Exception, e:
            root_logger.exception("project complete publish error: %s ", e)

    @staticmethod
    def get_test_details(project_id):
        test_details = project_test_collection.find_one({'project_id': project_id}, {'_id': 0})
        return test_details

    @staticmethod
    def add_test_details(project_id, request, api, smoke, keynote, test_file):
        try:
            test_details = {'project_id': project_id, 'request': request, 'api': api, 'smoke': smoke,
                            'keynote': keynote, 'test_file': test_file}
            if not ProjectService.get_test_details(project_id):
                project_test_collection.insert_one(test_details)
            else:
                project_test_collection.update_one({'project_id': project_id}, {'$set': test_details})
            return True
        except Exception, e:
            root_logger.exception("add_test_details error: %s", e)
            return False

    @staticmethod
    def update_test_details(project_id, request, api, smoke, keynote, test_file):
        try:
            test_details = {'project_id': project_id, 'request': request, 'api': api, 'smoke': smoke,
                            'keynote': keynote, 'test_file': test_file}
            if ProjectService.get_test_details(project_id):
                project_test_collection.update_one({'project_id': project_id}, {'$set': test_details})
            else:
                project_test_collection.insert_one(test_details)
            return True
        except Exception, e:
            root_logger.exception("update_test_details error: %s", e)
            return False

    @staticmethod
    def query_participant(project_id):
        project = Project.query.get(project_id)
        data = ProjectParticipantService.query_participant(project_id)
        data.append({
            'project_id': project_id,
            'participant_id': project.ba_id,
            'privilege_name': 'ba',
            'participant': project.ba.brief() if project.ba else {}
        })
        data.append({
            'project_id': project_id,
            'participant_id': project.owner_id,
            'privilege_name': 'owner',
            'participant': project.owner.brief() if project.owner else {}
        })
        return data

    @staticmethod
    def change_bad_man(record_id, flow_id, operator_id, reason, bad_man=None, rollback_type=None):
        remark = ""
        if rollback_type == 'pre_not_pass':
            remark = u"预发验证回退: <span>" + reason + u"</span>"
        elif rollback_type == 'local_not_pass':
            remark = u"项目owner自主回退: <span>" + reason + u"</span>"
        flow_data_collection.update_one({'flow': flow_id}, {'$set': {'data.bad_man': bad_man}})
        if bad_man:
            remark += u"<div>责任人: <a class='am-badge am-badge-danger' onclick='change_bad_man(this, \"{}\", \"{}\", \"{}\", \"{}\")'>{}</a></div>".format(
                flow_id, operator_id, reason, rollback_type, bad_man)
        return ProjectRecordService.mod_project_record(record_id, remark)

    @staticmethod
    def add_sql_review(project_id, env_execution_config, server_id):
        '''
        在应用仓库中创建上传目录
         '''
        msg = list()
        sql_scripts_project = SQLScriptsProjectService.get_sql_scripts_project(project_id, all=True)
        if not sql_scripts_project:
            sql_scripts_envs = env_execution_config.keys()
            svn_server_id = app.config.get('SVN_SQL_SERVER_ID').get(str(server_id))
            if not svn_server_id:
                svn_server_id = app.config.get('SVN_SQL_SERVER_ID').get('default')
            result, info = ApprepoService.create_sql_scripts_project(project_id, svn_server_id)
            if result:
                # 将该sql_review记录入库
                vcs_full_url = "https://svn.zhonganonline.com/repos/sql/duang/scripts/{}".format(project_id)
                revision_result = dict()
                for sql_scripts_env in sql_scripts_envs:
                    get_revision_result, revision = ApprepoService.get_sql_scripts_project_current_revision(info,
                                                                                                            sql_scripts_env)
                    if get_revision_result:
                        revision_result[sql_scripts_env] = revision
                    else:
                        revision_result[sql_scripts_env] = 0

                add_result, info = SQLScriptsProjectService.add_sql_scripts_project(project_id, info,
                                                                                    env_execution_config,
                                                                                    vcs_full_url, revision_result)
                if add_result:
                    return True, "ok"
                else:
                    msg.append(info)
                    return False, msg
            else:
                return False, msg.append(info)
        else:
            result = SQLScriptsProjectService.mod_sql_scripts_project(project_id,
                                                                      sql_execution_config=env_execution_config,
                                                                      enabled=True)
            if not result:
                msg.append(u"sql脚本项目信息更新失败")
                return False, msg
            else:
                return True, "ok"

    @staticmethod
    def get_sql_review(project_id):
        project = SQLScriptsProjectService.get_sql_scripts_project(project_id)
        if project:
            project["current_version"] = dict()
            svn_project_id = project["svn_project_id"]
            sql_execution_config = project["sql_execution_config"]

            for env in sql_execution_config.keys():
                result, info = ApprepoService.get_sql_scripts_project_current_revision(svn_project_id, env)
                if result:
                    project["current_version"][env] = info
                else:
                    project["current_version"][env] = 0
        return project

    @staticmethod
    def sql_review(project_id, operator_id, project_owner, dept_code, env_list=None, first_submit=False):
        project = SQLScriptsProjectService.get_sql_scripts_project(project_id)
        if project:
            svn_project_id = project.get("svn_project_id")
            publish_id = project.get("publish_id")
            msg = list()
            sql_scripts_version = dict()
            same_version = False
            submit_review_result = False
            for env in env_list:
                sql_scripts_version_result, info = ApprepoService.get_sql_scripts_project_current_revision(
                    svn_project_id, env)
                if sql_scripts_version_result:
                    if info > project["submited_test_version"][env]:
                        if first_submit and project["status"][env] == 'init' or not first_submit:
                            SQLScriptsProjectService.mod_sql_scripts_project(project_id, env=env,
                                                                             submited_test_version=info)
                            idb_result, info = iDB.apply_sql_review(project_id, project_owner, dept_code, env,
                                                                    project["vcs_full_url"] + "/" + env + "/", info)
                            if not idb_result:
                                msg.append(u"{}环境的sql脚本提交审核失败, {}".format(env, info))
                            else:
                                SQLScriptsProjectService.mod_sql_status(project_id, env, 'review',
                                                                        publish_id=publish_id,
                                                                        review_time=datetime.now(), manual=False)
                                msg.append(u"{}环境的sql脚本已提交审核。".format(env))
                    elif info == project["submited_test_version"][env]:
                        if not first_submit:
                            msg.append(u"提交审核失败，请确认{}环境的sql脚本已更新。".format(env))
                            return False, msg
                else:
                    if not first_submit:
                        msg.append(u"获取{}环境的sql脚本的当前版本失败，故无法提交SQL审核。".format(env))
                        return False, msg
            if len(msg):
                return True, msg
        return True, "ok"

    @staticmethod
    def update_sql_review_status(project_id, operator_id, env, status, remark=None, manual=None):
        project = SQLScriptsProjectService.get_sql_scripts_project(project_id)
        publish_id = project.get('publish_id')
        try:
            if project:
                if project.get('status').get(env) == 'review' or (
                        manual is not None and not manual and status == 'pass'):
                    if manual:
                        SQLScriptsProjectService.change_to_manual(project_id, env)
                    result = SQLScriptsProjectService.mod_sql_status(project_id, env, status, publish_id=publish_id)
                    if result:
                        if status == 'pass':
                            ProjectRecordService.add_project_record(project_id, operator_id, 'dba', 'SQL_REVIEW',
                                                                    'SQL_REVIEW_PASS',
                                                                    u'{}环境SQL Review 通过。'.format(env), datetime.now())
                        else:
                            if remark:
                                ProjectRecordService.add_project_record(project_id, operator_id, 'dba', 'SQL_REVIEW',
                                                                        'SQL_REVIEW_REJECT',
                                                                        u'{}环境SQL Review未通过， 原因：{}。'.format(env,
                                                                                                            remark),
                                                                        datetime.now())
                            else:
                                ProjectRecordService.add_project_record(project_id, operator_id, 'dba', 'SQL_REVIEW',
                                                                        'SQL_REVIEW_REJECT',
                                                                        u"{}环境SQL Review未通过， <a href='#' onclick=\"show_review_detail('{}', {})\">点击查看原因</a>。".format(
                                                                            env, project.get(
                                                                                'vcs_full_url') + '/' + env + '/',
                                                                            project.get('submited_test_version').get(
                                                                                env)), datetime.now())
                        return True, 'ok'
                elif manual is not None and not manual and status != 'pass':
                    return False, u'已经审核过的脚本只允许强制通过。'
                else:
                    return False, u'审核状态已经更新, 不允许重复更新, 请刷新页面显示最新状态。'
            return False, u'SQL项目已删除， 无法更新审核状态。'
        except Exception, e:
            root_logger.exception("update sql review status failed: %s", e)

    @staticmethod
    def update_sql_execute_status(project_id, operator_id, env, status, remark=None):
        project = SQLScriptsProjectService.get_sql_scripts_project(project_id)
        publish_id = project.get('publish_id')
        try:
            SQLScriptsProjectService.mod_sql_status(project_id, env, status, publish_id=publish_id)
            flow_data = flow_data_collection.find_one({'flow_id': publish_id})
            if flow_data.get('data').get('sql_execute_config').get(env).get('sql_before'):
                execute_time = 'sql_before'
            else:
                execute_time = 'sql_after'
            if status == 'success':
                flow_data_collection.update_one({'flow_id': publish_id},
                                                {'$set': {'data.{}_{}_executed'.format(env, execute_time): True}})
                ProjectRecordService.add_project_record(project_id, operator_id, 'dba', 'PUBLISH',
                                                        '{}_{}_EXECUTED'.format(env.upper(), execute_time.upper()),
                                                        None, datetime.now())
            else:
                opt_result = operation_result_collection.find(
                    {'flow_id': project.get('publish_id'), 'type': '{}_{}_execute'.format(env, execute_time)}).sort(
                    'finish_at', DESCENDING).limit(1)
                for opt in opt_result:
                    OperationService.mod_operation(opt.get('id'), 'fail')
                SQLScriptsProjectService.change_to_manual(project_id, env)
                datas = dict()
                datas['project_id'] = project_id
                datas['env'] = env
                datas['detail'] = '{}/publish/{}/detail'.format(app.config.get('SERVER_URL'), publish_id)
                datas['url'] = '{}/project/detail/{}'.format(app.config.get('SERVER_URL'), project.get("project_id"))
                project = Project.query.get(project_id)
                MessageService.sql_execute_failed(datas, {project.owner.real_name: project.owner.email,
                                                          'DBA': 'dba@zhongan.com'})
            return True
        except Exception, e:
            root_logger.exception("pre_sql_before_executed error: %s", e)
            return False
