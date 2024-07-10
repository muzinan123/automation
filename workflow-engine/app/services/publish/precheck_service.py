# -*- coding: utf8 -*-

from app.out.cmdb_core import CMDBCore
from app.services.apprepo_service import ApprepoService
from app.services.app_branch_service import AppBranchService
from app.services.diamond_service import DiamondService
from app.services.publish.experienced_app_list_service import ExperiencedAppListService
from app.services.publish.hot_pool_service import HotPoolService
from app.services.antx_service import AntxService
from app.services.project.sql_scripts_project_service import SQLScriptsProjectService
from app.mongodb import diamond_collection, flow_data_collection
from app.models.Project import Project
from app.util import Util
from app import app


class PreCheckService(object):

    @staticmethod
    def apply_publish_precheck(project_id, issue_id=None, oa_id=None):
        ret = dict()
        if issue_id:
            same_issue_count = flow_data_collection.find({'data.issue_id': issue_id}).count()
            ret['issue_id_ok'] = True
            if issue_id != app.config.get('SPECIAL_ISSUE_ID') and same_issue_count > 0:
                ret['issue_id_ok'] = False
            if ret['issue_id_ok']:
                ret['issue_id'] = issue_id

        if oa_id:
            same_oa_count = flow_data_collection.find({'data.oa_id': oa_id}).count()
            ret['oa_id_ok'] = True
            if oa_id != app.config.get('SPECIAL_OA_ID') and same_oa_count > 0:
                ret['oa_id_ok'] = False
            if ret['oa_id_ok']:
                ret['oa_id'] = oa_id

        # SQL
        sql_scripts_project = SQLScriptsProjectService.get_sql_scripts_project(project_id)
        if sql_scripts_project:
            # 目前先只配置发布前执行的SQL
            ret['sql_execute_config'] = dict()
            ret['sql_status'] = dict()
            for k, v in sql_scripts_project.get('sql_execution_config').items():
                if k != 'aut':
                    ret['sql_execute_config'][k] = dict()
                    ret['sql_execute_config'][k]['sql_before'] = v.get('execution_before')
                    ret['sql_execute_config'][k]['sql_after'] = v.get('execution_after')
                    ret['sql_status'][k] = sql_scripts_project.get('status').get(k)

        # Diamond
        diamond_before_count = diamond_collection.count({'project_id': str(project_id), 'm_type': 'before'})
        diamond_after_count = diamond_collection.count({'project_id': str(project_id), 'm_type': 'after'})
        if diamond_before_count > 0:
            ret['diamond_before'] = True
        else:
            ret['diamond_before'] = False
        if diamond_after_count > 0:
            ret['diamond_after'] = True
        else:
            ret['diamond_after'] = False

        # 电子保单
        dzbd_list = AppBranchService.list_app_branch(project_id, ['dzbd'])
        if dzbd_list:
            ret['dzbd'] = dict()
            dzbd = dzbd_list[0]
            submit_test = dzbd.get('submit_test')
            if submit_test:
                ret['dzbd'].update({'branch_revision': submit_test})
            # 进行预合并测试
            # 电子保单太大了，不预合并了
        ret['app_info'] = dict()

        # app应用
        app_list = AppBranchService.list_app_branch(project_id, ['app'])
        for one_app in app_list:
            one = dict()
            app_info = ApprepoService.get_app_info(one_app.get('app_id'))
            pre_server_amount = None
            if app_info and app_info.get('configs'):
                pre_server_amount = app_info.get('configs').get('pre_server_amount')
                if pre_server_amount is not None and Util.can_tune_to(pre_server_amount, int):
                    pre_server_amount = int(pre_server_amount)
            one.update({'pre_server_amount': pre_server_amount})
            submit_test = one_app.get('submit_test')
            pom_info = ApprepoService.get_info_from_pom(one_app.get('app_id'), branch_name=one_app.get('branch'),
                                                        directory='branch', svn_revision=submit_test,
                                                        git_commit_hash=submit_test)
            if submit_test and pom_info:
                one.update({'branch_revision': submit_test, 'artifact_id': pom_info.get('artifact_id'),
                            'ext_name': pom_info.get('ext_name'), 'no_snapshot': True,
                            'group_id': pom_info.get('group_id')
                            })
                for dv in pom_info.get('dependency_version'):
                    if dv.get('version') and dv.get('version').upper().find('SNAPSHOT') >= 0:
                        one.update({'no_snapshot': False})
                        break
                if not ExperiencedAppListService.check_has_experience(one_app.get('app_id')):
                    # 新应用
                    one.update({'first_time': True})

                pre_ecs_list = CMDBCore.query_arrange("pre", one_app.get('app_id'), "ecs")
                prd_ecs_list = CMDBCore.query_arrange("prd", one_app.get('app_id'), "ecs")
                pre_slb_list = CMDBCore.query_arrange("pre", one_app.get('app_id'), "slb")
                prd_slb_list = CMDBCore.query_arrange("prd", one_app.get('app_id'), "slb")

                f_type = one_app.get('f_type')
                fixed_pre_server = list()
                fixed_prd_server = list()
                if pre_ecs_list:
                    # 先查找并添加指定了相同f_type(如REALTIME, PRESELF)的服务器
                    for server in pre_ecs_list:
                        if server.get('f_type') == f_type:
                            fixed_pre_server.append(
                                {'res_id': server.get('res_id'), 'ip': server.get('ip'), 'port': server.get('port')})
                    # 如果没有匹配到指定f_type的服务器，就把所有服务器(f_type=None)都添加上
                    if not fixed_pre_server:
                        for server in pre_ecs_list:
                            fixed_pre_server.append({'res_id': server.get('res_id'), 'ip': server.get('ip'),
                                                     'port': server.get('port')})
                    # 预发必须有fixed server
                    one.update({'fixed_pre_server': fixed_pre_server})
                if prd_ecs_list:
                    # 先查找并添加指定了相同f_type(如REALTIME, PRESELF)的服务器
                    for server in prd_ecs_list:
                        if server.get('f_type') == f_type:
                            fixed_prd_server.append(
                                {'res_id': server.get('res_id'), 'ip': server.get('ip'), 'port': server.get('port')})
                    # 生产只有指定了f_type的时候才有fixed_server
                    one.update({'fixed_prd_server': fixed_prd_server})

                if not pre_ecs_list:
                    one.update({'pre_has_ecs': False})
                else:
                    one.update({'pre_has_ecs': True})
                if not prd_ecs_list:
                    one.update({'prd_has_ecs': False})
                else:
                    one.update({'prd_has_ecs': True})
                if not pre_slb_list:
                    one.update({'pre_has_slb': False})
                else:
                    one.update({'pre_has_slb': True})
                if not prd_slb_list:
                    one.update({'prd_has_slb': False})
                else:
                    one.update({'prd_has_slb': True})
                # 进行预合并测试
                pmr, pmd, pmi = ApprepoService.merge(one_app.get('app_id'), 'branch/{}'.format(one_app.get('branch')),
                                                     'trunk', svn_revision=submit_test, git_commit_hash=None, commit=False,
                                                     update_pom=False)
                one.update({'pre_merge_result': pmr})
                if one_app.get('app_id') in app.config.get("AUT_APP_ID_LIST"):
                    antx_check_result = PreCheckService.antx_config_precheck(project_id, one_app.get('app_id'), one_app.get('app_name'))
                    if not antx_check_result:
                        one.update({'aut_antx_config': False})
                    else:
                        one.update({'aut_antx_config': True})
            ret['app_info'][str(one_app.get('app_id'))] = one

        # share
        share_list = AppBranchService.list_app_branch(project_id, ['open', 'module'])
        for one_app in share_list:
            one = dict()
            submit_test = one_app.get('submit_test')
            pom_info = ApprepoService.get_info_from_pom(one_app.get('app_id'), branch_name=one_app.get('branch'),
                                                        directory='branch', svn_revision=submit_test,
                                                        git_commit_hash=submit_test)
            if submit_test and pom_info:
                one.update({'branch_revision': submit_test, 'artifact_id': pom_info.get('artifact_id'),
                            'ext_name': pom_info.get('ext_name'), 'no_snapshot': True,
                            'group_id': pom_info.get('group_id')
                            })
                for dv in pom_info.get('dependency_version'):
                    if dv.get('version') and dv.get('version').upper().find('SNAPSHOT') >= 0:
                        one.update({'no_snapshot': False})
                        break
                if not ExperiencedAppListService.check_has_experience(one_app.get('app_id')):
                    # 新应用
                    one.update({'first_time': True})
                    if pom_info.get('version') == '1.0.0':
                        one.update({'init_version_ok': True})
                    else:
                        one.update({'init_version_ok': False})
                # 进行预合并测试
                pmr, pmd, pmi = ApprepoService.merge(one_app.get('app_id'), 'branch/{}'.format(one_app.get('branch')),
                                                     'trunk', svn_revision=submit_test, git_commit_hash=None, commit=False,
                                                     update_pom=False)
                one.update({'pre_merge_result': pmr})
                if one_app.get('app_id') in app.config.get("AUT_APP_ID_LIST"):
                    antx_check_result = PreCheckService.antx_config_precheck(project_id, one_app.get('app_id'), one_app.get('app_name'))
                    if not antx_check_result:
                        one.update({'aut_antx_config': False})
                    else:
                        one.update({'aut_antx_config': True})
            ret['app_info'][str(one_app.get('app_id'))] = one
        return ret

    @staticmethod
    def pre_precheck(publish_id):
        flow_data = flow_data_collection.find_one({'flow_id': publish_id})
        if flow_data:
            project_id = flow_data.get('data').get('project_id')
            sql_status = flow_data.get('data').get('sql_status')
            if sql_status and (sql_status.get('pre') == 'not_pass' or sql_status.get('pre') == 'review'):
                return False, u"预发环境的SQL脚本审核未通过", []
            elif sql_status and sql_status.get('pre') == 'pass':
                flow_data_collection.update_one({'flow_id': publish_id}, {'$set': {'data.pre_sql_before_executed': False, 'data.pre_sql_after_executed': False}})

            diamond_list = DiamondService.list_project_diamond(project_id, env='pre')
            for diamond in diamond_list:
                hot_publish_id = HotPoolService.check_hot_diamond(diamond.get('data_id'), 'pre')
                if hot_publish_id:
                    return False, u"当前预发环境存在相同dataId[{}]的Diamond修改，存在冲突[{}]".format(diamond.get('data_id'), hot_publish_id), []
            ret = dict()
            for app_id, one_app in flow_data.get('data').get('app_info').items():
                fixed_pre_server = one_app.get('fixed_pre_server')
                pre_server_amount = one_app.get('pre_server_amount')
                free_pre_server = list()
                for server in fixed_pre_server:
                    if HotPoolService.check_free_pre_server(server.get('res_id'), server.get('port')) or "{}:{}".format(server.get('res_id'), server.get('port')) in app.config['PRE_PRECHECK_PASS_SERVER']:
                        free_pre_server.append(server)
                if pre_server_amount is not None and Util.can_tune_to(pre_server_amount, int):
                    # 指定了特定数量的服务器
                    pre_server_amount = int(pre_server_amount)
                    free_pre_server = free_pre_server[:pre_server_amount]
                    if len(free_pre_server) < pre_server_amount:
                        # 但是空余的服务器不够用了
                        return False, u"当前可用预发服务器不足，请稍后重试", []
                    else:
                        # 能够获取到特定数量的服务器，更新fixed服务器
                        flow_data_collection.update_one({'flow_id': publish_id}, {
                            "$set": {"data.app_info.{}.fixed_pre_server".format(app_id): free_pre_server}})
                        ret[app_id] = free_pre_server
                else:
                    # 需要占用所有fixed服务器
                    if len(free_pre_server) < len(fixed_pre_server):
                        # 但是有fixed服务器被占用了
                        return False, u"当前可用预发服务器不足，请稍后重试", []
                    else:
                        ret[app_id] = free_pre_server
            return True, u"获取发布服务器成功", ret
        return False, u"publish_id错误", []

    @staticmethod
    def prd_precheck(publish_id):
        flow_data = flow_data_collection.find_one({'flow_id': publish_id})
        if flow_data:
            sql_status = flow_data.get('data').get('sql_status')
            if sql_status and (sql_status.get('prd') == 'not_pass' or sql_status.get('prd') == 'review'):
                return False, u"生产环境的SQL脚本审核未通过"
            # 检查是否有定时发布冲突的应用
            scheduled_time = flow_data.get('data').get('scheduled_time')
            conflict_app_list_1 = list()
            conflict_app_list_2 = list()
            for app_id, one_app in flow_data.get('data').get('app_info').items():
                scheduled_prd_app = HotPoolService.get_latest_scheduled_prd_app(int(app_id))
                if scheduled_time:
                    if scheduled_prd_app and scheduled_time <= scheduled_prd_app.get('scheduled_time'):
                        # 当前单子是定时发布，生产区已经有相同应用的定时发布了，但是当前单子定时时间比已有的单子要早
                        conflict_app_list_1.append(one_app.get('name'))
                    else:
                        # 当前单子是定时发布，生产区没有相同应用的定时发布
                        # 当前单子是定时发布，生产区也有相同应用的定时发布，但是当前单子定时时间比已有的单子要晚
                        pass
                elif not scheduled_time and scheduled_prd_app:
                    # 当前单子不是定时发布, 生产区已经有相同应用的定时发布了, 就不能上生产了
                    conflict_app_list_2.append(one_app.get('name'))

            if flow_data.get('data').get('dzbd'):
                dzbd_app_id = flow_data.get('data').get('dzbd').get('app_id')
                scheduled_prd_app = HotPoolService.get_latest_scheduled_prd_app(dzbd_app_id)
                if scheduled_time:
                    if scheduled_prd_app and scheduled_time <= scheduled_prd_app.get('scheduled_time'):
                        # 当前单子是定时发布，生产区已经有相同应用的定时发布了，但是当前单子定时时间比已有的单子要早
                        conflict_app_list_1.append('dzbd')
                    else:
                        # 当前单子是定时发布，生产区没有相同应用的定时发布
                        # 当前单子是定时发布，生产区也有相同应用的定时发布，但是当前单子定时时间比已有的单子要晚
                        pass
                elif not scheduled_time and scheduled_prd_app:
                    # 当前单子不是定时发布, 生产区已经有相同应用的定时发布了, 就不能上生产了
                    conflict_app_list_2.append('dzbd')

            if conflict_app_list_1:
                return False, u"生产区已经有相同应用[{}]的定时发布了，且当前单子定时时间比已有的单子要早，造成冲突".format(','.join(conflict_app_list_1))

            if conflict_app_list_2:
                return False, u"生产区已经有相同应用[{}]的定时发布了, 无法直接上生产。请调整成定时发布，并将发布时间安排在已有的发布之后".format(','.join(conflict_app_list_2))

            project_id = flow_data.get('data').get('project_id')
            # 检查生产区是否已经有相同dataId的Diamond
            diamond_list = DiamondService.list_project_diamond(project_id, env='prd')
            for diamond in diamond_list:
                hot_publish_id = HotPoolService.check_hot_diamond(diamond.get('data_id'), 'prd')
                if hot_publish_id:
                    return False, u"当前生产发布区的发布单[{}]中存在相同dataId[{}]的Diamond修改,造成冲突".format(hot_publish_id, diamond.get('data_id'))
            # 检查生产区已经存在的相同的antx
            for app_id, one_app in flow_data.get('data').get('app_info').items():
                hot_app = HotPoolService.check_hot_prd_app(int(app_id))
                if hot_app:
                    source_project_id = hot_app.get('project_id')
                    result, info = AntxService.try_merge_project_prd_antx(source_project_id, project_id, int(app_id))
                    if not result:
                        return False, u"由于当前生产发布区的发布单{}中存在相同应用[{}],在合并antx配置时出现冲突，冲突项为:{}".format(hot_app.get('publish_id'), hot_app.get('app_name'), ",".join(info))
        return True, u"成功"

    @staticmethod
    def antx_config_precheck(project_id, app_id, app_name):
        add_keys = list()
        new_aut_antx = False
        antx_pre_config = AntxService.get_project_antx(project_id, app_id, 'pre')
        antx_aut_config = AntxService.get_project_antx(project_id, app_id, 'aut')

        if antx_pre_config and antx_aut_config:
            pre_content = antx_pre_config.get('content')
            aut_content = antx_aut_config.get('content')
        elif antx_pre_config:
            new_aut_antx = True
            pre_content = antx_pre_config.get('content')
            aut_content = AntxService.query_base_antx('aut', app_id)
        elif antx_aut_config:
            aut_content = antx_aut_config.get('content')
            pre_content = AntxService.query_base_antx('pre', app_id)
        else:
            new_aut_antx = True
            pre_content = AntxService.query_base_antx('pre', app_id)
            aut_content = AntxService.query_base_antx('aut', app_id)

        antx_pre_keys = list()
        antx_aut_keys = list()
        for e in pre_content:
            antx_pre_keys.append(e.get('k'))
        for e in aut_content:
            antx_aut_keys.append(e.get('k'))

        for key in antx_pre_keys:
            if not key in antx_aut_keys:
                add_keys.append(key)
        new_aut_content = list()
        aut_value_empty = False
        if len(add_keys):
            for key in add_keys:
                new_aut_content = aut_content
                new_aut_content.append({'k':key, 'v':''})
        else:
            for e in aut_content:
                if not e.get('v'):
                    if new_aut_antx:
                        app_env_list = list()
                        app_env_list.append({'app_id': app_id, 'app_name': app_name, 'env_list': ['aut']})
                        AntxService.create_project_antx(project_id, app_env_list)
                    return False

        if new_aut_antx and len(add_keys):
            app_env_list = list()
            app_env_list.append({'app_id': app_id, 'app_name': app_name, 'env_list': ['aut']})
            AntxService.create_project_antx(project_id, app_env_list)
            return False
        elif not new_aut_antx and len(add_keys):
            AntxService.mod_project_antx(project_id, app_id, 'aut', new_aut_content)
            return False
        return True