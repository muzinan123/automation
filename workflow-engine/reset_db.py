# -*- coding: utf8 -*-

import datetime

from app.services.framework.role_service import RoleService
from app.services.framework.privilege_service import PrivilegeService
from app.services.framework.user_service import UserService
from app.services.framework.staff_sync import StaffSync
from app.models import db
from app.mongodb import flow_template_collection, flow_data_collection, operation_template_collection
from app.mongodb import result_detail_collection, diamond_collection, antx_base_collection, antx_project_collection
from app.mongodb import app_branch_collection, hot_pool_pre_server_collection, experienced_app_list_collection
from app.mongodb import operation_result_collection, publish_switch_collection, hot_pool_diamond_collection
from app.mongodb import hot_pool_prd_app_collection, notice_system_collection
from app.mongodb import product_publish_statistics_collection, publish_abandon_statistics_collection
from app.mongodb import project_publish_statistics_collection, ci_project_collection
from app.mongodb import maven_dependency_preallocation_collection, aut_ci_project_collection
from app.mongodb import sql_scripts_project_collection


def create_table_mysql():
    db.create_all(bind=['main'])


def reset_role_and_privilege():

    RoleService.add_role('duang_admin', u'管理员')
    RoleService.add_role('user', u'默认用户')
    RoleService.add_role('pe', u'PE')
    RoleService.add_role('dba', u'DBA')
    RoleService.add_role('monitor', u'应用监控')
    RoleService.add_role('dev', u'开发')
    RoleService.add_role('qa', u'测试')
    RoleService.add_role('ba', u'需求')
    RoleService.add_role('code_review', u'代码评审')

    PrivilegeService.add_privilege('dev', u'开发')
    PrivilegeService.add_privilege('qa', u'测试')
    PrivilegeService.add_privilege('ba', u'需求')
    PrivilegeService.add_privilege('code_review', u'代码评审')
    PrivilegeService.add_privilege('dba', u'数据库管理员')
    PrivilegeService.add_privilege('pe', u'应用运维')
    PrivilegeService.add_privilege('monitor', u'应用监控')
    PrivilegeService.add_privilege('duang_admin', u'管理员')

    PrivilegeService.link_role_privilege(1, 1, True, True)
    PrivilegeService.link_role_privilege(1, 2, True, True)
    PrivilegeService.link_role_privilege(1, 3, True, True)
    PrivilegeService.link_role_privilege(1, 4, True, True)
    PrivilegeService.link_role_privilege(1, 5, False, False)
    PrivilegeService.link_role_privilege(1, 6, True, False)
    PrivilegeService.link_role_privilege(1, 7, False, False)
    PrivilegeService.link_role_privilege(1, 8, True, True)

    PrivilegeService.link_role_privilege(3, 6, True, True)
    PrivilegeService.link_role_privilege(4, 5, True, True)
    PrivilegeService.link_role_privilege(5, 7, True, True)

    PrivilegeService.link_role_privilege(6, 1, True, True)
    PrivilegeService.link_role_privilege(7, 2, True, True)
    PrivilegeService.link_role_privilege(8, 3, True, True)
    PrivilegeService.link_role_privilege(9, 4, True, True)


def sync_staff():
    StaffSync.sync_department()
    StaffSync.sync_user()
    UserService.add_sso_user("system", "devops@zhongan.com", u"系统用户", 'system', None, "运维开发组", None)
    RoleService.link_user_role('wz000850', 1)


def add_index_mongodb():
    flow_template_collection.ensure_index([('type', 1), ('key', 1)], unique=True)

    flow_data_collection.ensure_index([('flow_id', 1)], unique=True)

    operation_template_collection.ensure_index([('type', 1), ('name', 1)], unique=True)

    result_detail_collection.ensure_index([('opid', 1), ('step', 1)], unique=True)

    antx_base_collection.ensure_index([('env', 1), ('app_id', 1)], unique=True)

    antx_project_collection.ensure_index([('project_id', 1), ('env', 1), ('app_id', 1)], unique=True)

    diamond_collection.ensure_index([('project_id', 1), ('env', 1), ('data_id', 1)], unique=True)

    app_branch_collection.ensure_index([('project_id', 1), ('app_id', 1), ('version', 1)], unique=True)

    hot_pool_pre_server_collection.ensure_index([('res_id', 1), ('port', 1), ('publish_id', 1)], unique=True)

    experienced_app_list_collection.ensure_index([('app_id', 1)], unique=True)

    operation_result_collection.ensure_index([('id', 1)], unique=True)

    operation_result_collection.ensure_index([('flow_id', 1)])

    hot_pool_diamond_collection.ensure_index([('data_id', 1), ('env', 1)], unique=True)

    hot_pool_prd_app_collection.ensure_index([('app_id', 1), ('publish_id', 1)], unique=True)

    product_publish_statistics_collection.ensure_index([('date', 1)])

    project_publish_statistics_collection.ensure_index([('date', 1)])

    publish_abandon_statistics_collection.ensure_index([('date', 1)])

    ci_project_collection.ensure_index([('app_id', 1), ('branch', 1)], unique=True)

    aut_ci_project_collection.ensure_index([('app_id', 1), ('branch', 1)], unique=True)

    maven_dependency_preallocation_collection.ensure_index([('artifact_id', 1), ('sub_version', 1)], unique=True)

    sql_scripts_project_collection.ensure_index([('project_id', 1)], unique=True)


