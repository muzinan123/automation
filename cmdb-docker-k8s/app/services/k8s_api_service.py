# -*- coding:utf8 -*-

import datetime, re
from app.models.k8s_cluster_rds import K8SClusterRds
from app.models.k8s_cluster_rds_ip import K8SClusterRdsIP
from app.models import db
from app.services.k8s_app_cluster_service import K8SAppClusterService
from app.out.k8s_core_app import K8SCoreApp
from app import rds_logger


class K8SApiService(object):

    @staticmethod
    def del_rds_white_group(cluster_name_str, rd_list, operator, source, flag_del):
        try:
            flag = 2
            t_list = list()
            for e in rd_list:
                # 删除白名单组
                result = K8SCoreApp.add_aliyun_rds_white_ip('delGroup', e, cluster_name_str, '', operator, source)
                rds_logger.info(
                    "K8SCoreApp.add_aliyun_rds_white_ip {} {} {} {}".format(e, cluster_name_str, operator, source))
                if result == -1:
                    flag = -1
                    t_list.append(e)
                else:
                    flag = 1
                    # 与RDS 之间的关系数据
                    k8s_app = K8SClusterRds.query.filter(K8SClusterRds.cluster_name == cluster_name_str,
                                                         K8SClusterRds.rds_id == e).first()
                    if k8s_app:
                        db.session.delete(k8s_app)

                    rds_logger.info("K8SClusterRdsService.del_cluster_rds {} {}".format(cluster_name_str, e))
                if flag_del == 1:
                    result = K8SClusterRdsIP.query.filter(K8SClusterRdsIP.cluster_name == cluster_name_str).all()
                    if result:
                        for re in result:
                            db.session.delete(re)
                db.session.commit()
            if flag:
                msg = u'白名单组删除成功'
            else:
                msg = ','.join(t_list) + u'白名单组删除失败'
            return flag, msg
        except Exception, e:
            rds_logger.exception("K8SApiService.del_rds_white_group error: %s", e)

    @staticmethod
    def add_rds_white_ip(cluster_name_str, ips, rd_list, operator, source):
        try:
            flag = 1
            t_list = list()
            for e in rd_list:
                result = K8SCoreApp.add_aliyun_rds_white_ip('add', e, cluster_name_str, ips, operator, source)
                rds_logger.info(
                    "K8SCoreApp.add_aliyun_rds_white_ip {} {} {} {} {}".format(e, cluster_name_str, ips, operator,
                                                                               source))
                if result == -1:
                    flag = -1
                    t_list.append(e)
                else:
                    # 插入集群与RDS 之间的关系数据
                    e = K8SClusterRds(cluster_name=cluster_name_str, rds_id=e, create_at=datetime.datetime.now())
                    db.session.merge(e)
                    rds_logger.info("K8SClusterRdsService.add_cluster_rds {} {}".format(cluster_name_str, e))
                    # 批量插入白名单组与IP 的关系
                    if ips.strip():
                        ip_list = ips.split(',')
                        if ip_list:
                            for ip in ip_list:
                                e = K8SClusterRdsIP(cluster_name=cluster_name_str, ip=ip, create_at=datetime.datetime.now())
                                db.session.merge(e)
                    rds_logger.info("K8SClusterRdsService.add_cluster_rds_ips {} {}".format(cluster_name_str, ips))
                db.session.commit()
            if flag:
                msg = u'数据库添加白名单成功'
            else:
                msg = ','.join(t_list) + u'添加失败'
            return flag, msg
        except Exception, e:
            rds_logger.exception("K8SApiService.add_rds_white_ip error: %s", e)

    @staticmethod
    def query_rds_by_cluster_name(app_id, cluster_name, env, platform):
        result = K8SAppClusterService.select_un_app_name(app_id, env, cluster_name, platform)
        o_list = list()
        if result:
            for re in result:
                flag_one, ones = K8SCoreApp.select_rds_by_app_name(re.app_id, re.app_name, 'rds', env, re.org)
                if flag_one:
                    if ones:
                        o_list.extend(ones)
        return o_list

    @staticmethod
    def query_ips_by_cluster_name(cluster_name):
        result = K8SClusterRdsIP.query.filter(K8SClusterRdsIP.cluster_name == cluster_name)
        return result

    @staticmethod
    def check_parameter(app_id, app_name, cluster_name, env, platform, ips):
        if not app_id:
            msg = "app_id" + u"不能为空"
            return False, msg
        if not app_name:
            msg = "app_name" + u"不能为空"
            return False, msg
        if not cluster_name:
            msg = "cluster_name" + u"不能为空"
            return False, msg
        if not env:
            msg = "env" + u"不能为空"
            return False, msg
        if not platform:
            msg = "platform" + u"不能为空"
            return False, msg
        if not ips:
            msg = "ips" + u"不能为空"
            return False, msg
        return True, ''

    @staticmethod
    def check_parameter_boom(name, cluster, bizcluster, ip, platform):
        if not name:
            msg = "name" + u"不能为空"
            return False, msg
        if not cluster:
            msg = "cluster" + u"不能为空"
            return False, msg
        if not bizcluster:
            msg = "bizcluster" + u"不能为空"
            return False, msg
        if not platform:
            msg = "platform" + u"不能为空"
            return False, msg
        if not ip:
            msg = "ip" + u"不能为空"
            return False, msg
        if not re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",ip):
            msg = u'ip格式错误'
            return False, msg
        return True, ''

    @staticmethod
    def check_parameter_boom_del(ip, platform):
        if not platform:
            msg = "platform" + u"不能为空"
            return False, msg
        if platform != 'boom1' and platform != 'boom3':
            msg = "platform" + u'只支持boom1或boom3'
            return False, msg
        if not ip:
            msg = "ip" + u"不能为空"
            return False, msg
        if not re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
                        ip):
            msg = u'ip格式错误'
            return False, msg
        return True, ''