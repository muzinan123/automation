# -*- coding:utf-8 -*-

import json, re
from flask import Blueprint, jsonify, request

from app.services.docker_engine_service import DockerEngineService
from app.services.k8s_app_cluster_service import K8SAppClusterService
from app.services.k8s_app_cluster_log_service import K8SAppClusterLogService
from app.services.k8s_cluster_rds import K8SClusterRdsService
from app.out.k8s_core_app import K8SCoreApp
from app.services.k8s_node_service import K8SNodeService
from app.services.k8s_cluster_service import K8SClusterService
from app.services.k8s_api_service import K8SApiService
from app.decorators.access_control import api
from app import app, rds_logger

k8sApiProfile = Blueprint('k8sApiProfile', __name__)


@app.route("/api/k8s/app/update", methods=['POST'])
@api()
def k8s_app_update():
    app_name = request.get_json().get('app_name', None)
    cluster_name = request.get_json().get('cluster_name', None)
    env = request.get_json().get('env', None)
    platform = request.get_json().get('platform', None)
    org = request.get_json().get('org', None)
    app_id = request.get_json().get('app_id', None)
    ips_str = request.get_json().get('ips', None)
    ret = dict()
    rds_logger.info("K8SAppClusterService.access {} {} {} {} {} {} {}".format(app_id, app_name, env, cluster_name, platform, ips_str, org))
    if env == 'tst':
        env = 'test'
    if not ips_str:
        if platform == 'boom1':
            b_list = list()
            re_list = DockerEngineService.get_list_engine(cluster_name, env)
            if re_list:
                for r in re_list:
                    b_list.append(r.ip)
                ips_str = ','.join(re_list)
    # 检查必传参数
    flag, msg = K8SApiService.check_parameter(app_id, app_name, cluster_name, env, platform, ips_str)
    if not flag:
        ret['result'] = -1
        ret['msg'] = msg
        return jsonify(ret)

    if env == 'test' or env == 'pre':
        fl, rds_msg = add_white_ips_test_pre(env, ips_str, platform)
        ret['result'] = fl
        ret['msg'] = rds_msg
        return jsonify(ret)

    if not org:
        # 根据应用ID查询应用所属的公司
        flag_org, org = K8SCoreApp.get_app_company(app_id)
        if flag_org != 1:
            ret['result'] = -1
            ret['msg'] = org
            return jsonify(ret)
    # 打印调用日志
    rds_logger.info("K8SAppClusterLogService.add_app_cluster_log1 {} {} {} {} {} {}".format(app_id, app_name, env, cluster_name, platform, org))
    # 插入调用日志
    K8SAppClusterLogService.add_app_cluster_log(app_id, app_name, env, cluster_name, platform, org, 1, ips_str)
    # 检查目前的应用与集群是否已存在
    result = K8SAppClusterService.select_app_cluster(app_id, env, cluster_name, platform, 1)
    rds_logger.info("K8SAppClusterService.select_app_cluster {} {} {} {} {} {}".format(app_id, app_name, env, cluster_name, platform, result))
    if result:
        ret['result'] = 2
        ret['msg'] = u'该应用对应关系已存在，无需任何操作'
        return jsonify(ret)

    # 检查该应用是否有对应的RDS信息
    flag_rds, rds_list = K8SCoreApp.select_rds_by_app_name(app_id, app_name, 'rds', env, org)
    rds_logger.info("K8SCoreApp.select_rds_by_app_name {} {} {} {} {} {}".format(flag_rds, app_name, env, cluster_name, platform, result))
    if flag_rds == 1:
        if not rds_list:
            ret['result'] = 3
            ret['msg'] = u'该应用未查询到对应的RDS信息'
            return jsonify(ret)
    else:
        ret['result'] = -1
        ret['msg'] = rds_list
        return jsonify(ret)

    if rds_list:
        for rd in rds_list:
            flag = K8SClusterRdsService.check_count(rd)
            if not flag:
                ret['result'] = -1
                ret['msg'] = u'数据库白名单组已超过50个，RDS_ID:' + rd
                return jsonify(ret)

    plat = ''
    if platform == 'boom1':
        plat = 'b1'
    elif platform == 'boom3':
        plat = 'b3'
    else:
        plat = platform

    # 白名单组的名称
    cluster_name_str = cluster_name + "_" + env + "_" + plat

    # 检查该应用所属的其它集群信息
    res = K8SAppClusterService.select_un_app_cluster(app_id, app_name, env, cluster_name, platform, 1)
    rds_logger.info("K8SAppClusterService.select_un_app_cluster {} {} {} {} {}".format(app_id, app_name, env, cluster_name, platform))
    if res:
        # 更新应用所属其它集群信息的标识is_new=0
        re = K8SAppClusterService.update_app_cluster(app_id, res.app_name, res.env, res.cluster_name, res.platform, 0, org)
        rds_logger.info("K8SAppClusterService.update_app_cluster {} {} {} {} {} {} {}".format(app_id, res.app_name, res.env, res.cluster_name,res.platform, org, re))
        if not re:
            ret['result'] = -1
            ret['msg'] = u'更新数据库失败'
            return jsonify(ret)
        else:
            # 插入应用与集群新的对应关系
            rr = K8SAppClusterService.update_app_cluster(app_id, app_name, env, cluster_name, platform, 1, org)
            rds_logger.info("K8SAppClusterService.update_app_cluster {} {} {} {} {} {} {}".format(app_id, app_name, env, cluster_name, platform, org, rr))
            if not rr:
                ret['result'] = -1
                ret['msg'] = u'更新数据库失败'
                return jsonify(ret)
            else:
                # 插入应用与集群新的对应关系
                K8SAppClusterService.update_app_cluster(app_id, app_name, env, cluster_name, platform, 1, org)
                rds_logger.info("K8SAppClusterService.update_app_cluster {} {} {} {} {} {}".format(app_id, app_name, env, cluster_name, platform, org))
                fl, msg_rds = K8SApiService.add_rds_white_ip(cluster_name_str, ips_str, rds_list, 'system', 'add_new_app_cluster')
                ret['result'] = fl
                ret['msg'] = msg_rds
    else:
        # 插入应用与集群新的对应关系
        K8SAppClusterService.update_app_cluster(app_id, app_name, env, cluster_name, platform, 1, org)
        fl, msg_rds = K8SApiService.add_rds_white_ip(cluster_name_str, ips_str, rds_list, 'system', 'add_app_cluster')
        ret['result'] = fl
        ret['msg'] = msg_rds
    return jsonify(ret)


