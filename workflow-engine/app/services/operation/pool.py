# -*- coding: utf8 -*-

import time
import requests
import pycurl
import datetime
from StringIO import StringIO
from bson.objectid import ObjectId

from functools import wraps

from app.out.saltstack import Saltstack
from app.out.cmdb_aliyun import CMDBAliyun
from app.out.zabbix import Zabbix
from app.out.monitor import Monitor
from app.out.jaguar import Jaguar
from app.out.idb import iDB
from app.services.nexus_service import NexusService
from app.services.operation.result_service import ResultService
from app.services.jenkins_service import JenkinsService
from app.services.apprepo_service import ApprepoService
from app.services.diamond_service import DiamondService
from app.services.publish.experienced_app_list_service import ExperiencedAppListService
from app.services.publish.precheck_service import PreCheckService
from app.services.publish.hot_pool_service import HotPoolService
from app.services.antx_service import AntxService
from app.services.project.sql_scripts_project_service import SQLScriptsProjectService
from app.services.framework.kafka_service import KafkaService
from app.mongodb import flow_data_collection, ci_project_collection, aut_ci_project_collection
from app.util import Util
from app import app, out_logger, root_logger

func_list = set()

result_callback_list = set()


def func_register():
    def decorator(f):
        func_list.add((f.__name__, f.__doc__))

        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def result_callback_register():
    def decorator(f):
        result_callback_list.add((f.__name__, f.__doc__))
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_func(funct_name):
    return eval("Pool." + funct_name)