def reset_flow_template():

    flow_template_collection.delete_many({})

    nopre_local_wait_check = {'order': 0, 'type': 'nopre', 'key': 'local_wait_check', 'name': u'待确认', 'env': 'local', 'directions': {'local_pass': {'name': u'准备至生产', 'go': 'local_committing', 'prvg': ['qa', 'sqa', 'pe']}, 'local_not_pass': {'name': u'Owner回退', 'go': 'abandon', 'prvg': ['owner', 'pe'], 'action': 'local_not_pass'}}, 'trigger_type': 'auto_local'}
    nopre_local_commit_error = {'order': 1, 'type': 'nopre', 'key': 'local_commit_error', 'name': u'让步等待', 'env': 'local', 'directions': {'local_not_pass': {'name': u'Owner回退', 'go': 'abandon', 'prvg': ['owner', 'pe'], 'action': 'local_not_pass'}, 'local_pass': {'name': u'准备至生产', 'go': 'local_committing', 'prvg': ['qa', 'sqa', 'pe']}}, 'operation_type': 'pre_commit_error'}
    nopre_abandon = {'order': 2, 'type': 'nopre', 'key': 'abandon', 'name': u'废弃', 'env': 'local', 'trigger_type': 'abandon'}
    nopre_local_committing = {'order': 3, 'type': 'nopre', 'key': 'local_committing', 'name': u'生产前预检', 'env': 'local', 'directions': {'success': {'name': u'success', 'go': 'prd_sql_before'}, 'failed': {'name': u'failed', 'go': 'local_commit_error'}}, 'operation_type': 'local_commit'}

    nopre_prd_sql_before = {'order': 4, 'type': 'nopre', 'key': 'prd_sql_before', 'name': u'发布前执行SQL', 'env': 'prd', 'directions': {'sql_executed': {'name': u'SQL已执行', 'go': 'prd_wait_build', 'prvg': ['dba'], 'action': 'prd_sql_before_executed'}, 'sql_execute': {'name': u'执行SQL', 'go': 'prd_sql_before', 'prvg': ['dba', 'owner'], 'action': 'prd_sql'}, 'success': {'name': u'success', 'go': 'prd_wait_build'}, 'idb_success': {'name': u'idb_success', 'go': 'prd_sql_before_executing'}, 'failed': {'name': u'failed', 'go': 'prd_sql_before'}, 'skip': {'name': u'skip', 'go': 'prd_wait_build'}, 'cancel_sql':{'name': u'取消执行SQL', 'go': 'prd_wait_build', 'prvg': ['dba', 'owner']}}, 'trigger_type': 'prd_sql_before', 'operation_type': 'prd_sql_before'}
    nopre_prd_sql_before_executing = {'order': 5, 'type': 'nopre', 'key': 'prd_sql_before_executing', 'name': u'正在执行SQL', 'env': 'prd', 'directions': {'success': {'name': u'success', 'go': 'prd_wait_build'}, 'failed': {'name': u'failed', 'go': 'prd_sql_before'}, 'timeout': {'name': u'timeout', 'go': 'prd_sql_before'}}}

    nopre_prd_wait_build = {'order': 6, 'type': 'nopre', 'key': 'prd_wait_build', 'name': u'待PE打包', 'env': 'prd', 'directions': {'prd_build': {'name': u'打包', 'go': 'prd_building', 'prvg': ['pe', 'sqa'], 'action': 'prd_build'}}, 'trigger_type': 'prd_wait_build'}
    nopre_prd_building = {'order': 7, 'type': 'nopre', 'key': 'prd_building', 'name': u'正在打包', 'env': 'prd', 'directions': {'success': {'name': u'success', 'go': 'prd_wait_publish'}, 'failed': {'name': u'failed', 'go': 'prd_error'}}, 'operation_type': 'prd_build'}
    nopre_prd_wait_publish = {'order': 8, 'type': 'nopre', 'key': 'prd_wait_publish', 'name': u'待PE发布', 'env': 'prd', 'directions': {'prd_publish': {'name': u'发布', 'go': 'prd_publishing', 'prvg': ['pe', 'sqa']}, 'prd_rebuild': {'name': u'重新打包', 'go': 'prd_wait_build', 'prvg': ['pe', 'sqa'], 'action': 'prd_rebuild'}}}
    nopre_prd_publishing = {'order': 9, 'type': 'nopre', 'key': 'prd_publishing', 'name': u'发布中', 'env': 'prd', 'directions': {'success': {'name': u'success', 'go': 'prd_sql_after'}, 'failed': {'name': u'failed', 'go': 'prd_error'}}, 'operation_type': 'prd_publish'}
    nopre_prd_sql_after = {'order': 10, 'type': 'nopre', 'key': 'prd_sql_after', 'name': u'发布后执行SQL', 'env': 'prd', 'directions': {'sql_executed': {'name': u'SQL已执行', 'go': 'prd_committing', 'prvg': ['dba'], 'action': 'prd_sql_after_executed'}, 'sql_execute': {'name': u'执行SQL', 'go': 'prd_sql_after', 'prvg': ['dba', 'owner'], 'action': 'prd_sql'}, 'success': {'name': u'success', 'go': 'prd_committing'}, 'idb_success': {'name': u'idb_success', 'go': 'prd_sql_after_executing'},  'failed': {'name': u'failed', 'go': 'prd_sql_after'}, 'skip': {'name': u'skip', 'go': 'prd_committing'}, 'cancel_sql':{'name': u'取消执行SQL', 'go': 'prd_committing', 'prvg': ['dba', 'owner']}}, 'trigger_type': 'prd_sql_after', 'operation_type': 'prd_sql_after'}
    nopre_prd_sql_after_executing = {'order': 11, 'type': 'nopre', 'key': 'prd_sql_after_executing', 'name': u'正在执行SQL', 'env': 'prd', 'directions': {'success': {'name': u'success', 'go': 'prd_committing'}, 'failed': {'name': u'failed', 'go': 'prd_sql_after'}, 'timeout': {'name': u'timeout', 'go': 'prd_sql_after'}}}

    nopre_prd_committing = {'order': 12, 'type': 'nopre', 'key': 'prd_committing', 'name': u'代码提交中', 'env': 'prd', 'directions': {'success': {'name': u'success', 'go': 'prd_complete'}, 'failed': {'name': u'failed', 'go': 'prd_error'}}, 'operation_type': 'prd_commit'}
    nopre_prd_error = {'order': 13, 'type': 'nopre', 'key': 'prd_error', 'name': u'出错', 'env': 'prd', 'directions': {'prd_rebuild': {'name': u'重新打包', 'go': 'prd_building', 'prvg': ['pe', 'sqa']}, 'prd_republish': {'name': u'重新发布', 'go': 'prd_publishing', 'prvg': ['pe', 'sqa']}}}
    nopre_prd_complete = {'order': 14, 'type': 'nopre', 'key': 'prd_complete', 'name': u'完成', 'env': 'prd', 'trigger_type': 'prd_complete'}

    flow_template_collection.insert_one(nopre_local_wait_check)
    flow_template_collection.insert_one(nopre_local_commit_error)
    flow_template_collection.insert_one(nopre_abandon)
    flow_template_collection.insert_one(nopre_local_committing)

    flow_template_collection.insert_one(nopre_prd_sql_before)
    flow_template_collection.insert_one(nopre_prd_sql_before_executing)
    flow_template_collection.insert_one(nopre_prd_wait_build)
    flow_template_collection.insert_one(nopre_prd_building)
    flow_template_collection.insert_one(nopre_prd_wait_publish)
    flow_template_collection.insert_one(nopre_prd_publishing)
    flow_template_collection.insert_one(nopre_prd_sql_after)
    flow_template_collection.insert_one(nopre_prd_sql_after_executing)
    flow_template_collection.insert_one(nopre_prd_committing)
    flow_template_collection.insert_one(nopre_prd_error)
    flow_template_collection.insert_one(nopre_prd_complete)

    local_wait_check = {'order': 0, 'type': 'default', 'key': 'local_wait_check', 'name': u'待确认', 'env': 'local', 'directions': {'local_pass': {'name': u'准备至预发', 'go': 'local_committing', 'prvg': ['qa', 'sqa', 'pe']}, 'local_not_pass': {'name': u'Owner回退', 'go': 'abandon', 'prvg': ['owner'], 'action': 'local_not_pass'}}, 'trigger_type': 'auto_local'}
    local_commit_error = {'order': 1, 'type': 'default', 'key': 'local_commit_error', 'name': u'让步等待', 'env': 'local', 'directions': {'local_not_pass': {'name': u'Owner回退', 'go': 'abandon', 'prvg': ['owner'], 'action': 'local_not_pass'}, 'local_pass': {'name': u'准备至预发', 'go': 'local_committing', 'prvg': ['qa', 'sqa', 'pe']}}, 'operation_type': 'local_commit_error'}
    abandon = {'order': 2, 'type': 'default', 'key': 'abandon', 'name': u'废弃', 'env': 'local', 'trigger_type': 'abandon', 'operation_type': 'local_commit_error'}
    local_committing = {'order': 3, 'type': 'default', 'key': 'local_committing', 'name': u'预发前预检', 'env': 'local', 'directions': {'success': {'name': u'success', 'go': 'pre_sql_before'}, 'failed': {'name': u'failed', 'go': 'local_commit_error'}}, 'operation_type': 'local_commit'}
    pre_sql_before = {'order': 4, 'type': 'default', 'key': 'pre_sql_before', 'name': u'发布前执行SQL', 'env': 'pre', 'directions': {'sql_executed': {'name': u'SQL已执行', 'go': 'pre_wait_build', 'prvg': ['dba'], 'action': 'pre_sql_before_executed'}, 'sql_execute': {'name': u'执行SQL', 'go': 'pre_sql_before', 'prvg': ['dba', 'owner'], 'action': 'pre_sql'}, 'success': {'name': u'success', 'go': 'pre_wait_build'}, 'idb_success': {'name': u'idb_success', 'go': 'pre_sql_before_executing'}, 'failed': {'name': u'failed', 'go': 'pre_sql_before'}, 'skip': {'name': u'skip', 'go': 'pre_wait_build'}, 'cancel_sql':{'name': u'取消执行SQL', 'go': 'pre_wait_build', 'prvg': ['dba', 'owner']}}, 'operation_type': 'pre_sql_before', 'trigger_type': 'pre_sql_before'}
    pre_sql_before_executing = {'order': 5, 'type': 'default', 'key': 'pre_sql_before_executing', 'name': u'正在执行SQL', 'env': 'pre', 'directions':{'success': {'name': u'success', 'go': 'pre_wait_build'}, 'failed': {'name': u'failed', 'go': 'pre_sql_before'}, 'timeout': {'name': u'timeout', 'go': 'pre_sql_before'}}}

    pre_wait_build = {'order': 6, 'type': 'default', 'key': 'pre_wait_build', 'name': u'待PE打包', 'env': 'pre', 'directions': {'pre_build': {'name': u'打包', 'go': 'pre_building', 'prvg': ['pe', 'sqa']}}, 'trigger_type': 'auto_pre_build'}
    pre_building = {'order': 7, 'type': 'default', 'key': 'pre_building', 'name': u'正在打包', 'env': 'pre', 'directions': {'success': {'name': u'success', 'go': 'pre_wait_publish'}, 'failed': {'name': u'failed', 'go': 'pre_error'}}, 'operation_type': 'pre_build'}
    pre_wait_publish = {'order': 8, 'type': 'default', 'key': 'pre_wait_publish', 'name': u'待PE发布', 'env': 'pre', 'directions': {'pre_publish': {'name': u'发布', 'go': 'pre_publishing', 'prvg': ['pe', 'sqa']}}, 'trigger_type': 'auto_pre_publish'}
    pre_publishing = {'order': 9, 'type': 'default', 'key': 'pre_publishing', 'name': u'发布中', 'env': 'pre', 'directions': {'success': {'name': u'success', 'go': 'pre_sql_after'}, 'failed': {'name': u'failed', 'go': 'pre_error'}}, 'operation_type': 'pre_publish'}
    pre_sql_after = {'order': 10, 'type': 'default', 'key': 'pre_sql_after', 'name': u'发布后执行SQL', 'env': 'pre', 'directions': {'sql_executed': {'name': u'SQL已执行', 'go': 'pre_wait_check', 'prvg': ['dba'], 'action': 'pre_sql_after_executed'}, 'sql_execute': {'name': u'执行SQL', 'go': 'pre_sql_after', 'prvg': ['dba', 'owner'], 'action': 'pre_sql'}, 'success': {'name': u'success', 'go': 'pre_wait_check'}, 'idb_success': {'name': u'idb_success', 'go': 'pre_sql_after_executing'}, 'failed': {'name': u'failed', 'go': 'pre_sql_after'}, 'skip': {'name': u'skip', 'go': 'pre_wait_check'}, 'cancel_sql':{'name': u'取消执行SQL', 'go': 'pre_wait_check', 'prvg': ['dba', 'owner']}}, 'trigger_type': 'pre_sql_after', 'operation_type': 'pre_sql_after'}
    pre_sql_after_executing = {'order': 11, 'type': 'default', 'key': 'pre_sql_after_executing', 'name': u'正在执行SQL', 'env': 'pre', 'directions': {'success': {'name': u'success', 'go': 'pre_wait_check'}, 'failed': {'name': u'failed', 'go': 'pre_sql_after'}, 'timeout': {'name': u'timeout', 'go': 'pre_sql_after'}}}

    pre_wait_check = {'order': 12, 'type': 'default', 'key': 'pre_wait_check', 'name': u'待测试验证', 'env': 'pre', 'directions': {'pre_pass': {'name': u'发布至生产', 'go': 'pre_monitor_check', 'prvg': ['qa', 'sqa'], 'action': 'pre_pass'}, 'pre_not_pass': {'name': u'验证回退', 'go': 'abandon', 'prvg': ['qa', 'sqa'], 'action': 'pre_not_pass'}, 'pre_roll_back': {'name': u'让步回退', 'go': 'local_commit_error', 'prvg': ['qa', 'sqa'], 'action': 'pre_roll_back'}}}
    pre_monitor_check = {'order': 13, 'type': 'default', 'key': 'pre_monitor_check', 'name': u'应用监控验证', 'env': 'pre', 'directions': {'pre_pass': {'name': u'发布至生产', 'go': 'pre_committing', 'prvg': ['monitor']}, 'pre_not_pass': {'name': u'验证回退', 'go': 'abandon', 'prvg': ['monitor'], 'action': 'pre_not_pass'}}, 'trigger_type': 'check_new'}
    pre_error = {'order': 14, 'type': 'default', 'key': 'pre_error', 'name': u'出错', 'env': 'pre', 'directions': {'pre_rebuild': {'name': u'重新打包', 'go': 'pre_building', 'prvg': ['pe', 'sqa']}, 'pre_republish': {'name': u'重新发布', 'go': 'pre_publishing', 'prvg': ['pe', 'sqa']}, 'pre_not_pass': {'name': u'验证回退', 'go': 'abandon', 'prvg': ['pe', 'sqa'], 'action': 'pre_not_pass'}, 'local_not_pass': {'name': u'Owner回退', 'go': 'abandon', 'prvg': ['owner'], 'action': 'local_not_pass'}}}
    pre_committing = {'order': 15, 'type': 'default', 'key': 'pre_committing', 'name': u'生产前预检', 'env': 'pre', 'directions': {'success': {'name': u'success', 'go': 'prd_sql_before'}, 'failed': {'name': u'failed', 'go': 'pre_commit_error'}}, 'operation_type': 'pre_commit'}
    pre_commit_error = {'order': 16, 'type': 'default', 'key': 'pre_commit_error', 'name': u'出错', 'env': 'pre', 'directions': {'pre_rebuild': {'name': u'重新打包', 'go': 'pre_building', 'prvg': ['pe', 'sqa']}, 'pre_republish': {'name': u'重新发布', 'go': 'pre_publishing', 'prvg': ['pe', 'sqa']}, 'pre_recheck': {'name': u'重新预检', 'go': 'pre_committing', 'prvg': ['pe', 'sqa']}, 'pre_not_pass': {'name': u'验证回退', 'go': 'abandon', 'prvg': ['pe', 'sqa'], 'action': 'pre_not_pass'}, 'local_not_pass': {'name': u'Owner回退', 'go': 'abandon', 'prvg': ['owner'], 'action': 'local_not_pass'}}, 'operation_type': 'pre_commit_error'}

    prd_sql_before = {'order': 17, 'type': 'default', 'key': 'prd_sql_before', 'name': u'发布前执行SQL', 'env': 'prd', 'directions': {'sql_executed': {'name': u'SQL已执行', 'go': 'prd_wait_build', 'prvg': ['dba'], 'action': 'prd_sql_before_executed'}, 'sql_execute': {'name': u'执行SQL', 'go': 'prd_sql_before', 'prvg': ['dba', 'owner'], 'action': 'prd_sql'}, 'success': {'name': u'success', 'go': 'prd_wait_build'}, 'idb_success': {'name': u'idb_success', 'go': 'prd_sql_before_executing'}, 'failed': {'name': u'failed', 'go': 'prd_sql_before'}, 'skip': {'name': u'skip', 'go': 'prd_wait_build'}, 'cancel_sql':{'name': u'取消执行SQL', 'go': 'prd_wait_build', 'prvg': ['dba', 'owner']}}, 'trigger_type': 'prd_sql_before', 'operation_type': 'prd_sql_before'}
    prd_sql_before_executing = {'order': 18, 'type': 'default', 'key': 'prd_sql_before_executing', 'name': u'正在执行SQL', 'env': 'prd', 'directions': {'success': {'name': u'success', 'go': 'prd_wait_build'}, 'failed': {'name': u'failed', 'go': 'prd_sql_before'}, 'timeout': {'name': u'timeout', 'go': 'prd_sql_before'}}}

    prd_wait_build = {'order': 19, 'type': 'default', 'key': 'prd_wait_build', 'name': u'待PE打包', 'env': 'prd', 'directions': {'prd_build': {'name': u'打包', 'go': 'prd_building', 'prvg': ['pe', 'sqa'], 'action': 'prd_build'}}, 'trigger_type': 'prd_wait_build'}
    prd_building = {'order': 20, 'type': 'default', 'key': 'prd_building', 'name': u'正在打包', 'env': 'prd', 'directions': {'success': {'name': u'success', 'go': 'prd_wait_publish'}, 'failed': {'name': u'failed', 'go': 'prd_error'}}, 'operation_type': 'prd_build'}
    prd_wait_publish = {'order': 21, 'type': 'default', 'key': 'prd_wait_publish', 'name': u'待PE发布', 'env': 'prd', 'directions': {'prd_publish': {'name': u'发布', 'go': 'prd_publishing', 'prvg': ['pe', 'sqa']}, 'prd_rebuild': {'name': u'重新打包', 'go': 'prd_wait_build', 'prvg': ['pe', 'sqa'], 'action': 'prd_rebuild'}}}
    prd_publishing = {'order': 22, 'type': 'default', 'key': 'prd_publishing', 'name': u'发布中', 'env': 'prd', 'directions': {'success': {'name': u'success', 'go': 'prd_sql_after'}, 'failed': {'name': u'failed', 'go': 'prd_error'}}, 'operation_type': 'prd_publish'}
    prd_sql_after = {'order': 23, 'type': 'default', 'key': 'prd_sql_after', 'name': u'发布后执行SQL', 'env': 'prd', 'directions': {'sql_executed': {'name': u'SQL已执行', 'go': 'prd_committing', 'prvg': ['dba'], 'action': 'prd_sql_after_executed'}, 'sql_execute': {'name': u'执行SQL', 'go': 'prd_sql_after', 'prvg': ['dba', 'owner'], 'action': 'prd_sql'}, 'success': {'name': u'success', 'go': 'prd_committing'}, 'idb_success': {'name': u'idb_success', 'go': 'prd_sql_after_executing'},  'failed': {'name': u'failed', 'go': 'prd_sql_after'}, 'skip': {'name': u'skip', 'go': 'prd_committing'}, 'cancel_sql':{'name': u'取消执行SQL', 'go': 'prd_committing', 'prvg': ['dba', 'owner']}}, 'trigger_type': 'prd_sql_after', 'operation_type': 'prd_sql_after'}
    prd_sql_after_executing = {'order': 24, 'type': 'default', 'key': 'prd_sql_after_executing', 'name': u'正在执行SQL', 'env': 'prd', 'directions': {'success': {'name': u'success', 'go': 'prd_committing'}, 'failed': {'name': u'failed', 'go': 'prd_sql_after'}, 'timeout': {'name': u'timeout', 'go': 'prd_sql_after'}}}

    prd_committing = {'order': 25, 'type': 'default', 'key': 'prd_committing', 'name': u'代码提交中', 'env': 'prd', 'directions': {'success': {'name': u'success', 'go': 'prd_complete'}, 'failed': {'name': u'failed', 'go': 'prd_error'}}, 'operation_type': 'prd_commit'}
    prd_error = {'order': 26, 'type': 'default', 'key': 'prd_error', 'name': u'出错', 'env': 'prd', 'directions': {'prd_rebuild': {'name': u'重新打包', 'go': 'prd_building', 'prvg': ['pe', 'sqa']}, 'prd_republish': {'name': u'重新发布', 'go': 'prd_publishing', 'prvg': ['pe', 'sqa']}}}
    prd_complete = {'order': 27, 'type': 'default', 'key': 'prd_complete', 'name': u'完成', 'env': 'prd', 'trigger_type': 'prd_complete'}

    flow_template_collection.insert_one(local_wait_check)
    flow_template_collection.insert_one(local_commit_error)
    flow_template_collection.insert_one(abandon)
    flow_template_collection.insert_one(local_committing)

    flow_template_collection.insert_one(pre_sql_before)
    flow_template_collection.insert_one(pre_sql_before_executing)
    flow_template_collection.insert_one(pre_wait_build)
    flow_template_collection.insert_one(pre_building)
    flow_template_collection.insert_one(pre_wait_publish)
    flow_template_collection.insert_one(pre_publishing)
    flow_template_collection.insert_one(pre_sql_after)
    flow_template_collection.insert_one(pre_sql_after_executing)

    flow_template_collection.insert_one(pre_wait_check)
    flow_template_collection.insert_one(pre_monitor_check)
    flow_template_collection.insert_one(pre_error)
    flow_template_collection.insert_one(pre_committing)
    flow_template_collection.insert_one(pre_commit_error)

    flow_template_collection.insert_one(prd_sql_before)
    flow_template_collection.insert_one(prd_sql_before_executing)
    flow_template_collection.insert_one(prd_wait_build)
    flow_template_collection.insert_one(prd_building)
    flow_template_collection.insert_one(prd_wait_publish)
    flow_template_collection.insert_one(prd_publishing)
    flow_template_collection.insert_one(prd_sql_after)
    flow_template_collection.insert_one(prd_sql_after_executing)

    flow_template_collection.insert_one(prd_committing)
    flow_template_collection.insert_one(prd_error)
    flow_template_collection.insert_one(prd_complete)