@app.route("/api/k8s/app/return_back", methods=['POST'])
@api()
def k8s_app_return_back():
    app_name = request.get_json().get('app_name', None)
    cluster_name = request.get_json().get('cluster_name', None)
    env = request.get_json().get('env', None)
    platform = request.get_json().get('platform', None)
    org = request.get_json().get('org', None)
    app_id = request.get_json().get('app_id', None)
    if env == 'tst':
        env = 'test'
    ret = dict()
    # 检查必传参数
    flag, msg = K8SApiService.check_parameter(app_id, app_name, cluster_name, env, platform, '1')
    if not flag:
        ret['result'] = -1
        ret['msg'] = msg
        return jsonify(ret)
    if not org:
        # 根据应用ID查询应用所属的公司
        flag_org, org = K8SCoreApp.get_app_company(app_id)
        if flag_org != 1:
            ret['result'] = -1
            ret['msg'] = org
            return jsonify(ret)

    # 白名单组的名称
    if platform == 'boom1':
        plat = 'b1'
    elif platform == 'boom3':
        plat = 'b3'
    else:
        plat = platform

    if env == 'test' or env == 'pre':
        ret['result'] = 1
        ret['msg'] = u'调用成功'
        return jsonify(ret)

    # 打印输出日志
    rds_logger.info("K8SAppClusterLogService.add_app_cluster_log2 {} {} {} {} {} {}".format(app_id, app_name, env, cluster_name, platform, org))
    # 插入调用日志
    K8SAppClusterLogService.add_app_cluster_log(app_id, app_name, env, cluster_name, platform, org, 2, '')
    # 检查目前的应用是否有is_new = 0的对应关系
    result = K8SAppClusterService.select_un_app_clusters(app_id, app_name, env, cluster_name, platform, 0).all()
    rds_logger.info("K8SAppClusterService.select_un_app_clusters {} {}".format(app_name, cluster_name))
    if not result:
        ret['result'] = 1
        ret['msg'] = u'调用成功'
        return jsonify(ret)
    else:
        # 查询该应用所对应的RDS信息
        flag_one, ones_list = K8SCoreApp.select_rds_by_app_name(app_id, app_name, 'rds', env, org)
        rds_logger.info("K8SCoreApp.select_rds_by_app_name {} {}".format(flag_one, ones_list))
        if (not flag_one) or (not ones_list):
            ret['result'] = -1
            ret['msg'] = u'应用所查的RDS信息异常'
            return jsonify(ret)

        for one in result:
            del_flag = 0
            ret_list = list()
            # 查询集群所对应的非本应的其它应用所有的RDS信息
            o_lists = K8SApiService.query_rds_by_cluster_name(app_id, one.cluster_name, env, platform)
            if o_lists:
                rds_logger.info("query_rds_by_cluster_name {}".format(json.dumps(o_lists)))
                for oe in ones_list:
                    if oe not in o_lists:
                        ret_list.append(oe)
            else:
                ret_list = ones_list
                del_flag = 1
            if ret_list:
                cluster_name_strs = one.cluster_name + "_" + env + "_" + plat
                # 删除应用与RDS对应的白名单
                fl, msg_rds = K8SApiService.del_rds_white_group(cluster_name_strs, ret_list, 'system', 'delete_app_rds_return', del_flag)
                rds_logger.info("del_rds_white_group {} {}".format(cluster_name_strs, fl))
                ret['result'] = fl
                ret['msg'] = msg_rds

            # 删除应用与集群之间的对应关系表数据
            rr_flag = K8SAppClusterService.del_app_cluster(one.app_id, one.app_name, one.env, one.cluster_name, one.platform, 0)
            rds_logger.info("K8SAppClusterService.del_app_cluster {} {} {} {}".format(one.app_id, one.platform, one.cluster_name, rr_flag))
            if not rr_flag:
                ret['result'] = -1
                ret['msg'] = u'应用与集群的关系删除失败'
                return jsonify(ret)
            else:
                ret['result'] = 1
                ret['msg'] = u'调用成功'
        return jsonify(ret)


