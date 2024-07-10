# -*- coding:utf-8 -*-

from app.out.cmdb_core import CMDBCore
from app.out.apprepo import Apprepo
from app.out.idb import iDB
from app.services.operation.operation_service import OperationService
from app.services.project.sql_scripts_project_service import SQLScriptsProjectService
from app.mongodb import flow_data_collection
from app import app, root_logger


class WrapOperation(object):

    @staticmethod
    def wrap_operation(flow_type, operation_type, flow_id, operator_id):
        flow_data = flow_data_collection.find_one({'flow_id': flow_id})
        result = None
        if flow_data:
            flow_data = flow_data.get('data')
            flow_data['flow_id'] = flow_id
            if flow_type == 'default':
                flow_data['publish_id'] = flow_id
                if operation_type == 'pre_build':
                    result = WrapOperation.default_pre_build(operator_id=operator_id, **flow_data)
                elif operation_type == 'prd_build':
                    result = WrapOperation.default_prd_build(operator_id=operator_id, **flow_data)
                elif operation_type == 'pre_publish':
                    result = WrapOperation.default_pre_publish(operator_id=operator_id, **flow_data)
                elif operation_type == 'prd_publish':
                    result = WrapOperation.default_prd_publish(operator_id=operator_id, **flow_data)
                elif operation_type == 'pre_commit':
                    result = WrapOperation.default_pre_commit(operator_id=operator_id, **flow_data)
                elif operation_type == 'pre_commit_error':
                    result = WrapOperation.pre_commit_error(operator_id=operator_id, **flow_data)
                elif operation_type == 'prd_commit':
                    result = WrapOperation.default_prd_commit(operator_id=operator_id, **flow_data)
                elif operation_type == 'local_commit':
                    result = WrapOperation.local_commit(operator_id=operator_id, **flow_data)
                elif operation_type == 'local_commit_error':
                    result = WrapOperation.local_commit_error(operator_id=operator_id, **flow_data)
                elif operation_type == 'pre_sql_before':
                    result = WrapOperation.pre_sql_before(operator_id=operator_id, **flow_data)
                elif operation_type == 'pre_sql_after':
                    result = WrapOperation.pre_sql_after(operator_id=operator_id, **flow_data)
                elif operation_type == 'prd_sql_before':
                    result = WrapOperation.prd_sql_before(operator_id=operator_id, **flow_data)
                elif operation_type == 'prd_sql_after':
                    result = WrapOperation.prd_sql_after(operator_id=operator_id, **flow_data)
            elif flow_type == 'nopre':
                flow_data['publish_id'] = flow_id
                if operation_type == 'local_commit':
                    result = WrapOperation.nopre_local_commit(operator_id=operator_id, **flow_data)
                elif operation_type == 'prd_build':
                    result = WrapOperation.default_prd_build(operator_id=operator_id, **flow_data)
                elif operation_type == 'prd_publish':
                    result = WrapOperation.default_prd_publish(operator_id=operator_id, **flow_data)
                elif operation_type == 'prd_commit':
                    result = WrapOperation.default_prd_commit(operator_id=operator_id, **flow_data)
                elif operation_type == 'pre_commit_error':
                    result = WrapOperation.pre_commit_error(operator_id=operator_id, **flow_data)
        return result

    @staticmethod
    def default_pre_build(operator_id='system', **kwargs):
        share_order = kwargs.get('share_order')
        app_order = kwargs.get('app_order')
        project_id = kwargs.get('project_id')
        publish_id = kwargs.get('publish_id')
        flow_id = kwargs.get('flow_id')
        app_infos = kwargs.get('app_info')
        has_first_time = False
        for app_id in share_order:
            app_info = app_infos.get(str(app_id))
            if app_info.get('first_time'):
                data = dict()
                data['project_id'] = project_id
                OperationService.run_operation("pre_parent_allocate", "self", "Parent", operator_id, _flow_id=publish_id, **data)
                has_first_time = True
                break

        op_result = True
        for app_id in share_order:
            app_info = app_infos.get(str(app_id))
            if app_info.get('pre_built'):
                continue
            app_name = app_info.get('name')
            artifact_id = app_info.get('artifact_id')
            ext_name = app_info.get('ext_name')
            app_type = app_info.get('type')
            data = dict()
            data['app_id'] = int(app_id)
            data['branch_name'] = app_info.get('branch_name')
            data['branch_revision'] = app_info.get('branch_revision')
            data['update_pom'] = True
            data['env'] = "pre"
            data['project_id'] = project_id
            data['publish_id'] = publish_id
            data['artifact_id'] = artifact_id
            data['ext_name'] = ext_name
            data['app_type'] = app_type
            data['flow_id'] = flow_id
            data['first_time'] = app_info.get('first_time')
            data['has_first_time'] = has_first_time
            result = OperationService.run_operation("pre_build", "jenkins", app_name, operator_id, _flow_id=publish_id, **data)
            if not result:
                op_result = False
                break
        if not op_result:
            data = dict()
            data['project_id'] = project_id
            OperationService.run_operation("release_preallocate_version", "self", "Version", operator_id, _flow_id=publish_id, **data)
            return "failed"
        change = dict()
        for app_id in app_order:
            if not app_infos.get(str(app_id)).get('pre_built'):
                change['data.app_info.{}.pre_built'.format(app_id)] = None
        if change:
            flow_data_collection.update_one({'flow_id': flow_id}, {'$set': change})
        for app_id in app_order:
            app_info = app_infos.get(str(app_id))
            if app_info.get('pre_built'):
                continue
            app_name = app_info.get('name')
            artifact_id = app_info.get('artifact_id')
            ext_name = app_info.get('ext_name')
            app_type = app_info.get('type')
            data = dict()
            data['app_id'] = int(app_id)
            data['branch_name'] = app_info.get('branch_name')
            data['branch_revision'] = app_info.get('branch_revision')
            data['update_pom'] = True
            data['env'] = "pre"
            data['project_id'] = project_id
            data['publish_id'] = publish_id
            data['artifact_id'] = artifact_id
            data['ext_name'] = ext_name
            data['app_type'] = app_type
            data['flow_id'] = flow_id
            data['first_time'] = app_info.get('first_time')
            data['has_first_time'] = has_first_time
            OperationService.run_operation.delay("pre_build", "jenkins", app_name, operator_id, _flow_id=publish_id, **data)
        data = dict()
        data['publish_id'] = publish_id
        data['env'] = 'pre'
        op_result = OperationService.run_operation("wait_app_build", "self", publish_id, operator_id, _flow_id=publish_id, **data)
        if not op_result:
            data = dict()
            data['project_id'] = project_id
            OperationService.run_operation("release_preallocate_version", "self", "Version", operator_id, _flow_id=publish_id, **data)
            return "failed"
        data = dict()
        data['project_id'] = project_id
        OperationService.run_operation("release_preallocate_version", "self", "Version", operator_id, _flow_id=publish_id, **data)
        return "success"

    @staticmethod
    def default_prd_build(operator_id='system', **kwargs):
        share_order = kwargs.get('share_order')
        app_order = kwargs.get('app_order')
        project_id = kwargs.get('project_id')
        publish_id = kwargs.get('publish_id')
        flow_id = kwargs.get('flow_id')
        app_infos = kwargs.get('app_info')
        for app_id in app_order:
            # 特殊应用打包发布前要执行特殊操作
            if str(app_id) in app.config['SPECIAL_APP_OPERATION_BEFORE_PRD_BUILD'].keys():
                app_info = app_infos.get(str(app_id))
                app_name = app_info.get('name')
                special_operation_type = app.config['SPECIAL_APP_OPERATION_BEFORE_PRD_BUILD'].get(str(app_id))
                result = OperationService.run_operation(special_operation_type, 'special', app_name, operator_id, _flow_id=flow_id)
                if not result:
                    return "failed"
        for app_id in share_order:
            app_info = app_infos.get(str(app_id))
            # 已经打包成功过了，跳过
            if app_info.get('prd_built'):
                continue
            # 已经被别的发布单带着发掉了，跳过
            if app_info.get('skip'):
                continue
            app_name = app_info.get('name')
            artifact_id = app_info.get('artifact_id')
            ext_name = app_info.get('ext_name')
            app_type = app_info.get('type')
            data = dict()
            data['app_id'] = int(app_id)
            data['tag_revision'] = app_info.get('tag_revision')
            data['env'] = "prd"
            data['project_id'] = project_id
            data['publish_id'] = publish_id
            data['artifact_id'] = artifact_id
            data['ext_name'] = ext_name
            data['app_type'] = app_type
            data['flow_id'] = flow_id
            result = OperationService.run_operation("prd_build", "jenkins", app_name, operator_id, _flow_id=flow_id, **data)
            if not result:
                data = dict()
                data['project_id'] = project_id
                OperationService.run_operation("release_preallocate_version", "self", "Version", operator_id, _flow_id=publish_id, **data)
                return "failed"
        change = dict()
        for app_id in app_order:
            if not app_infos.get(str(app_id)).get('prd_built'):
                change['data.app_info.{}.prd_built'.format(app_id)] = None
        if change:
            flow_data_collection.update_one({'flow_id': flow_id}, {'$set': change})
        for app_id in app_order:
            app_info = app_infos.get(str(app_id))
            # 已经打包成功过了，跳过
            if app_info.get('prd_built'):
                continue
            # 已经被别的发布单带着发掉了，跳过
            if app_info.get('skip'):
                continue
            app_name = app_info.get('name')
            artifact_id = app_info.get('artifact_id')
            ext_name = app_info.get('ext_name')
            app_type = app_info.get('type')
            data = dict()
            data['app_id'] = int(app_id)
            data['tag_revision'] = app_info.get('tag_revision')
            data['env'] = "prd"
            data['project_id'] = project_id
            data['publish_id'] = publish_id
            data['artifact_id'] = artifact_id
            data['ext_name'] = ext_name
            data['app_type'] = app_type
            data['flow_id'] = flow_id
            OperationService.run_operation.delay("prd_build", "jenkins", app_name, operator_id, _flow_id=flow_id, **data)
        data = dict()
        data['publish_id'] = publish_id
        data['env'] = 'prd'
        result = OperationService.run_operation("wait_app_build", "self", publish_id, operator_id, _flow_id=flow_id, **data)
        if not result:
            data = dict()
            data['project_id'] = project_id
            OperationService.run_operation("release_preallocate_version", "self", "Version", operator_id, _flow_id=flow_id, **data)
            return "failed"
        return "success"

    @staticmethod
    def default_pre_publish(operator_id='system', **kwargs):
        app_order = kwargs.get('app_order')
        project_id = kwargs.get('project_id')
        publish_id = kwargs.get('publish_id')
        app_infos = kwargs.get('app_info')

        # 发布前更新Diamond
        diamond_data = dict()
        diamond_data['project_id'] = project_id
        diamond_data['env'] = 'pre'
        diamond_data['m_type'] = 'before'
        result = OperationService.run_operation("commit_project_diamond", 'pre_diamond', 'diamond', operator_id, _flow_id=publish_id, **diamond_data)
        if not result:
            return "failed"

        dzbd = kwargs.get('dzbd')
        # 发布电子保单
        if dzbd:
            servers = app.config['DZBD_PRE_SERVER']
            published_pre_servers = dzbd.get('published_pre_servers', [])
            for server in servers:
                if server in published_pre_servers:
                    continue
                data = dict()
                data['env'] = 'pre'
                data['publish_id'] = publish_id
                data['dzbd_server'] = server
                data['branch_name'] = dzbd.get('branch_name')
                data['vcs_full_url'] = dzbd.get('vcs_full_url')
                data['svn_revision'] = dzbd.get('branch_revision')
                data['dir_path'] = app.config['DZBD_DIR']
                data['user'] = app.config['DZBD_SVN_USER']
                data['password'] = app.config['DZBD_SVN_PASS']
                OperationService.run_operation.delay("dzbd_publish", "{}".format(server), 'dzbd', operator_id, _flow_id=publish_id, **data)

            data = dict()
            data['publish_id'] = publish_id
            data['env'] = 'pre'
            op_result = OperationService.run_operation("wait_dzbd_publish", "self", publish_id, operator_id, _flow_id=publish_id, **data)
            if not op_result:
                return "failed"

        # 发布应用
        for app_id in app_order:
            app_info = app_infos.get(str(app_id))
            info = Apprepo.get_app_info(app_id)
            if info:
                published_pre_servers = app_info.get('published_pre_servers', [])
                app_name = info.get('name')
                org = info.get('company_code')
                fixed_server = app_info.get('fixed_pre_server')
                pre_server_amount = app_info.get('pre_server_amount')
                ecs_list = CMDBCore.query_arrange('pre', app_id, 'ecs')
                slb_list = CMDBCore.query_arrange('pre', app_id, 'slb')

                # 跳过预发
                if pre_server_amount == 0:
                    continue

                if not ecs_list:
                    root_logger.info("default_pre_publish fail, app({}) has no ecs".format(app_name))
                    return "failed"

                if fixed_server:
                    all_ecs_list = ecs_list
                    ecs_list = list()
                    for ecs in all_ecs_list:
                        if "{}:{}".format(ecs.get('res_id'), ecs.get('port')) in ["{}:{}".format(e.get('res_id'), e.get('port')) for e in fixed_server]:
                            ecs_list.append(ecs)

                for ecs in ecs_list:
                    if "{}:{}".format(ecs.get('ip'), ecs.get('port')) in published_pre_servers:
                        continue
                    if fixed_server and "{}:{}".format(ecs.get('res_id'), ecs.get('port')) not in ["{}:{}".format(e.get('res_id'), e.get('port')) for e in fixed_server]:
                        continue
                    data = dict()
                    data['app_id'] = app_id
                    data['publish_id'] = publish_id
                    data['company'] = org
                    data['env'] = 'pre'
                    data['ip'] = ecs.get('ip')
                    data['app_name'] = app_name
                    port = int(ecs.get('port'))
                    data['port'] = port
                    data['hsf_port'] = port + 1
                    data['hsf_timeout'] = 120
                    data['ext_name'] = app_info.get('ext_name')
                    data['check_url'] = info.get('check_url')
                    data['pack_serv_url'] = "{}/release/app/{}/pre/{}/".format(app.config['PACKAGE_SERVER_URL'], app_id, publish_id)
                    if slb_list:
                        data['ecs_id'] = ecs.get('res_id')
                        data['slb_id'] = slb_list[0].get('res_id')
                    result = OperationService.run_operation("pre_publish", ecs.get('ip'), app_name, operator_id, _flow_id=publish_id, **data)
                    if not result:
                        return "failed"
            else:
                root_logger.info("default_pre_publish fail, can not get appinfo from apprepo(appid={})".format(app_id))
                return "failed"

        # 发布后更新Diamond
        diamond_data = dict()
        diamond_data['project_id'] = project_id
        diamond_data['env'] = 'pre'
        diamond_data['m_type'] = 'after'
        result = OperationService.run_operation("commit_project_diamond", 'pre_diamond', 'diamond', operator_id, _flow_id=publish_id, **diamond_data)
        if not result:
            return "failed"

        return "success"

    @staticmethod
    def default_prd_publish(operator_id='system', **kwargs):
        app_order = kwargs.get('app_order')
        project_id = kwargs.get('project_id')
        publish_id = kwargs.get('publish_id')
        app_infos = kwargs.get('app_info')

        # 发布前更新Diamond
        diamond_data = dict()
        diamond_data['project_id'] = project_id
        diamond_data['env'] = 'prd'
        diamond_data['m_type'] = 'before'
        result = OperationService.run_operation("commit_project_diamond", 'prd_diamond', 'diamond', operator_id, _flow_id=publish_id, **diamond_data)
        if not result:
            return "failed"

        dzbd = kwargs.get('dzbd')
        # 发布电子保单
        if dzbd and not dzbd.get('skip'):
            servers = app.config['DZBD_PRD_SERVER']
            published_prd_servers = dzbd.get('published_prd_servers', [])
            for server in servers:
                if server in published_prd_servers:
                    continue
                data = dict()
                data['env'] = 'prd'
                data['publish_id'] = publish_id
                data['dzbd_server'] = server
                data['svn_revision'] = dzbd.get('tag_revision')
                data['dir_path'] = app.config['DZBD_DIR']
                data['user'] = app.config['DZBD_SVN_USER']
                data['password'] = app.config['DZBD_SVN_PASS']
                OperationService.run_operation.delay("dzbd_publish", "{}".format(server), 'dzbd', operator_id, _flow_id=publish_id, **data)

            data = dict()
            data['publish_id'] = publish_id
            data['env'] = 'prd'
            op_result = OperationService.run_operation("wait_dzbd_publish", "self", publish_id, operator_id, _flow_id=publish_id, **data)
            if not op_result:
                return "failed"

        # 发布应用
        for app_id in app_order:
            app_info = app_infos.get(str(app_id))
            if app_info.get('skip'):
                continue
            info = Apprepo.get_app_info(app_id)
            if info:
                published_prd_servers = app_info.get('published_prd_servers', [])
                app_name = info.get('name')
                org = info.get('company_code')
                fixed_server = app_info.get('fixed_prd_server')
                ecs_list = CMDBCore.query_arrange('prd', app_id, 'ecs')
                slb_list = CMDBCore.query_arrange('prd', app_id, 'slb')
                if not ecs_list:
                    root_logger.info("default_prd_publish fail, app({}) has no ecs".format(app_name))
                    return "failed"

                if fixed_server:
                    all_ecs_list = ecs_list
                    ecs_list = list()
                    for ecs in all_ecs_list:
                        if "{}:{}".format(ecs.get('res_id'), ecs.get('port')) in ["{}:{}".format(e.get('res_id'), e.get('port')) for e in fixed_server]:
                            ecs_list.append(ecs)

                # 按30% 30% 40%的比例进行发布
                server_count_list = list()
                server_count_list.append(int(round(len(ecs_list) / 3.0)))
                server_count_list.append(int(round(len(ecs_list) / 3.0)))
                if server_count_list[0] + server_count_list[1] < len(ecs_list):
                    server_count_list.append(len(ecs_list) - server_count_list[0] - server_count_list[1])

                for count in server_count_list:
                    sub_ecs_list = list()
                    for i in range(count):
                        sub_ecs_list.append(ecs_list.pop(0))

                    for ecs in sub_ecs_list:
                        if "{}:{}".format(ecs.get('ip'), ecs.get('port')) in published_prd_servers:
                            continue
                        if fixed_server and "{}:{}".format(ecs.get('res_id'), ecs.get('port')) not in ["{}:{}".format(e.get('res_id'), e.get('port')) for e in fixed_server]:
                            continue
                        data = dict()
                        data['app_id'] = app_id
                        data['publish_id'] = publish_id
                        data['company'] = org
                        data['env'] = 'prd'
                        data['ip'] = ecs.get('ip')
                        data['app_name'] = app_name
                        port = int(ecs.get('port'))
                        data['port'] = port
                        data['hsf_port'] = port + 1
                        data['hsf_timeout'] = 120
                        data['ext_name'] = app_info.get('ext_name')
                        data['check_url'] = info.get('check_url')
                        data['app_owner_list'] = info.get('owner_list')
                        data['app_contacts_list'] = info.get('contact_list')
                        data['pack_serv_url'] = "{}/release/app/{}/prd/{}/".format(app.config['PACKAGE_SERVER_URL'], app_id, publish_id)
                        if slb_list:
                            data['ecs_id'] = ecs.get('res_id')
                            data['slb_id'] = slb_list[0].get('res_id')
                        OperationService.run_operation.delay("prd_publish", ecs.get('ip'), app_name, operator_id, _flow_id=publish_id, **data)

                    data = dict()
                    data['publish_id'] = publish_id
                    data['env'] = 'prd'
                    data['app_id'] = app_id
                    data['server_list'] = ["{}:{}".format(ecs.get('ip'), ecs.get('port')) for ecs in sub_ecs_list]
                    op_result = OperationService.run_operation("wait_app_publish", "self", publish_id, operator_id, _flow_id=publish_id, **data)
                    if not op_result:
                        return "failed"
            else:
                root_logger.info("default_prd_publish fail, can not get appinfo from apprepo(appid={})".format(app_id))
                return "failed"

        # 发布后更新Diamond
        diamond_data = dict()
        diamond_data['project_id'] = project_id
        diamond_data['env'] = 'prd'
        diamond_data['m_type'] = 'after'
        result = OperationService.run_operation("commit_project_diamond", 'prd_diamond', 'diamond', operator_id, _flow_id=publish_id, **diamond_data)
        if not result:
            return "failed"

        return "success"

    @staticmethod
    def default_pre_commit(operator_id='system', **kwargs):
        # 上生产前的预检操作
        project_id = kwargs.get('project_id')
        flow_id = kwargs.get('flow_id')
        publish_id = kwargs.get('publish_id')
        result = OperationService.run_operation("prd_precheck", "publish", str(publish_id), operator_id, _flow_id=publish_id,
                                                **{"publish_id": publish_id})
        if not result:
            return "failed"

        app_infos = kwargs.get('app_info')
        dzbd = kwargs.get('dzbd')
        # 提交电子保单
        if dzbd:
            data = dict()
            data['flow_id'] = flow_id
            data['app_id'] = dzbd.get('app_id')
            data['branch_name'] = dzbd.get('branch_name')
            data['branch_revision'] = dzbd.get('branch_revision')
            data['project_id'] = project_id
            data['publish_id'] = flow_id
            data['app_name'] = 'dzbd'
            data['scheduled_time'] = kwargs.get('scheduled_time').strftime('%Y-%m-%d %H:%M') if kwargs.get('scheduled_time') else None
            if kwargs.get('sql_before'):
                data['ready'] = False
            else:
                data['ready'] = True
            result = OperationService.run_operation("pre_dzbd_commit", "apprepo", 'dzbd', operator_id, _flow_id=publish_id, **data)
            if not result:
                # 已经通过了预检，理论上不会失败了
                root_logger.error("default_pre_commit failed in pre_dzbd_commit after prd_precheck success!")
                return "failed"
        # 提交应用
        for app_id, app_info in app_infos.items():
            app_name = app_info.get('name')
            data = dict()
            data['flow_id'] = flow_id
            data['app_id'] = int(app_id)
            data['pre_release_name'] = app_info.get('pre_release_name')
            data['project_id'] = project_id
            data['publish_id'] = publish_id
            data['app_name'] = app_name
            data['scheduled_time'] = kwargs.get('scheduled_time').strftime('%Y-%m-%d %H:%M') if kwargs.get('scheduled_time') else None
            if kwargs.get('sql_before'):
                data['ready'] = False
            else:
                data['ready'] = True
            result = OperationService.run_operation("pre_commit", "apprepo", app_name, operator_id, _flow_id=publish_id, **data)
            if not result:
                # 已经通过了预检，理论上不会失败了
                root_logger.error("default_pre_commit failed in pre_commit after prd_precheck success!")
                return "failed"
        # 添加hot diamond
        result = OperationService.run_operation("prd_diamond_allocate", "self", "Diamond", operator_id,
                                                _flow_id=publish_id, **{"project_id": project_id, "publish_id": publish_id})
        if not result:
            # 已经通过了预检，理论上不会失败了
            root_logger.error("default_pre_commit failed in prd_diamond_allocate after prd_precheck success!")
            return "failed"

        return "success"

    @staticmethod
    def default_prd_commit(operator_id='system', **kwargs):
        project_id = kwargs.get('project_id')
        publish_id = kwargs.get('publish_id')
        app_infos = kwargs.get('app_info')
        dzbd = kwargs.get('dzbd')
        # 提交电子保单
        if dzbd and not dzbd.get('skip'):
            data = dict()
            data['app_id'] = dzbd.get('app_id')
            data['tag_revision'] = dzbd.get('tag_revision')
            result = OperationService.run_operation("prd_dzbd_commit", "apprepo", 'dzbd', operator_id, _flow_id=publish_id, **data)
            if not result:
                return "failed"
        # 提交应用
        for app_id, app_info in app_infos.items():
            app_info = app_infos.get(str(app_id))
            if app_info.get('skip'):
                continue
            app_name = app_info.get('name')
            data = dict()
            data['app_id'] = int(app_id)
            data['app_name'] = app_name
            data['app_type'] = app_info.get('type')
            data['project_id'] = project_id
            data['publish_id'] = publish_id
            data['prd_release_name'] = app_info.get('prd_release_name')
            result = OperationService.run_operation("prd_commit", "apprepo", app_name, operator_id, _flow_id=publish_id, **data)
            if not result:
                return "failed"
        # 更新Diamond的version、释放hot diamond
        result = OperationService.run_operation("prd_release", "self", "Diamond", operator_id,
                                                _flow_id=publish_id, **{"project_id": project_id, "publish_id": publish_id})
        if not result:
            return "failed"
        return "success"

    @staticmethod
    def local_commit(operator_id='system', **kwargs):
        # 上预发前的预检操作
        project_id = kwargs.get('project_id')
        publish_id = kwargs.get('publish_id')
        result = OperationService.run_operation("pre_precheck", "publish", str(publish_id), operator_id, _flow_id=publish_id,
                                                **{"publish_id": publish_id})
        if not result:
            return "failed"
        # 更新Diamond的version、分配hot diamond
        result = OperationService.run_operation("pre_diamond_allocate", "self", "Diamond", operator_id,
                                                _flow_id=publish_id, **{"project_id": project_id, "publish_id": publish_id})
        if not result:
            return "failed"
        return "success"

    @staticmethod
    def nopre_local_commit(operator_id='system', **kwargs):
        # 上生产前的预检操作
        project_id = kwargs.get('project_id')
        flow_id = kwargs.get('flow_id')
        publish_id = kwargs.get('publish_id')
        result = OperationService.run_operation("prd_precheck", "publish", str(publish_id), operator_id, _flow_id=publish_id,
                                                **{"publish_id": publish_id})
        if not result:
            return "failed"

        app_infos = kwargs.get('app_info')
        dzbd = kwargs.get('dzbd')
        # 提交电子保单
        if dzbd:
            data = dict()
            data['flow_id'] = flow_id
            data['app_id'] = dzbd.get('app_id')
            data['branch_name'] = dzbd.get('branch_name')
            data['branch_revision'] = dzbd.get('branch_revision')
            data['project_id'] = project_id
            data['publish_id'] = flow_id
            data['app_name'] = 'dzbd'
            if kwargs.get('sql_before'):
                data['ready'] = False
            else:
                data['ready'] = True
            result = OperationService.run_operation("pre_dzbd_commit", "apprepo", 'dzbd', operator_id, _flow_id=publish_id, **data)
            if not result:
                # 已经通过了预检，理论上不会失败了
                root_logger.error("nopre_local_commit failed in pre_dzbd_commit after prd_precheck success!")
                return "failed"
        # 提交应用
        for app_id, app_info in app_infos.items():
            app_name = app_info.get('name')
            data = dict()
            data['flow_id'] = flow_id
            data['app_id'] = int(app_id)
            data['branch_name'] = app_info.get('branch_name')
            data['branch_revision'] = app_info.get('branch_revision')
            data['project_id'] = project_id
            data['publish_id'] = publish_id
            data['app_name'] = app_name
            data['scheduled_time'] = kwargs.get('scheduled_time').strftime('%Y-%m-%d %H:%M') if kwargs.get('scheduled_time') else None
            if kwargs.get('sql_before'):
                data['ready'] = False
            else:
                data['ready'] = True
            result = OperationService.run_operation("nopre_local_commit", "apprepo", app_name, operator_id, _flow_id=publish_id, **data)
            if not result:
                # 已经通过了预检，理论上不会失败了
                root_logger.error("nopre_local_commit failed in nopre_local_commit after prd_precheck success!")
                return "failed"
        # 更新Diamond的version、添加hot diamond
        result = OperationService.run_operation("prd_diamond_allocate", "self", "Diamond", operator_id,
                                                _flow_id=publish_id, **{"project_id": project_id, "publish_id": publish_id})
        if not result:
            # 已经通过了预检，理论上不会失败了
            root_logger.error("nopre_local_commit failed in prd_diamond_allocate after prd_precheck success!")
            return "failed"

        return "success"

    @staticmethod
    def local_commit_error(operator_id='system', **kwargs):
        # 从待预发提交预发失败后的异常处理
        publish_id = kwargs.get('publish_id')
        project_id = kwargs.get('project_id')
        OperationService.run_operation("local_commit_error", "self", publish_id, operator_id, _flow_id=publish_id,
                                       **{'publish_id': publish_id, 'project_id': project_id})
        return

    @staticmethod
    def pre_commit_error(operator_id='system', **kwargs):
        # 从预发提交生产失败后的异常处理
        publish_id = kwargs.get('publish_id')
        project_id = kwargs.get('project_id')
        OperationService.run_operation("pre_commit_error", "self", publish_id, operator_id, _flow_id=publish_id,
                                       **{'publish_id': publish_id, 'project_id': project_id})
        return

    @staticmethod
    def pre_sql_before(operator_id='system', **kwargs):
        project_id = kwargs.get('project_id')
        sql_scripts_project = SQLScriptsProjectService.get_sql_scripts_project(project_id)
        if sql_scripts_project:
            if sql_scripts_project.get('manual').get('pre'):
                return
            else:
                sql_scripts_data = dict()
                sql_scripts_data['flow_id'] = kwargs.get('publish_id')
                sql_scripts_data['project_id'] = project_id
                sql_scripts_data['sql_svn_path'] = sql_scripts_project.get('vcs_full_url') + '/pre/'
                sql_scripts_data['revision'] = sql_scripts_project.get('submited_test_version').get('pre')
                result = OperationService.run_operation("pre_sql_before_execute", 'pre_sql', 'sql', operator_id,
                                                        _flow_id=kwargs.get('publish_id'), **sql_scripts_data)
                if result:
                    return "idb_success"
                else:
                    return
        return 'skip'


    @staticmethod
    def pre_sql_after(operator_id='system', **kwargs):
        project_id = kwargs.get('project_id')
        sql_scripts_project = SQLScriptsProjectService.get_sql_scripts_project(project_id)
        if sql_scripts_project:
            if sql_scripts_project.get('manual').get('pre'):
                return
            else:
                sql_scripts_data = dict()
                sql_scripts_data['flow_id'] = kwargs.get('publish_id')
                sql_scripts_data['project_id'] = project_id
                sql_scripts_data['sql_svn_path'] = sql_scripts_project.get('vcs_full_url') + '/pre/'
                sql_scripts_data['revision'] = sql_scripts_project.get('submited_test_version').get('pre')
                result = OperationService.run_operation("pre_sql_after_execute", 'pre_sql', 'sql', operator_id,
                                                        _flow_id=kwargs.get('publish_id'), **sql_scripts_data)
                if result:
                    return "idb_success"
                else:
                    return
        return 'skip'

    @staticmethod
    def prd_sql_before(operator_id='system', **kwargs):
        project_id = kwargs.get('project_id')
        sql_scripts_project = SQLScriptsProjectService.get_sql_scripts_project(project_id)
        if sql_scripts_project:
            if sql_scripts_project.get('manual').get('prd'):
                return
            else:
                sql_scripts_data = dict()
                sql_scripts_data['flow_id'] = kwargs.get('publish_id')
                sql_scripts_data['project_id'] = project_id
                sql_scripts_data['sql_svn_path'] = sql_scripts_project.get('vcs_full_url') + '/prd/'
                sql_scripts_data['revision'] = sql_scripts_project.get('submited_test_version').get('prd')
                result = OperationService.run_operation("prd_sql_before_execute", 'prd_sql', 'sql', operator_id,
                                                        _flow_id=kwargs.get('publish_id'), **sql_scripts_data)
                if result:
                    return "idb_success"
                else:
                    return
        return 'skip'

    @staticmethod
    def prd_sql_after(operator_id='system', **kwargs):
        project_id = kwargs.get('project_id')
        sql_scripts_project = SQLScriptsProjectService.get_sql_scripts_project(project_id)
        if sql_scripts_project:
            if sql_scripts_project.get('manual').get('prd'):
                return
            else:
                sql_scripts_data = dict()
                sql_scripts_data['flow_id'] = kwargs.get('publish_id')
                sql_scripts_data['project_id'] = project_id
                sql_scripts_data['sql_svn_path'] = sql_scripts_project.get('vcs_full_url') + '/prd/'
                sql_scripts_data['revision'] = sql_scripts_project.get('submited_test_version').get('prd')
                result = OperationService.run_operation("prd_sql_after_execute", 'prd_sql', 'sql', operator_id,
                                                        _flow_id=kwargs.get('publish_id'), **sql_scripts_data)
                if result:
                    return "idb_success"
                else:
                    return
        return 'skip'