def reset_operation_template():
    operation_template_collection.delete_many({})

    one = {'type': 'restart_java_app', 'name': 'hsf_offline', 'desc': u'HSF下线', 'func': 'hsf_offline', 'order': 0, 'progress': 25}
    operation_template_collection.insert_one(one)
    one = {'type': 'restart_java_app', 'name': 'salt', 'desc': u'调用Salt重启', 'func': 'salt_restart_app', 'order': 1, 'progress': 25}
    operation_template_collection.insert_one(one)
    one = {'type': 'restart_java_app', 'name': 'health_check', 'desc': u'健康监测', 'func': 'health_check', 'order': 2, 'progress': 25}
    operation_template_collection.insert_one(one)
    one = {'type': 'restart_java_app', 'name': 'hsf_online', 'desc': u'HSF上线', 'func': 'hsf_online', 'order': 3, 'progress': 25}
    operation_template_collection.insert_one(one)

    one = {'type': 'pre_build', 'name': 'cp_tag_release', 'desc': u'从Tag拉取Release分支', 'func': 'cp_tag_release', 'order': 0, 'progress': 20}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_build', 'name': 'merge_branch_release', 'desc': u'合并Branch分支到Release分支', 'func': 'merge_branch_release', 'order': 1,'progress': 20}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_build', 'name': 'pre_share_allocate', 'desc': u'预发本地Share版本准备', 'func': 'pre_share_allocate', 'order': 2, 'progress': 20}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_build', 'name': 'build_pre', 'desc': u'预发环境打包Release分支', 'func': 'build_release', 'order': 3, 'progress': 20}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_build', 'name': 'build_aut', 'desc': u'自动化测试环境打包Release分支', 'func': 'build_release', 'order': 4, 'progress': 20}
    operation_template_collection.insert_one(one)

    one = {'type': 'prd_build', 'name': 'cp_trunk_release', 'desc': u'从Trunk拉取Release分支', 'func': 'cp_trunk_release', 'order': 0, 'progress': 15}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_build', 'name': 'merge_tag_release', 'desc': u'合并Tag分支到Release分支', 'func': 'merge_tag_release', 'order': 1, 'progress': 25}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_build', 'name': 'build_prd', 'desc': u'生产环境打包Release分支', 'func': 'build_release', 'order': 2, 'progress': 50}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_build', 'name': 'deploy_parent', 'desc': u'提交parent', 'func': 'deploy_parent', 'order': 2, 'progress': 10}
    operation_template_collection.insert_one(one)

    one = {'type': 'init_java_app', 'name': 'init_java_app', 'desc': u'调用Salt初始化Java应用', 'func': 'init_java_app', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'del_java_app', 'name': 'del_java_app', 'desc': u'调用Salt抹除Java应用', 'func': 'del_java_app', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'archive_log', 'name': 'archive_log', 'desc': u'调用Salt归档应用当天的日志', 'func': 'archive_log', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'pre_publish', 'name': 'slb_block', 'desc': u'SLB屏蔽服务器', 'func': 'slb_block', 'order': 0, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_publish', 'name': 'hsf_offline', 'desc': u'HSF下线', 'func': 'hsf_offline', 'order': 1, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_publish', 'name': 'stop_java_app', 'desc': u'通过Salt停止应用', 'func': 'stop_java_app', 'order': 2, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_publish', 'name': 'clean_before_deploy', 'desc': u'发布前通过Salt清理应用环境', 'func': 'clean_before_deploy', 'order': 3, 'progress': 5}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_publish', 'name': 'upload_package', 'desc': u'通过Salt上传应用包', 'func': 'upload_package', 'order': 4, 'progress': 20}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_publish', 'name': 'start_java_app', 'desc': u'通过Salt启动应用', 'func': 'start_java_app', 'order': 5, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_publish', 'name': 'health_check', 'desc': u'健康监测', 'func': 'health_check', 'order': 6, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_publish', 'name': 'hsf_online', 'desc': u'HSF上线', 'func': 'hsf_online', 'order': 7, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_publish', 'name': 'slb_unblock', 'desc': u'SLB开放服务器', 'func': 'slb_unblock', 'order': 8, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_publish', 'name': 'mark_server_published', 'desc': u'标记服务器已发布', 'func': 'mark_server_published', 'order': 9, 'progress': 5}
    operation_template_collection.insert_one(one)

    one = {'type': 'prd_publish', 'name': 'slb_block', 'desc': u'SLB屏蔽服务器', 'func': 'slb_block', 'order': 0, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_publish', 'name': 'stop_health_check', 'desc': u'停止健康检查', 'func': 'stop_health_check', 'order': 1, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_publish', 'name': 'hsf_offline', 'desc': u'HSF下线', 'func': 'hsf_offline', 'order': 2, 'progress': 5}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_publish', 'name': 'stop_java_app', 'desc': u'通过Salt停止应用', 'func': 'stop_java_app', 'order': 3, 'progress': 5}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_publish', 'name': 'clean_before_deploy', 'desc': u'发布前通过Salt清理应用环境', 'func': 'clean_before_deploy', 'order': 4, 'progress': 5}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_publish', 'name': 'upload_package', 'desc': u'通过Salt上传应用包', 'func': 'upload_package', 'order': 5, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_publish', 'name': 'start_java_app', 'desc': u'通过Salt启动应用', 'func': 'start_java_app', 'order': 6, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_publish', 'name': 'health_check', 'desc': u'健康监测', 'func': 'health_check', 'order': 7, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_publish', 'name': 'hsf_online', 'desc': u'HSF上线', 'func': 'hsf_online', 'order': 8, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_publish', 'name': 'start_health_check', 'desc': u'启动健康检查', 'func': 'start_health_check', 'order': 9, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_publish', 'name': 'slb_unblock', 'desc': u'SLB开放服务器', 'func': 'slb_unblock', 'order': 10, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_publish', 'name': 'mark_server_published', 'desc': u'标记服务器已发布', 'func': 'mark_server_published', 'order': 11, 'progress': 5}
    operation_template_collection.insert_one(one)

    one = {'type': 'commit_project_diamond', 'name': 'commit_project_diamond', 'desc': u'提交项目Diamond配置', 'func': 'commit_project_diamond', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'pre_commit', 'name': 'merge_release_tag', 'desc': u'合并Release到Tag', 'func': 'merge_release_tag', 'order': 0, 'progress': 20}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_commit', 'name': 'commit_pre_antx', 'desc': u'提交预发Antx', 'func': 'commit_pre_antx', 'order': 1, 'progress': 20}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_commit', 'name': 'commit_aut_antx', 'desc': u'提交自动化测试Antx', 'func': 'commit_aut_antx', 'order': 2, 'progress': 20}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_commit', 'name': 'merge_prd_antx', 'desc': u'合并生产区Antx', 'func': 'merge_prd_antx', 'order': 3, 'progress': 20}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_commit', 'name': 'add_prd_app', 'desc': u'添加生产区发布标记', 'func': 'add_prd_app', 'order': 4, 'progress': 20}
    operation_template_collection.insert_one(one)

    one = {'type': 'prd_commit', 'name': 'merge_release_trunk', 'desc': u'合并Release到Trunk', 'func': 'merge_release_trunk', 'order': 0, 'progress': 50}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_commit', 'name': 'commit_prd_antx', 'desc': u'提交生产Antx', 'func': 'commit_prd_antx', 'order': 1, 'progress': 50}
    operation_template_collection.insert_one(one)

    one = {'type': 'dzbd_publish', 'name': 'dzbd_publish', 'desc': u'电子保单发布', 'func': 'dzbd_publish', 'order': 0, 'progress': 90}
    operation_template_collection.insert_one(one)
    one = {'type': 'dzbd_publish', 'name': 'mark_server_published', 'desc': u'标记服务器已发布', 'func': 'mark_server_published', 'order': 1, 'progress': 10}
    operation_template_collection.insert_one(one)

    one = {'type': 'pre_dzbd_commit', 'name': 'merge_branch_tag', 'desc': u'预发提交电子保单', 'func': 'merge_branch_tag', 'order': 0, 'progress': 50}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_dzbd_commit', 'name': 'add_prd_app', 'desc': u'电子保单添加到生产区发布标记', 'func': 'add_prd_app', 'order': 1, 'progress': 50}
    operation_template_collection.insert_one(one)

    one = {'type': 'prd_dzbd_commit', 'name': 'merge_tag_trunk', 'desc': u'生产提交电子保单', 'func': 'merge_tag_trunk', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'dzbd_rollback', 'name': 'dzbd_rollback', 'desc': u'电子保单回滚', 'func': 'dzbd_rollback', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'pre_precheck', 'name': 'pre_precheck', 'desc': u'预发前预检', 'func': 'pre_precheck', 'order': 0, 'progress': 80}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_precheck', 'name': 'allocate_pre_server', 'desc': u'占用预发服务器', 'func': 'allocate_pre_server', 'order': 1, 'progress': 20}
    operation_template_collection.insert_one(one)

    one = {'type': 'prd_precheck', 'name': 'prd_precheck', 'desc': u'生产前预检', 'func': 'prd_precheck', 'order': 0, 'progress': 80}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_precheck', 'name': 'release_pre_server', 'desc': u'释放预发服务器', 'func': 'release_pre_server', 'order': 1, 'progress': 20}
    operation_template_collection.insert_one(one)

    one = {'type': 'local_commit_error', 'name': 'release_pre_server', 'desc': u'释放预发服务器', 'func': 'release_pre_server', 'order': 0, 'progress': 25}
    operation_template_collection.insert_one(one)
    one = {'type': 'local_commit_error', 'name': 'rollback_pre_config', 'desc': u'回退预发配置', 'func': 'rollback_pre_config', 'order': 1, 'progress': 50}
    operation_template_collection.insert_one(one)
    one = {'type': 'local_commit_error', 'name': 'release_pre_diamond', 'desc': u'释放预发Diamond修改名额', 'func': 'release_pre_diamond', 'order': 2, 'progress': 25}
    operation_template_collection.insert_one(one)

    one = {'type': 'pre_commit_error', 'name': 'release_prd_app', 'desc': u'释放生产区发布标记', 'func': 'release_prd_app', 'order': 0, 'progress': 50}
    operation_template_collection.insert_one(one)
    one = {'type': 'pre_commit_error', 'name': 'release_prd_diamond', 'desc': u'释放生产Diamond修改名额', 'func': 'release_prd_diamond', 'order': 1, 'progress': 50}
    operation_template_collection.insert_one(one)

    one = {'type': 'nopre_local_commit', 'name': 'merge_branch_tag', 'desc': u'合并Branch到Tag', 'func': 'merge_branch_tag', 'order': 0, 'progress': 40}
    operation_template_collection.insert_one(one)
    one = {'type': 'nopre_local_commit', 'name': 'merge_prd_antx', 'desc': u'合并生产区Antx', 'func': 'merge_prd_antx', 'order': 1, 'progress': 30}
    operation_template_collection.insert_one(one)
    one = {'type': 'nopre_local_commit', 'name': 'add_prd_app', 'desc': u'添加生产区发布标记', 'func': 'add_prd_app', 'order': 2, 'progress': 30}
    operation_template_collection.insert_one(one)

    one = {'type': 'pre_diamond_allocate', 'name': 'allocate_pre_diamond', 'desc': u'分配预发Diamond修改名额', 'func': 'allocate_pre_diamond', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'prd_diamond_allocate', 'name': 'release_pre_diamond', 'desc': u'释放预发Diamond修改名额', 'func': 'release_pre_diamond', 'order': 1, 'progress': 50}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_diamond_allocate', 'name': 'allocate_prd_diamond', 'desc': u'分配生产Diamond修改名额', 'func': 'allocate_prd_diamond', 'order': 1, 'progress': 50}
    operation_template_collection.insert_one(one)

    one = {'type': 'prd_release', 'name': 'release_prd_app', 'desc': u'释放生产区发布标记', 'func': 'release_prd_app', 'order': 0, 'progress': 50}
    operation_template_collection.insert_one(one)
    one = {'type': 'prd_release', 'name': 'release_prd_diamond', 'desc': u'释放生产Diamond修改名额', 'func': 'release_prd_diamond', 'order': 1, 'progress': 50}
    operation_template_collection.insert_one(one)

    one = {'type': 'ci_build', 'name': 'ci_build', 'desc': u'持续集成打包', 'func': 'ci_build', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'aut_ci_build', 'name': 'aut_ci_build', 'desc': u'自动化测试打包', 'func': 'aut_ci_build', 'order': 0, 'progress': 80}
    operation_template_collection.insert_one(one)
    one = {'type': 'aut_ci_build', 'name': 'commit_aut_antx', 'desc': u'提交自动化测试Antx', 'func': 'commit_aut_antx', 'order': 1, 'progress': 10}
    operation_template_collection.insert_one(one)
    one = {'type': 'aut_ci_build', 'name': 'kafka_message', 'desc': u'kafka消息记录', 'func': 'kafka_message', 'order': 2, 'progress': 10}
    operation_template_collection.insert_one(one)

    one = {'type': 'jaguar_check', 'name': 'jaguar_check', 'desc': u'美洲豹生产打包前检查', 'func': 'jaguar_check', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'release_preallocate_version', 'name': 'release_preallocate_version', 'desc': u'释放项目预占的版本', 'func': 'release_preallocate_version', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'pre_parent_allocate', 'name': 'pre_parent_allocate', 'desc': u'预发本地Parent准备', 'func': 'pre_parent_allocate', 'order': 2, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'wait_app_build', 'name': 'wait_app_build', 'desc': u'等待并行打包完成', 'func': 'wait_app_build', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'wait_dzbd_publish', 'name': 'wait_dzbd_publish', 'desc': u'等待电子保单并行发布完成', 'func': 'wait_dzbd_publish', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'wait_app_publish', 'name': 'wait_app_publish', 'desc': u'等待并行发布完成', 'func': 'wait_app_publish', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'pre_sql_before_execute', 'name': 'pre_sql_before_execute', 'desc': u'预发发布前执行SQL脚本', 'func': 'pre_sql_before_execute', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'pre_sql_after_execute', 'name': 'pre_sql_after_execute', 'desc': u'预发发布后执行SQL脚本', 'func': 'pre_sql_after_execute', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'prd_sql_before_execute', 'name': 'prd_sql_before_execute', 'desc': u'生产发布前执行SQL脚本', 'func': 'prd_sql_before_execute', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)

    one = {'type': 'prd_sql_after_execute', 'name': 'prd_sql_after_execute', 'desc': u'生产发布后执行SQL脚本', 'func': 'prd_sql_after_execute', 'order': 0, 'progress': 100}
    operation_template_collection.insert_one(one)