@app.route("/api/k8s/app/down", methods=['POST'])
@api()
def k8s_app_down():
    app_id = request.values.get('app_id', None)
    operator = request.values.get('operator', 'system')
    source = request.values.get('source', 0)
    org = request.values.get('company_code', None)
    ret = dict()
    # 检查必传参数
    if not app_id:
        ret['result'] = -1
        ret['msg'] = u'app_id不能为空'
        return jsonify(ret)

    if not org:
        ret['result'] = -1
        ret['msg'] = u'根据应用ID未到相关的公司'
        return jsonify(ret)

    # 检查目前的应用所有的对应关系
    result = K8SAppClusterService.select_un_app_clusters(app_id, None, None, None, None, None).all()
    if result:
        rds_logger.info("K8SAppClusterService.select_un_app_clusters {}".format(app_id))
        for dd in result:
            app_name = dd.app_name
            env = dd.env
            cluster_name = dd.cluster_name
            platform = dd.platform

            # 白名单组的名称
            if platform == 'boom1':
                plat = 'b1'
            elif platform == 'boom3':
                plat = 'b3'
            else:
                plat = platform

            # 插入调用日志
            K8SAppClusterLogService.add_app_cluster_log(app_id, app_name, env, cluster_name, platform, org, 3, '')
            rds_logger.info("K8SAppClusterLogService.add_app_cluster_log {} {} {} {}".format(app_id, app_name, cluster_name, platform))
            # 查询该应用所对应的RDS信息
            flag_one, ones_list = K8SCoreApp.select_rds_by_app_name(app_id, app_name+'@'+org, 'rds', env, org)
            if flag_one == 1:
                if ones_list:
                    rds_logger.info("K8SCoreApp.select_rds_by_app_name {} {}".format(app_id, flag_one))
                    for one in result:
                        flag_del = 0
                        ret_list = list()
                        # 查询集群所对应的非本应的其它应用所有的RDS信息
                        o_lists = K8SApiService.query_rds_by_cluster_name(app_id, one.cluster_name, env, platform)
                        cluster_name_strs = one.cluster_name + "_" + env + "_" + plat
                        if o_lists:
                            rds_logger.info("query_rds_by_cluster_name {} {} {}".format(app_id, one.cluster_name, platform))
                            for oe in ones_list:
                                if oe not in o_lists:
                                    ret_list.append(oe)
                        else:
                            ret_list = ones_list
                            flag_del = 1
                        if ret_list:
                            # 删除应用与RDS对应的白名单
                            fl, msg_rds = K8SApiService.del_rds_white_group(cluster_name_strs, ret_list, operator, source, flag_del)
                            rds_logger.info("del_rds_white_group {} {} {}".format(cluster_name_strs, operator, source))
                            ret['result'] = fl
                            ret['msg'] = msg_rds

                        # 删除应用与集群之间的对应关系表数据
                        rr_flag = K8SAppClusterService.del_app_cluster(one.app_id, one.app_name, one.env,
                                                                       one.cluster_name,
                                                                       one.platform, one.is_new)
                        rds_logger.info("K8SAppClusterService.del_app_cluster {} {} {} {}".format(one.app_id, one.app_name, one.cluster_name, one.platform))
                        if not rr_flag:
                            ret['result'] = -1
                            ret['msg'] = u'应用与集群的关系删除失败'
                            return jsonify(ret)
                        else:
                            ret['result'] = 1
                    return jsonify(ret)
            else:
                ret['result'] = -1
                ret['msg'] = u'应用所查的RDS信息异常'
                return jsonify(ret)
    else:
        ret['result'] = 1
        ret['msg'] = u'暂无RDS白名单数据需要处理'
        return jsonify(ret)