class Pool(object):

    @staticmethod
    @func_register()
    def init_java_app(opid=None, op_type=None, step=None, company=None, env=None, ip=None, app_deploy_type=None, app_name=None, jdk_ver=None, jvm_size=None, new_size=None, perm_size=None, rpc_provider="hsf", **kwargs):
        """通过Salt初始化应用"""
        if app_deploy_type == 'web':
            port = kwargs.get('port')
            if port:
                start_port = int(port)
                shut_port = int(port) - 1
                result = Saltstack.app_init_war(company, env, ip, app_name=app_name, jdk_ver=jdk_ver,
                                                start_port=start_port, shut_port=shut_port, jvm_size=str(jvm_size) + "m",
                                                new_size=str(new_size) + "m", perm_size=str(perm_size) + "m", rpc_provider=rpc_provider)
                if result:
                    ResultService.add_result_detail(opid, op_type, step, content=u"init java web app ok")
                    return True
            ResultService.add_result_detail(opid, op_type, step, content=u"init java web app fail")
            return False
        elif app_deploy_type == 'jar':
            extra_options = kwargs.get('extra_options')
            result = Saltstack.app_init_jar(company, env, ip, app_name=app_name, jdk_ver=jdk_ver,
                                            extra_options=extra_options, jvm_size=str(jvm_size) + "m",
                                            new_size=str(new_size) + "m", perm_size=str(perm_size) + "m", rpc_provider=rpc_provider)
            if result:
                ResultService.add_result_detail(opid, op_type, step, content=u"init java jar app ok")
                return True
            ResultService.add_result_detail(opid, op_type, step, content=u"init java jar app fail")
            return False

    @staticmethod
    @func_register()
    def del_java_app(opid=None, op_type=None, step=None, company=None, env=None, ip=None, app_name=None, **kwargs):
        """通过Salt抹除应用"""
        result = Saltstack.del_app(company, env, ip, app_name=app_name)
        if result:
            ResultService.add_result_detail(opid, op_type, step, content=u"del app ok")
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"del app fail")
            return False

    @staticmethod
    @func_register()
    def archive_log(opid=None, op_type=None, step=None, company=None, env=None, ip=None, app_name=None, **kwargs):
        """调用Salt归档应用当天的日志"""
        result = Saltstack.archive_log(company, env, ip, app_name=app_name)
        if result:
            ResultService.add_result_detail(opid, op_type, step, content=u"archive log ok")
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"archive log fail")
            return False

    @staticmethod
    @func_register()
    def salt_restart_app(opid=None, op_type=None, step=None, company=None, env=None, ip=None, app_name=None, port=None, **kwargs):
        """通过Salt重启应用"""
        result = Saltstack.restart_app(company, env, ip, app_name=app_name, port=port)
        if result:
            ResultService.add_result_detail(opid, op_type, step, content=u"salt restart ok")
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"salt restart fail")
            return False

    @staticmethod
    @func_register()
    def health_check(opid=None, op_type=None, step=None, ip=None, port=None, check_url=None, **kwargs):
        """Web应用健康监测"""
        retry_count = 120
        result = False
        for i in range(retry_count):
            try:
                response = requests.get("http://{}:{}{}".format(ip, port, check_url), timeout=2)
                if response.status_code == 200 and 'OK' in response.content.upper():
                    result = True
                    break
            except Exception, e:
                pass
            time.sleep(5)
        if result:
            ResultService.add_result_detail(opid, op_type, step, content=u"health check ok")
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"health check fail")
            return False

    @staticmethod
    @func_register()
    def hsf_online(opid=None, op_type=None, step=None, ip=None, hsf_port=None, ext_name=None, **kwargs):
        """HSF服务上线"""
        try:
            if not Util.check_port_open(ip, hsf_port):
                ResultService.add_result_detail(opid, op_type, step, content=u"no hsf port({}) open".format(hsf_port))
                return True
            buffer = StringIO()
            c = pycurl.Curl()
            c.setopt(c.URL, 'http://{}:{}/hsf/online?k=hsf'.format(ip, hsf_port))
            c.setopt(c.TIMEOUT, 10)
            c.setopt(c.WRITEFUNCTION, buffer.write)
            c.perform()
            c.close()
            out_logger.info(buffer.getvalue())
            if "register" in buffer.getvalue():
                ResultService.add_result_detail(opid, op_type, step, content=u"hsf online ok: \n{}".format(buffer.getvalue()))
                return True
            else:
                ResultService.add_result_detail(opid, op_type, step, content=u"hsf online fail: \n{}".format(buffer.getvalue()))
                if ext_name == 'jar':
                    return True
                else:
                    return False
        except Exception, e:
            root_logger.exception("hsf_online error: %s", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"hsf online fail")
            if ext_name == 'jar':
                return True
            else:
                return False

    @staticmethod
    @func_register()
    def hsf_offline(opid=None, op_type=None, step=None, ip=None, hsf_port=None, hsf_timeout=120, **kwargs):
        """HSF服务下线"""
        try:
            if not Util.check_port_open(ip, hsf_port):
                ResultService.add_result_detail(opid, op_type, step, content=u"no hsf port({}) open".format(hsf_port))
                return True
            buffer = StringIO()
            c = pycurl.Curl()
            c.setopt(c.URL, 'http://{}:{}/hsf/offline?k=hsf'.format(ip, hsf_port))
            c.setopt(c.TIMEOUT, hsf_timeout)
            c.setopt(c.WRITEFUNCTION, buffer.write)
            c.perform()
            c.close()
            out_logger.info(buffer.getvalue())
            if "unregistered" in buffer.getvalue():
                ResultService.add_result_detail(opid, op_type, step, content=u"hsf offline ok: \n{}".format(buffer.getvalue()))
                return True
            else:
                ResultService.add_result_detail(opid, op_type, step, content=u"hsf offline fail: \n{}".format(buffer.getvalue()))
                # 忽略HSF下线失败
                return True
        except Exception, e:
            root_logger.exception("hsf_offline error: %s", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"hsf offline fail")

            return True

    @staticmethod
    @func_register()
    def cp_tag_release(opid=None, op_type=None, step=None, app_id=None, publish_id=None, env=None, **kwargs):
        """从Tag拉取Release"""
        try:
            release_name = "{}_{}_{}".format(env, publish_id, datetime.datetime.now().strftime('%y%m%d%H%M'))
            result, info = ApprepoService.create_branch(app_id, release_name, directory='release', source='tag')
            if result:
                ResultService.add_result_detail(opid, op_type, step, content=u"cp tag to release ok: \n{}".format(info))
                return {'release_name': release_name}
            else:
                ResultService.add_result_detail(opid, op_type, step, content=u"cp tag to release fail: \n{}".format(info))
                flow_data_collection.update_one({'flow_id': publish_id},
                                                {"$set": {"data.app_info.{}.{}_built".format(app_id, env): False}})
                return False
        except Exception, e:
            root_logger.exception("cp_tag_release error: %s", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"cp tag to release fail")
            flow_data_collection.update_one({'flow_id': publish_id},
                                            {"$set": {"data.app_info.{}.{}_built".format(app_id, env): False}})
            return False

    @staticmethod
    @func_register()
    def merge_branch_release(opid=None, op_type=None, step=None, app_id=None, branch_name=None, release_name=None, branch_revision=None, flow_id=None, project_id=None, env=None, **kwargs):
        """合并Branch到预发Release"""
        try:
            result, data, info = ApprepoService.merge(app_id, source="branch/{}".format(branch_name), target="release/{}".format(release_name), svn_revision=branch_revision, commit=True, update_pom=True, duang_project_id=project_id, update_parent_version=True, update_self_version=True, accept='theirs')
            if result:
                mongo_result = flow_data_collection.update_one({'flow_id': flow_id}, {"$set": {"data.app_info.{}.pre_release_name".format(app_id): release_name}})
                if mongo_result.modified_count >= 1:
                    ResultService.add_result_detail(opid, op_type, step, content=u"merge branch release ok: \n{}".format(info))
                    return {'release_revision': data}
                else:
                    ResultService.add_result_detail(opid, op_type, step, content=u"merge branch release fail: \n{}\n{}".format("flow data update error", mongo_result.raw_result))
                    flow_data_collection.update_one({'flow_id': flow_id},
                                                    {"$set": {"data.app_info.{}.{}_built".format(app_id, env): False}})
                    return False
            else:
                ResultService.add_result_detail(opid, op_type, step, content=u"merge branch release fail: \n{}".format(info))
                flow_data_collection.update_one({'flow_id': flow_id},
                                                {"$set": {"data.app_info.{}.{}_built".format(app_id, env): False}})
                return False
        except Exception, e:
            root_logger.exception("merge_branch_release error: %s", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"merge branch release fail")
            flow_data_collection.update_one({'flow_id': flow_id},
                                            {"$set": {"data.app_info.{}.{}_built".format(app_id, env): False}})
            return False

    @staticmethod
    @func_register()
    def merge_release_tag(opid=None, op_type=None, step=None, app_id=None, pre_release_name=None, flow_id=None, project_id=None, **kwargs):
        """合并预发Release到Tag，并记录tag的revision"""
        try:
            result, data, info = ApprepoService.merge(app_id, source='release/{}'.format(pre_release_name), target="tag", commit=True, update_pom=True, duang_project_id=project_id, update_parent_version=True, update_self_version=False, accept='theirs')
            if result:
                mongo_result = flow_data_collection.update_one({'flow_id': flow_id}, {"$set": {"data.app_info.{}.tag_revision".format(app_id): data}})
                if mongo_result.modified_count >= 1:
                    ResultService.add_result_detail(opid, op_type, step, content=u"merge release tag ok: \n{}".format(info))
                    return {'tag_revision': data, 'up_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}
                else:
                    ResultService.add_result_detail(opid, op_type, step, content=u"merge release tag fail: \n{}\n{}".format("flow data update error", mongo_result.raw_result))
                    return False
            else:
                ResultService.add_result_detail(opid, op_type, step, content=u"merge release tag fail: \n{}".format(info))
                return False
        except Exception, e:
            root_logger.exception("merge_release_tag error: %s", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"merge release tag fail")
            return False

    @staticmethod
    @func_register()
    def build_release(opid=None, op_type=None, step=None, env=None, project_id=None, publish_id=None, app_id=None, release_name=None, release_revision=None, ext_name=None, has_first_time=None, **kwargs):
        """打包Release"""
        try:
            if env == 'aut' and app_id not in app.config['AUT_APP_ID_LIST']:
                ResultService.add_result_detail(opid, op_type, step, content=u"don't need to build aut, pass")
                return True

            app_info = ApprepoService.get_app_info(app_id)
            if app_info and app_info.get('vcs_project').get('full_url'):
                svn_path = '{}/release/{}'.format(app_info.get('vcs_project').get('full_url'), release_name)
                job_name, build_number = JenkinsService.build_java(env, project_id, publish_id, app_id, svn_path, release_revision, ext_name, has_first_time)
                if job_name and build_number:
                    ResultService.add_result_detail(opid, op_type, step,
                                                    callback="JenkinsService.get_build_result('{}', '{}', {})".
                                                    format(env, job_name, build_number))
                    result = None
                    retry_count = 120
                    for i in range(retry_count):
                        status = JenkinsService.get_job_status(env, job_name, build_number)
                        if status and not status.get('building'):
                            result = status.get('result')
                            break
                        time.sleep(5)
                    if result == 'SUCCESS':
                        flow_data_collection.update_one({'flow_id': publish_id}, {"$set": {"data.app_info.{}.{}_built".format(app_id, env): True}})
                        if env == 'pre':
                            # 打完预发的包继续打AUT的包
                            return {'env': 'aut'}
                        else:
                            return True
                    elif env == 'aut':
                        # 自动化测试环境的打包忽略结果
                        return True
            flow_data_collection.update_one({'flow_id': publish_id}, {"$set": {"data.app_info.{}.{}_built".format(app_id, env): False}})
            return False
        except Exception, e:
            root_logger.exception("build_release error: %s", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"build release fail")
            flow_data_collection.update_one({'flow_id': publish_id},
                                            {"$set": {"data.app_info.{}.{}_built".format(app_id, env): False}})
            return False

    @staticmethod
    @func_register()
    def cp_trunk_release(opid=None, op_type=None, step=None, app_id=None, publish_id=None, env=None, **kwargs):
        """从Trunk拉取Release"""
        try:
            release_name = "{}_{}_{}".format(env, publish_id, datetime.datetime.now().strftime('%y%m%d%H%M'))
            result, info = ApprepoService.create_branch(app_id, release_name, directory='release', source='trunk')
            if result:
                ResultService.add_result_detail(opid, op_type, step, content=u"cp trunk to release ok: \n{}".format(info))
                return {'release_name': release_name}
            else:
                ResultService.add_result_detail(opid, op_type, step, content=u"cp trunk to release fail: \n{}".format(info))
                flow_data_collection.update_one({'flow_id': publish_id},
                                                {"$set": {"data.app_info.{}.{}_built".format(app_id, env): False}})
                return False
        except Exception, e:
            root_logger.exception("cp_trunk_release error: %s", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"cp trunk to release fail")
            flow_data_collection.update_one({'flow_id': publish_id},
                                            {"$set": {"data.app_info.{}.{}_built".format(app_id, env): False}})
            return False

    @staticmethod
    @func_register()
    def merge_tag_release(opid=None, op_type=None, step=None, app_id=None, release_name=None, tag_revision=None, app_type=None, project_id=None, artifact_id=None, flow_id=None, env=None, **kwargs):
        """合并Tag到生产Release， 同时更新share类型应用的version"""
        try:
            if app_type in ['module', 'open']:
                NexusService.preallocate_share_version(artifact_id, project_id)
                result, data, info = ApprepoService.merge(app_id, source='tag', target="release/{}".format(release_name), svn_revision=tag_revision, commit=True, update_pom=True, duang_project_id=project_id, update_parent_version=True, update_self_version=True, accept='theirs')
            else:
                result, data, info = ApprepoService.merge(app_id, source='tag', target="release/{}".format(release_name), svn_revision=tag_revision, commit=True, update_pom=True, duang_project_id=project_id, update_parent_version=True, update_self_version=False, accept='theirs')
            if result:
                mongo_result = flow_data_collection.update_one({'flow_id': flow_id}, {"$set": {"data.app_info.{}.prd_release_name".format(app_id): release_name}})
                if mongo_result.modified_count >= 1:
                    ResultService.add_result_detail(opid, op_type, step, content=u"merge tag release ok: \n{}".format(info))
                    return {'release_revision': data}
                else:
                    ResultService.add_result_detail(opid, op_type, step, content=u"merge tag release fail: \n{}\n{}".format("flow data update error", mongo_result.raw_result))
                    flow_data_collection.update_one({'flow_id': flow_id},
                                                    {"$set": {"data.app_info.{}.{}_built".format(app_id, env): False}})
                    return False
            else:
                ResultService.add_result_detail(opid, op_type, step, content=u"merge tag release fail: \n{}".format(info))
                flow_data_collection.update_one({'flow_id': flow_id},
                                                {"$set": {"data.app_info.{}.{}_built".format(app_id, env): False}})
                return False
        except Exception, e:
            root_logger.exception("merge_tag_release error: %s", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"merge tag release fail")
            flow_data_collection.update_one({'flow_id': flow_id},
                                            {"$set": {"data.app_info.{}.{}_built".format(app_id, env): False}})
            return False

    @staticmethod
    @func_register()
    def merge_release_trunk(opid=None, op_type=None, step=None, app_id=None, prd_release_name=None, app_name=None, app_type=None, project_id=None, publish_id=None, **kwargs):
        """合并生产Release到Trunk"""
        try:
            result, data, info = ApprepoService.merge(app_id, source='release/{}'.format(prd_release_name), target="trunk", commit=True, update_pom=False, accept='theirs')
            if result:
                # TODO: 更新所有生产区的单子中相同应用而且tag_revision低的应用的commited为true
                ExperiencedAppListService.add_experience(app_id, app_name, app_type, project_id, publish_id)
                ResultService.add_result_detail(opid, op_type, step, content=u"merge release trunk ok: \n{}".format(info))
                return True
            else:
                ResultService.add_result_detail(opid, op_type, step, content=u"merge release trunk fail: \n{}".format(info))
                return False
        except Exception, e:
            root_logger.exception("merge_release_trunk error: %s", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"merge release trunk fail")
            return False

    @staticmethod
    @func_register()
    def slb_block(opid=None, op_type=None, step=None, ecs_id=None, slb_id=None, **kwargs):
        if ecs_id and slb_id:
            result = CMDBAliyun.slb_action('rm', ecs_id, slb_id)
            if result:
                ResultService.add_result_detail(opid, op_type, step, content=u"slb block ok")
                return True
            else:
                ResultService.add_result_detail(opid, op_type, step, content=u"slb block fail")
                return False
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"no slb, pass")
            return True

    @staticmethod
    @func_register()
    def slb_unblock(opid=None, op_type=None, step=None, ecs_id=None, slb_id=None, **kwargs):
        if ecs_id and slb_id:
            result = CMDBAliyun.slb_action('add', ecs_id, slb_id)
            if result:
                ResultService.add_result_detail(opid, op_type, step, content=u"slb unblock ok")
                return True
            else:
                ResultService.add_result_detail(opid, op_type, step, content=u"slb unblock fail")
                return False
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"no slb, pass")
            return True

    @staticmethod
    @func_register()
    def start_health_check(opid=None, op_type=None, step=None, app_name=None, ip=None, port=None, check_url=None, app_dpmt_name=None, app_owner_list=None, app_contacts_list=None, **kwargs):
        try:
            za_result = False
            # 获取机器信息
            hostid = Zabbix.query_host_info(ip)
            if not hostid:
                app_dpmt_id = Zabbix.query_app_group_id(app_dpmt_name)
                if app_dpmt_id:
                    hostid = Zabbix.create_host(ip, app_dpmt_id)
                if hostid:
                    za_result = Zabbix.create_httptest(ip, str(port), hostid, check_url)
            else:
                # 根据hostid获取httptest信息
                httptest_id = Zabbix.query_httptest_info(hostid, str(port))
                # 启停监控
                if httptest_id:
                    za_result = Zabbix.httptest_update(httptest_id, 0)
                else:
                    za_result = Zabbix.create_httptest(ip, str(port), hostid, check_url)
            mon_result = Monitor.monitor_start(ip, str(port), check_url, app_name, app_owner_list, app_contacts_list)
            if za_result and mon_result:
                ResultService.add_result_detail(opid, op_type, step, content=u"start health check ok")
                return True
            else:
                ResultService.add_result_detail(opid, op_type, step, content=u"start health check fail(zabbix: {}, monitor: {})".format(str(za_result), str(mon_result)))
                return False
        except Exception, e:
            out_logger.exception("start_health_check exception", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"start health check exception")
            return False

    @staticmethod
    @func_register()
    def stop_health_check(opid=None, op_type=None, step=None, ip=None, port=None, app_name=None, check_url=None, **kwargs):
        try:
            # 获取机器信息
            hostid = Zabbix.query_host_info(ip)
            if not hostid:
                za_result = True
            else:
                # 根据hostid获取httptest信息
                httptest_id = Zabbix.query_httptest_info(hostid, str(port))
                # 启停监控
                if httptest_id:
                    za_result = Zabbix.httptest_update(httptest_id, 1)
                else:
                    za_result = True
            mon_result = Monitor.monitor_stop(ip, str(port), app_name, check_url)
            if za_result and mon_result:
                ResultService.add_result_detail(opid, op_type, step, content=u"stop health check ok")
                return True
            else:
                ResultService.add_result_detail(opid, op_type, step, content=u"stop health check fail(zabbix: {}, monitor: {})".format(str(za_result), str(mon_result)))
                return False
        except Exception, e:
            out_logger.exception("stop_health_check exception", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"stop health check exception")
            return False

    @staticmethod
    @func_register()
    def stop_java_app(opid=None, op_type=None, step=None, company=None, env=None, ip=None, app_name=None, port=None, **kwargs):
        """通过Salt停止应用"""
        result = Saltstack.stop_app(company, env, ip, app_name=app_name, port=port)
        if result:
            ResultService.add_result_detail(opid, op_type, step, content=u"salt stop ok")
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"salt stop fail")
            return False

    @staticmethod
    @func_register()
    def clean_before_deploy(opid=None, op_type=None, step=None, company=None, env=None, ip=None, app_name=None, **kwargs):
        """发布前通过Salt清理应用环境"""
        result = Saltstack.clean_env(company, env, ip, app_name=app_name)
        if result:
            ResultService.add_result_detail(opid, op_type, step, content=u"salt clean env ok")
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"salt clean env fail")
            return False

    @staticmethod
    @func_register()
    def upload_package(opid=None, op_type=None, step=None, company=None, env=None, ip=None, app_name=None, pack_serv_url=None, **kwargs):
        """通过Salt上传应用包"""
        result = Saltstack.upload_package(company, env, ip, app_name=app_name,
                                          pack_serv_url=pack_serv_url, need_uncomp=False, unzip_dir=None)
        if result:
            ResultService.add_result_detail(opid, op_type, step, content=u"salt upload package ok")
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"salt upload package fail")
            return False

    @staticmethod
    @func_register()
    def start_java_app(opid=None, op_type=None, step=None, company=None, env=None, ip=None, app_name=None, port=None, **kwargs):
        """通过Salt启动应用"""
        result = Saltstack.start_app(company, env, ip, app_name=app_name, port=port)
        if result:
            ResultService.add_result_detail(opid, op_type, step, content=u"salt start ok")
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"salt start fail")
            return False

    @staticmethod
    @func_register()
    def commit_project_diamond(opid=None, op_type=None, step=None, project_id=None, env=None, m_type=None, **kwargs):
        if project_id and env and m_type:
            result, info = DiamondService.commit_project_diamond(project_id, env, m_type)
            if result:
                ResultService.add_result_detail(opid, op_type, step, content=info)
                return True
            else:
                ResultService.add_result_detail(opid, op_type, step, content=info)
                return False

    @staticmethod
    @func_register()
    def dzbd_publish(opid=None, op_type=None, step=None, env=None, dzbd_server=None, branch_name=None, vcs_full_url=None, svn_revision=None, dir_path=None, user=None, password=None, **kwargs):
        result = None
        if env == 'pre':
            # 预发的电子保单是在测试环境的
            result = Saltstack.dzbd_pre_publish('ZA', 'test', dzbd_server, branch="{}/branch/{}".format(vcs_full_url, branch_name), svn_revision=svn_revision, dir_path=dir_path, user=user, password=password)
        elif env == 'prd':
            result = Saltstack.dzbd_prd_publish('ZA', env, dzbd_server, svn_revision=svn_revision, dir_path=dir_path, user=user, password=password)
        if result:
            ResultService.add_result_detail(opid, op_type, step, content=u"dzbd publish success")
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"dzbd publish fail")
            return False

    @staticmethod
    @func_register()
    def dzbd_rollback(opid=None, op_type=None, step=None, env=None, dzbd_server=None, user=None, password=None, **kwargs):
        result = list()
        if env == 'pre':
            for s in dzbd_server:
                # 预发的电子保单是在测试环境的
                ret = Saltstack.dzbd_pre_rollback('ZA', 'test', dzbd_server, user=user, password=password)
                result.append({'server': s, 'result': ret})
        elif env == 'prd':
            for s in dzbd_server:
                ret = Saltstack.dzbd_prd_rollback('ZA', env, dzbd_server, user=user, password=password)
                result.append({'server': s, 'result': ret})
        if result and not (False in [e.get('result') for e in result]):
            ResultService.add_result_detail(opid, op_type, step, content=u"dzbd rollback success: {}".format(result))
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"dzbd rollback fail: {}".format(result))
            return False

    @staticmethod
    @func_register()
    def merge_branch_tag(opid=None, op_type=None, step=None, app_id=None, branch_name=None, branch_revision=None, flow_id=None, **kwargs):
        """合并Branch到Tag，并记录tag的revision，用于电子保单"""
        try:
            result, data, info = ApprepoService.merge(app_id, source='branch/{}'.format(branch_name),
                                                      target="tag", svn_revision=branch_revision, commit=True,
                                                      update_pom=False, accept='theirs')
            if result:
                if app_id == app.config['DZBD_APP_ID']:
                    mongo_result = flow_data_collection.update_one({'flow_id': flow_id}, {"$set": {"data.dzbd.tag_revision": data}})
                else:
                    mongo_result = flow_data_collection.update_one({'flow_id': flow_id}, {"$set": {"data.app_info.{}.tag_revision".format(app_id): data}})
                if mongo_result.modified_count >= 1:
                    ResultService.add_result_detail(opid, op_type, step, content=u"merge branch tag ok: \n{}".format(info))
                    return {'tag_revision': data, 'up_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}
                else:
                    ResultService.add_result_detail(opid, op_type, step, content=u"merge branch tag fail: \n{}\n{}".format(u"flow data update error", mongo_result.raw_result))
                    return False
            else:
                ResultService.add_result_detail(opid, op_type, step, content=u"merge branch tag fail: \n{}".format(info))
                return False
        except Exception, e:
            root_logger.exception("merge_branch_tag error: %s", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"merge branch tag fail")
            return False

    @staticmethod
    @func_register()
    def merge_tag_trunk(opid=None, op_type=None, step=None, app_id=None, tag_revision=None, **kwargs):
        """合并Tag到Trunk，用于电子保单"""
        try:
            result, data, info = ApprepoService.merge(app_id, source='tag', target="trunk", svn_revision=tag_revision,
                                                      commit=True, update_pom=False, accept='theirs')
            if result:
                ResultService.add_result_detail(opid, op_type, step, content=u"merge tag trunk ok: \n{}".format(info))
                return True
            else:
                ResultService.add_result_detail(opid, op_type, step, content=u"merge tag trunk fail: \n{}".format(info))
                return False
        except Exception, e:
            root_logger.exception("merge_tag_trunk error: %s", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"merge tag trunk fail")
            return False

    @staticmethod
    @func_register()
    def deploy_parent(opid=None, op_type=None, step=None, app_type=None, project_id=None, **kwargs):
        if app_type in ['module', 'open']:
            NexusService.preallocate_parent_version(project_id)
            result, info = NexusService.upload_parent_pom(project_id=project_id)
            if result:
                # parent实际提交后，再提交对外版本
                NexusService.commit_version_by_project_id(project_id)
                ResultService.add_result_detail(opid, op_type, step, content=info)
                return True
            else:
                ResultService.add_result_detail(opid, op_type, step, content=info)
                return False
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"type is not share, pass")
            return True

    @staticmethod
    @func_register()
    def pre_precheck(opid=None, op_type=None, step=None, publish_id=None, **kwargs):
        result, info, data = PreCheckService.pre_precheck(publish_id)
        if result:
            ResultService.add_result_detail(opid, op_type, step, content=info)
            return {"free_pre_server_dict": data}
        else:
            ResultService.add_result_detail(opid, op_type, step, content=info)
            return False

    @staticmethod
    @func_register()
    def allocate_pre_server(opid=None, op_type=None, step=None, publish_id=None, free_pre_server_dict=None, **kwargs):
        if free_pre_server_dict:
            for app_id, free_pre_server in free_pre_server_dict.items():
                for server in free_pre_server:
                    result = HotPoolService.allocate_pre_server(server.get('res_id'), server.get('ip'), server.get('port'), int(app_id), publish_id)
                    if not result:
                        # 占用失败，放弃
                        HotPoolService.release_pre_server(publish_id)
                        ResultService.add_result_detail(opid, op_type, step, content=u"allocate pre server fail({})".format(server))
                        return False
        ResultService.add_result_detail(opid, op_type, step, content=u"allocate pre server success")
        return True

    @staticmethod
    @func_register()
    def release_pre_server(opid=None, op_type=None, step=None, publish_id=None, **kwargs):
        """释放预发服务器"""
        result = HotPoolService.release_pre_server(publish_id)
        if result:
            ResultService.add_result_detail(opid, op_type, step, content=u"release success")
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"release fail")
            return False

    @staticmethod
    @func_register()
    def rollback_pre_config(opid=None, op_type=None, step=None, publish_id=None, project_id=None, **kwargs):
        result_before, info_before = DiamondService.rollback_project_diamond(project_id, 'pre', 'before')
        result_after, info_after = DiamondService.rollback_project_diamond(project_id, 'pre', 'after')
        if not result_before or not result_after:
            ResultService.add_result_detail(opid, op_type, step, content=u"rollback diamond error\nmtype before:{};\nmtype after: {}".format(info_before, info_after))
            # 回滚失败也继续处理下去
            return True
        ResultService.add_result_detail(opid, op_type, step, content=u"roll back config success")
        return True

    @staticmethod
    @func_register()
    def prd_precheck(opid=None, op_type=None, step=None, publish_id=None, **kwargs):
        result, info = PreCheckService.prd_precheck(publish_id)
        if result:
            ResultService.add_result_detail(opid, op_type, step, content=info)
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=info)
            return False

    @staticmethod
    @func_register()
    def merge_prd_antx(opid=None, op_type=None, step=None, app_id=None, project_id=None, publish_id=None, app_name=None, tag_revision=None, **kwargs):
        one = HotPoolService.check_hot_prd_app(int(app_id))
        if one:
            source_project_id = one.get('project_id')
            AntxService.merge_project_prd_antx(source_project_id, project_id, app_id)
            ResultService.add_result_detail(opid, op_type, step, content=u"antx merge success")
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"don't need to merge, pass")
            return True

    @staticmethod
    @func_register()
    def allocate_pre_diamond(opid=None, op_type=None, step=None, project_id=None, publish_id=None, **kwargs):
        diamond_list = DiamondService.list_project_diamond(project_id, env='pre')
        if diamond_list:
            for diamond in diamond_list:
                HotPoolService.allocate_diamond(diamond.get('data_id'), 'pre', publish_id)
            ResultService.add_result_detail(opid, op_type, step, content=u"allocate pre diamond success[{}]".format(','.join([d.get('data_id') for d in diamond_list])))
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"no diamond, pass")
        return True

    @staticmethod
    @func_register()
    def release_pre_diamond(opid=None, op_type=None, step=None, publish_id=None, **kwargs):
        HotPoolService.releases_diamond(publish_id, 'pre')
        ResultService.add_result_detail(opid, op_type, step, content=u"release pre diamond success")
        return True

    @staticmethod
    @func_register()
    def allocate_prd_diamond(opid=None, op_type=None, step=None, project_id=None, publish_id=None, **kwargs):
        diamond_list = DiamondService.list_project_diamond(project_id, env='prd')
        if diamond_list:
            for diamond in diamond_list:
                HotPoolService.allocate_diamond(diamond.get('data_id'), 'prd', publish_id)
            ResultService.add_result_detail(opid, op_type, step, content=u"allocate prd diamond success[{}]".format(
                ','.join([d.get('data_id') for d in diamond_list])))
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"no diamond, pass")
        return True

    @staticmethod
    @func_register()
    def release_prd_diamond(opid=None, op_type=None, step=None, publish_id=None, **kwargs):
        HotPoolService.releases_diamond(publish_id, 'prd')
        ResultService.add_result_detail(opid, op_type, step, content=u"release prd diamond success")
        return True

    @staticmethod
    @func_register()
    def commit_pre_antx(opid=None, op_type=None, step=None, project_id=None, **kwargs):
        """提交预发ANTX配置"""
        AntxService.commit_project_antx(project_id, 'pre')
        ResultService.add_result_detail(opid, op_type, step, content=u"commit pre antx success")
        return True

    @staticmethod
    @func_register()
    def commit_aut_antx(opid=None, op_type=None, step=None, project_id=None, **kwargs):
        """提交自动化测试ANTX配置"""
        AntxService.commit_project_antx(project_id, 'aut')
        ResultService.add_result_detail(opid, op_type, step, content=u"commit aut antx success")
        return True

    @staticmethod
    @func_register()
    def commit_prd_antx(opid=None, op_type=None, step=None, project_id=None, **kwargs):
        """提交生产ANTX配置"""
        AntxService.commit_project_antx(project_id, 'prd')
        ResultService.add_result_detail(opid, op_type, step, content=u"commit prd antx success")
        return True

    @staticmethod
    @func_register()
    def add_prd_app(opid=None, op_type=None, step=None, app_id=None, publish_id=None, project_id=None, app_name=None, tag_revision=None, up_time=None, scheduled_time=None, ready=False, **kwargs):
        scheduled_time = datetime.datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M') if scheduled_time else None
        HotPoolService.add_prd_app(app_id, publish_id, project_id, app_name, tag_revision, up_time, scheduled_time, ready)
        ResultService.add_result_detail(opid, op_type, step, content=u"add prd app success")
        return True

    @staticmethod
    @func_register()
    def release_prd_app(opid=None, op_type=None, step=None, publish_id=None, **kwargs):
        HotPoolService.release_prd_app(publish_id)
        ResultService.add_result_detail(opid, op_type, step, content=u"release prd app success")
        return True

    @staticmethod
    @func_register()
    def ci_build(opid=None, op_type=None, step=None, env=None, app_id=None, app_name=None, branch_name=None, jdk_version=None, vcs_type=None, vcs_full_url=None, **kwargs):
        """持续集成打包"""
        try:
            job_name, build_number = JenkinsService.build_ci_java(env, app_name, branch_name, jdk_version, vcs_type, vcs_full_url)
            if job_name and build_number:
                ResultService.add_result_detail(opid, op_type, step,
                                                callback="JenkinsService.get_build_result('{}', '{}', {})".
                                                format(env, job_name, build_number))
                result = None
                retry_count = 120
                for i in range(retry_count):
                    status = JenkinsService.get_job_status(env, job_name, build_number)
                    if status and not status.get('building'):
                        result = status.get('result')
                        break
                    time.sleep(5)
                if result == 'SUCCESS':
                    ci_project_collection.update_one({'app_id': app_id, 'branch': branch_name}, {'$set': {'status': 'ready'}})
                    return True
            ci_project_collection.update_one({'app_id': app_id, 'branch': branch_name}, {'$set': {'status': 'ready'}})
            return False
        except Exception, e:
            root_logger.exception("ci_build error: %s", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"ci build fail")
            ci_project_collection.update_one({'app_id': app_id, 'branch': branch_name}, {'$set': {'status': 'ready'}})
            return False

    @staticmethod
    @func_register()
    def aut_ci_build(opid=None, op_type=None, step=None, env=None, project_id=None, publish_id=None, app_id=None, branch_name=None, jdk_version=None, vcs_type=None, vcs_full_url=None, **kwargs):
        """自动化测试打包"""
        try:
            job_name, build_number = JenkinsService.build_aut_ci_java(env, project_id, publish_id, app_id, branch_name, jdk_version, vcs_type, vcs_full_url)
            if job_name and build_number:
                ResultService.add_result_detail(opid, op_type, step,
                                                callback="JenkinsService.get_build_result('{}', '{}', {})".
                                                format(env, job_name, build_number))
                result = None
                retry_count = 120
                for i in range(retry_count):
                    status = JenkinsService.get_job_status(env, job_name, build_number)
                    if status and not status.get('building'):
                        result = status.get('result')
                        break
                    time.sleep(5)
                if result == 'SUCCESS':
                    aut_ci_project_collection.update_one({'_id': ObjectId(project_id)}, {'$set': {'status': 'ready'}})
                    return True
            aut_ci_project_collection.update_one({'_id': ObjectId(project_id)}, {'$set': {'status': 'ready'}})
            return False
        except Exception, e:
            root_logger.exception("aut_ci_build error: %s", e)
            ResultService.add_result_detail(opid, op_type, step, content=u"aut ci build fail")
            aut_ci_project_collection.update_one({'_id': ObjectId(project_id)}, {'$set': {'status': 'ready'}})
            return False

    @staticmethod
    @func_register()
    def jaguar_check(opid=None, op_type=None, step=None, **kwargs):
        """美洲豹生产打包前检查"""
        result = Jaguar.check_working_status()
        if result is not None and result:
            ResultService.add_result_detail(opid, op_type, step, content=u"没有正在执行的美洲豹报文，可以发布")
            return True
        elif result is not None and not result:
            ResultService.add_result_detail(opid, op_type, step, content=u"存在正在执行的美洲豹报文，请稍后重试")
            return False
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"查询美洲豹报文执行情况失败")
            return False

    @staticmethod
    @func_register()
    def release_preallocate_version(opid=None, op_type=None, step=None, project_id=None, **kwargs):
        """释放项目预占的版本"""
        result = NexusService.release_version_by_project_id(project_id)
        if result:
            ResultService.add_result_detail(opid, op_type, step, content=u"释放项目预占的版本成功")
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=u"释放项目预占的版本失败")
            return False

    @staticmethod
    @func_register()
    def pre_share_allocate(opid=None, op_type=None, step=None, project_id=None, artifact_id=None, app_type=None, first_time=None, **kwargs):
        """预发本地Share版本准备"""
        if app_type == 'app' or not first_time:
            ResultService.add_result_detail(opid, op_type, step, content=u"无需准备预发本地Share版本, 跳过")
            return True
        NexusService.preallocate_share_version(artifact_id, project_id)
        ResultService.add_result_detail(opid, op_type, step, content=u"准备预发本地Share版本成功")
        return True

    @staticmethod
    @func_register()
    def pre_parent_allocate(opid=None, op_type=None, step=None, project_id=None, **kwargs):
        """预发本地Parent准备"""
        NexusService.preallocate_parent_version(project_id)
        ResultService.add_result_detail(opid, op_type, step, content=u"准备预发本地Parent成功")
        return True

    @staticmethod
    @func_register()
    def wait_app_build(opid=None, op_type=None, step=None, publish_id=None, env=None, **kwargs):
        """等待应用打包完成"""
        retry_count = 240
        for i in range(retry_count):
            flag = list()
            flow_data = flow_data_collection.find_one({'flow_id': publish_id})
            for app_id, app_info in flow_data.get('data').get('app_info').items():
                if app_info.get('skip'):
                    # 跳过
                    continue
                if app_info.get('{}_built'.format(env)) is None:
                    # 还未执行，跳过
                    flag.append(None)
                elif app_info.get('{}_built'.format(env)):
                    # 成功了
                    flag.append(True)
                elif not app_info.get('{}_built'.format(env)):
                    # 失败了
                    flag.append(False)

            if False in flag:
                # 有失败，结束等待
                ResultService.add_result_detail(opid, op_type, step, content=u"有打包失败")
                return False
            elif None in flag:
                # 有未完成的，继续等待
                time.sleep(5)
            else:
                # 全部成功了，结束等待
                ResultService.add_result_detail(opid, op_type, step, content=u"所有打包都已完成")
                return True
        # 超时还未完成
        ResultService.add_result_detail(opid, op_type, step, content=u"等待打包完成超时(1200s)")
        return False

    @staticmethod
    @func_register()
    def wait_dzbd_publish(opid=None, op_type=None, step=None, publish_id=None, env=None, **kwargs):
        """等待电子保单发布完成"""
        retry_count = 240
        for i in range(retry_count):
            flow_data = flow_data_collection.find_one({'flow_id': publish_id})
            dzbd = flow_data.get('data').get('dzbd')
            servers, published_servers = list(), list()
            if env == 'pre':
                servers = app.config['DZBD_PRE_SERVER']
                published_servers = dzbd.get('published_pre_servers', [])
            elif env == 'prd':
                servers = app.config['DZBD_PRD_SERVER']
                published_servers = dzbd.get('published_prd_servers', [])
            if published_servers and set(servers) == set(published_servers):
                ResultService.add_result_detail(opid, op_type, step, content=u"所有服务器都已发布完成")
                return True
            else:
                time.sleep(5)
        # 超时还未完成
        ResultService.add_result_detail(opid, op_type, step, content=u"等待发布完成超时(1200s)")
        return False

    @staticmethod
    @func_register()
    def wait_app_publish(opid=None, op_type=None, step=None, publish_id=None, env=None, app_id=None, server_list=None, **kwargs):
        """等待应用发布完成"""
        retry_count = 120
        for i in range(retry_count):
            flow_data = flow_data_collection.find_one({'flow_id': publish_id})
            published_servers = flow_data.get('data').get('app_info').get(str(app_id)).get('published_{}_servers'.format(env), [])
            if not set(server_list) - set(published_servers):
                ResultService.add_result_detail(opid, op_type, step, content=u"选定的服务器已发布完成")
                return True
            else:
                time.sleep(5)
        # 超时还未完成
        ResultService.add_result_detail(opid, op_type, step, content=u"等待发布完成超时(1200s)")
        return False

    @staticmethod
    @func_register()
    def mark_server_published(opid=None, op_type=None, step=None, publish_id=None, env=None, app_id=None, ip=None, port=None, dzbd_server=None, **kwargs):
        """标记服务器已发布"""
        if app_id and ip and port:
            flow_data_collection.update_one({'flow_id': publish_id}, {
                '$push': {'data.app_info.{}.published_{}_servers'.format(app_id, env): "{}:{}".format(ip, port)}})
        elif dzbd_server:
            flow_data_collection.update_one({'flow_id': publish_id}, {'$push': {'data.dzbd.published_{}_servers'.format(env): "{}".format(dzbd_server)}})
        ResultService.add_result_detail(opid, op_type, step, content=u"标记成功")
        return True

    @staticmethod
    @func_register()
    def kafka_message(opid=None, op_type=None, step=None, project_id=None, publish_id=None, **kwargs):
        """kafka消息记录"""
        data = KafkaService.assemble_aut_kafka_json(project_id, publish_id, **kwargs)
        result = KafkaService.produce(data)
        if result:
            ResultService.add_result_detail(opid, op_type, step, content=data)
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content="send kafka message error!")
            return False

    @staticmethod
    @func_register()
    def pre_sql_before_execute(opid=None, op_type=None, step=None, flow_id=None, project_id=None, env=None, sql_svn_path=None, revision=None, **kwargs):
        result, msg = iDB.execute_sql(project_id, 'pre', sql_svn_path, revision)
        if result:
            SQLScriptsProjectService.mod_sql_status(project_id, 'pre', 'execute', publish_id=flow_id, execute_time=datetime.datetime.now())
            ResultService.add_result_detail(opid, op_type, step, callback="SQLScriptsProjectService.get_sql_execute_detail('{}',{})".format(sql_svn_path, revision))
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=msg)
            return

    @staticmethod
    @func_register()
    def pre_sql_after_execute(opid=None, op_type=None, step=None, flow_id=None, project_id=None, env=None, sql_svn_path=None, revision=None, **kwargs):
        result, msg = iDB.execute_sql(project_id, 'pre', sql_svn_path, revision)
        if result:
            SQLScriptsProjectService.mod_sql_status(project_id, 'pre', 'execute', publish_id=flow_id, execute_time=datetime.datetime.now())
            ResultService.add_result_detail(opid, op_type, step, callback="SQLScriptsProjectService.get_sql_execute_detail('{}',{})".format(sql_svn_path, revision))
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=msg)
            return

    @staticmethod
    @func_register()
    def prd_sql_before_execute(opid=None, op_type=None, step=None, flow_id=None, project_id=None, env=None, sql_svn_path=None, revision=None, **kwargs):
        result, msg = iDB.execute_sql(project_id, 'prd', sql_svn_path, revision)
        if result:
            SQLScriptsProjectService.mod_sql_status(project_id, 'prd', 'execute', publish_id=flow_id, execute_time=datetime.datetime.now())
            ResultService.add_result_detail(opid, op_type, step, callback="SQLScriptsProjectService.get_sql_execute_detail('{}',{})".format(sql_svn_path, revision))
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=msg)
            return

    @staticmethod
    @func_register()
    def prd_sql_after_execute(opid=None, op_type=None, step=None, flow_id=None, project_id=None, env=None, sql_svn_path=None, revision=None, **kwargs):
        result, msg = iDB.execute_sql(project_id, 'prd', sql_svn_path, revision)
        if result:
            SQLScriptsProjectService.mod_sql_status(project_id, 'prd', 'execute', publish_id=flow_id, execute_time=datetime.datetime.now())
            ResultService.add_result_detail(opid, op_type, step, callback="SQLScriptsProjectService.get_sql_execute_detail('{}',{})".format(sql_svn_path, revision))
            return True
        else:
            ResultService.add_result_detail(opid, op_type, step, content=msg)
            return