def reset_switch():
    publish_switch_collection.delete_many({})

    publish_switch = {
        'auto_local': True,
        'auto_pre': False,
        'no_publish_date': {'begin': datetime.datetime.utcnow(), 'end': datetime.datetime.utcnow()},
        'publish_date': {'begin': datetime.datetime.utcnow(), 'end': datetime.datetime.utcnow()},
        'weekly_publish_date': {
            'default': {
                'Mon': {'begin': '00:00', 'end': '00:00'},
                'Tue': {'begin': '00:00', 'end': '00:00'},
                'Wed': {'begin': '00:00', 'end': '00:00'},
                'Thu': {'begin': '00:00', 'end': '00:00'},
                'Fri': {'begin': '00:00', 'end': '00:00'},
                'Sat': {'begin': '00:00', 'end': '00:00'},
                'Sun': {'begin': '00:00', 'end': '00:00'}
            }
        }}

    publish_switch_collection.insert_one(publish_switch)


def reset_notice_system():
    notice_system_collection.delete_many({})

    notice_system_collection.insert_one({'content': '', 'week_day': '1', 'create_date': datetime.datetime.utcnow(), 'update_date': datetime.datetime.utcnow(), 'creator_id': 'system', 'type': "notice"})
    notice_system_collection.insert_one({'content': '', 'week_day': '2', 'create_date': datetime.datetime.utcnow(), 'update_date': datetime.datetime.utcnow(), 'creator_id': 'system', 'type': "notice"})
    notice_system_collection.insert_one({'content': '', 'week_day': '3', 'create_date': datetime.datetime.utcnow(), 'update_date': datetime.datetime.utcnow(), 'creator_id': 'system', 'type': "notice"})
    notice_system_collection.insert_one({'content': '', 'week_day': '4', 'create_date': datetime.datetime.utcnow(), 'update_date': datetime.datetime.utcnow(), 'creator_id': 'system', 'type': "notice"})
    notice_system_collection.insert_one({'content': '', 'week_day': '5', 'create_date': datetime.datetime.utcnow(), 'update_date': datetime.datetime.utcnow(), 'creator_id': 'system', 'type': "notice"})
    notice_system_collection.insert_one({'content': '', 'week_day': '6', 'create_date': datetime.datetime.utcnow(), 'update_date': datetime.datetime.utcnow(), 'creator_id': 'system', 'type': "notice"})
    notice_system_collection.insert_one({'content': '', 'week_day': '7', 'create_date': datetime.datetime.utcnow(), 'update_date': datetime.datetime.utcnow(), 'creator_id': 'system', 'type': "notice"})
    notice_system_collection.insert_one({'content': '', 'create_date': datetime.datetime.utcnow(), 'update_date': datetime.datetime.utcnow(), 'creator_id': 'system', 'type': "systemUpdate"})