@app.route("/api/k8s/app/down_res", methods=['POST'])
@api()
def k8s_app_down_res():
    ret = dict()
    res_id = request.get_json().get('res_id', None)
    ip = request.get_json().get('ip', None)
    operator = request.get_json().get('operator', 'system')
    source = request.get_json().get('source', 0)
    platform = request.get_json().get('platform', None)
    flag_del, msg = K8SApiService.check_parameter_boom_del(ip, platform)
    if not flag_del:
        ret['result'] = -1
        ret['msg'] = msg
        return jsonify(ret)
    if platform:
        source = platform
        # 插入调用日志
        K8SAppClusterLogService.add_app_cluster_log('', ip, source, operator, platform, ip, 5, '')

    err_list = list()
    rds_ips = K8SClusterRdsService.list_cluster_rds_ip('', ip).all()
    if rds_ips:
        for rds_ip in rds_ips:
            rdss = K8SClusterRdsService.list_cluster_rds(rds_ip.cluster_name, '').all()
            if rdss:
                rds_logger.info("K8SClusterRdsService.list_cluster_rds {}".format(rds_ip.cluster_name))
                for rds in rdss:
                    flag_ecs = K8SCoreApp.add_aliyun_rds_white_ip('delete', rds.rds_id, rds.cluster_name, rds_ip.ip, operator, source)
                    rds_logger.info("K8SCoreApp.add_aliyun_rds_white_ip delete {} {} {} {} {}".format(rds.rds_id, rds.cluster_name, rds_ip.ip, operator, source))
                    if flag_ecs == 1:
                        K8SClusterRdsService.del_cluster_rds_ip(rds.cluster_name, rds_ip.ip)
                        rds_logger.info("K8SClusterRdsService.del_cluster_rds_ip {} {} {}".format(rds.cluster_name, rds_ip.ip, flag_ecs))
                    else:
                        err_list.append(rds.rds_id)
    if err_list:
        err_str = ','.join(err_list)
        ret['result'] = -1
        ret['msg'] = err_str + u'删除白名单IP异常'
        return jsonify(ret)
    ret['result'] = 1
    return jsonify(ret)


@app.route("/api/k8s/app/get_cluster_name", methods=['GET'])
@api()
def k8s_app_get_cluster_name():
    ret = dict()
    platform = request.values.get('platform', None)
    ip = request.values.get('ip', None)
    if not platform:
        ret['result'] = -1
        ret['msg'] = u'platform平台类型不能为空'
        return jsonify(ret)

    if not ip:
        ret['result'] = -1
        ret['msg'] = u'ip不能为空'
        return jsonify(ret)
    else:
        if not re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",ip):
            ret['result'] = -1
            ret['msg'] = u'ip格式错误'
            return jsonify(ret)

    if platform == 'boom1':
        b1_result = DockerEngineService.get_cluster_name_by_ip(ip)
        if b1_result:
            ret['result'] = 1
            ret['msg'] = u'调用成功'
            ret['data'] = b1_result.cluster_name
            return jsonify(ret)
        else:
            ret['result'] = -1
            ret['msg'] = u'集群信息不存在，请管理员核实信息'
            return jsonify(ret)

    elif platform == 'boom3':
        b3_result = K8SNodeService.get_cluster_name_by_ip(ip)
        if b3_result:
            ret['result'] = 1
            ret['msg'] = u'调用成功'
            ret['data'] = b3_result.name
            return jsonify(ret)
        else:
            ret['result'] = -1
            ret['msg'] = u'集群信息不存在，请管理员核实信息'
            return jsonify(ret)
    else:
        ret['result'] = -1
        ret['msg'] = u'平台类型只能为boom1或boom3'
        return jsonify(ret)


@app.route("/api/k8s/node/add", methods=['POST'])
@api()
def k8s_node_add_boom():
    name = request.get_json().get('name', None)
    cluster = request.get_json().get('cluster', None)
    department = request.get_json().get('department', None)
    bizcluster = request.get_json().get('bizcluster', None)
    ip = request.get_json().get('ip', None)
    pod_cidr = request.get_json().get('pod_cidr', None)
    cpu = request.get_json().get('cpu', None)
    memory = request.get_json().get('memory', None)
    platform = request.get_json().get('platform', None)
    if cluster == 'tst':
        cluster = 'test'
    ret = dict()
    # 插入调用日志
    K8SAppClusterLogService.add_app_cluster_log('', ip, cluster, bizcluster, platform, name, 4, '')
    # 检查必传参数
    flag, msg = K8SApiService.check_parameter_boom(name, cluster, bizcluster, ip, platform)
    if not flag:
        ret['result'] = -1
        ret['msg'] = msg
        return jsonify(ret)
    cluster_list = K8SAppClusterService.get_cluster_name(ip).first()
    if cluster_list:
        cluster_name = cluster_list.cluster_name
        plat = ''
        if platform == 'boom1':
            plat = 'b1'
        elif platform == 'boom3':
            plat = 'b3'
        else:
            plat = platform

        cluster_arr = cluster_name.split('_')
        if cluster_arr[0] == bizcluster and cluster_arr[1] == cluster and cluster_arr[2] == plat:
            ret['result'] = 1
            ret['msg'] = u'新增成功'
            return jsonify(ret)
        else:
            err_list = list()
            rdss = K8SClusterRdsService.list_cluster_rds(cluster_name, '').all()
            if rdss:
                rds_logger.info("K8SClusterRdsService.list_cluster_rds {}".format(cluster_name))
                for rds in rdss:
                    flag_ecs = K8SCoreApp.add_aliyun_rds_white_ip('delete', rds.rds_id, rds.cluster_name, ip, platform, 6)
                    rds_logger.info("K8SCoreApp.add_aliyun_rds_white_ip delete {} {} {} {} {}".format(rds.rds_id, rds.cluster_name, ip, platform, 'boom'))
                    if flag_ecs == 1:
                        K8SClusterRdsService.del_cluster_rds_ip(rds.cluster_name, ip)
                        rds_logger.info("K8SClusterRdsService.del_cluster_rds_ip {} {} {}".format(rds.cluster_name, ip, flag_ecs))
                    else:
                        err_list.append(rds.rds_id)
            if err_list:
                err_str = ','.join(err_list)
                ret['result'] = -1
                ret['msg'] = err_str + u'删除白名单IP异常'
                return jsonify(ret)

    flag = K8SNodeService.modify_aliyun_rds_white_ip(bizcluster, cluster, ip, platform)
    if flag:
        ret['result'] = 1
        ret['msg'] = u'新增成功'
    else:
        ret['result'] = -1
        ret['msg'] = u'新增失败'
    return jsonify(ret)


@app.route("/api/k8s/rds/add", methods=['POST'])
@api()
def k8s_rds_add():
    app_name = request.values.get('app_name', None)
    env = request.values.get('env', None)
    org = request.values.get('org', None)
    app_id = request.values.get('app_id', None)
    res_id = request.values.get('res_id', None)
    operator = request.values.get('operator', None)
    if env == 'tst':
        env = 'test'
    ret = dict()
    # 打印调用日志
    rds_logger.info("k8s_rds_add {} {} {} {}".format(app_id, app_name, env, org))
    # 插入调用日志
    K8SAppClusterLogService.add_app_cluster_log(app_id, app_name, env, res_id, '', org, 4, '')
    # 检查目前的应用与集群是否已存在
    result = K8SAppClusterService.select_app_cluster(app_id, env, None, None, 1)
    if result:
        for r in result:
            if r.platform == 'boom1':
                plat = 'b1'
            elif r.platform == 'boom3':
                plat = 'b3'
            else:
                plat = r.platform

            group_name_str = r.cluster_name + '_' + env + '_' + plat
            ip_list_result = K8SClusterRdsService.get_cluster_rds_ip_list(group_name_str)
            if ip_list_result:
                rds_list = list()
                ips = list()
                for ip_list in ip_list_result:
                    ips.append(ip_list.ip)
                ips_str = ','.join(ips)
                rds_list.append(res_id)
                fl, msg_rds = K8SApiService.add_rds_white_ip(group_name_str, ips_str, rds_list, operator,'add_rds_app_cluster')
                ret['result'] = fl
                ret['msg'] = msg_rds
    else:
        ret['result'] = 1
    return jsonify(ret)


def add_white_ips_test_pre(env, ips, platform):
    cluster_name_str = 'k8s_' + env + '_' + platform
    k8s_test_pre = app.config['ZA_RDS_WHITE_TEST_UAT']
    if platform == 'za-boom3':
        key_str = 'za_' + env
    elif platform == 'zatech-boom3':
        key_str = 'zatech_' + env
    rds_str = k8s_test_pre.get(key_str)
    rds_arr = rds_str.split(',')
    ips_list = list()
    if ips:
        ips_list = ips.split(',')
    result_ips = K8SApiService.query_ips_by_cluster_name(cluster_name_str).all()
    if result_ips:
        ip_list = list()
        for res in result_ips:
            ip_list.append(res.ip)
        if ip_list:
            ips_list.extend(ip_list)
    ips_list = list(set(ips_list))
    ips_str = ','.join(ips_list)
    fl, msg_rds = K8SApiService.add_rds_white_ip(cluster_name_str, ips_str, rds_arr, 'system', 'add_test_uat')
    return fl, msg_rds
