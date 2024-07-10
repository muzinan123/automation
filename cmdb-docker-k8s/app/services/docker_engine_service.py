# -*- coding:utf-8 -*-

from sqlalchemy import desc, or_

from app.services.framework.recycle_service import RecycleService
from app.services.k8s_cluster_rds import K8SClusterRdsService
from app.out.k8s_core_app import K8SCoreApp
from app.models.docker_engine import DockerEngine
from app.models import db
from app.out.cmdb_aliyun import Aliyun
from app.out.docker_client import Docker
from app import app, root_logger, rds_logger


class DockerEngineService(object):

    @staticmethod
    def add_engine(ip, port, host_id):
        try:
            if ip and port:
                info = Docker.info(ip, port)
                if info:
                    registry_list = [k for (k, v) in info.get('RegistryConfig').get('IndexConfigs').items() if k!='docker.io']
                    registry = registry_list[0] if registry_list else None
                    org = ""
                    if registry in app.config['ZA_REGISTRY']:
                        org = 'ZA'
                    elif registry in app.config['ZATECH_REGISTRY']:
                        org = 'ZATECH'
                    labels = info.get('Labels')
                    env, cluster_name = '', ''
                    for label in labels:
                        if label[0:16] == 'com.zhongan.env=':
                            env = label[16:]
                        if label[0:23] == 'com.zhongan.bizcluster=':
                            cluster_name = label[23:]

                    d = DockerEngine(id=info.get('ID'), host_id=host_id, name=info.get('Name'), ip=ip, port=port,
                                     version=info.get('ServerVersion'), cpu=info.get('NCPU'), memory=info.get('MemTotal'),
                                     org=org, env=env, registry=registry, cluster_name=cluster_name, cluster_store=info.get('ClusterStore'),
                                     kernel_version=info.get('KernelVersion'), core_sync=True)
                    db.session.add(d)
                    db.session.commit()

                    flag = DockerEngineService.modify_aliyun_rds_white_ip(cluster_name, env, ip)
                    if not flag:
                        return False
                    return True
        except Exception, e:
            root_logger.exception("add_engine error: %s", e)

    # 新增RDS白名单处理逻辑，新增时将相关的集群新增新地NODE节点
    @staticmethod
    def modify_aliyun_rds_white_ip(cluster_name, env, ip):
        try:
            cluster_name_str = cluster_name + '_' + env + '_b1'
            result = K8SClusterRdsService.get_cluster_rds_list_by_name(cluster_name_str)
            if result:
                for res in result:
                    flag = K8SCoreApp.add_aliyun_rds_white_ip('append', res.rds_id, res.cluster_name, ip, 'system', 'add_docker_engine')
                    rds_logger.info("K8SCoreApp.add_aliyun_rds_white_ip {} {} {} {} {}".format('append', res.rds_id, res.cluster_name, ip, 'add_docker_engine'))
                    if flag == 1:
                        # 新增白名单组与IP的关系
                        K8SClusterRdsService.add_cluster_rds_ip(cluster_name_str, ip)
                        rds_logger.info("K8SClusterRdsService.add_cluster_rds_ip {} {}".format(cluster_name_str, ip))
            return True
        except Exception, e:
            rds_logger.info("DockerEngineService.modify_aliyun_rds_white_ip error: %s", e)
            return False

    @staticmethod
    def del_engine(engine_id):
        try:
            d = DockerEngine.query.get(engine_id)
            if d:
                RecycleService.recycle(d)
                db.session.delete(d)
                db.session.commit()
                return True
        except Exception, e:
            root_logger.exception("del_engine error: %s", e)

    @staticmethod
    def mod_engine(engine_id, env=None, cluster_name=None):
        try:
            d = DockerEngine.query.get(engine_id)
            if env:
                d.env = env
            if cluster_name:
                d.cluster_name = cluster_name
            db.session.commit()
        except Exception, e:
            root_logger.exception("mod_engine error: %s", e)

    @staticmethod
    def list_engine(query, env, cluster_name, order_by="id", order_desc=None):
        result = DockerEngine.query.filter(
            or_(DockerEngine.id.like("%" + query + "%") if query is not None else "",
                DockerEngine.name.like("%" + query + "%") if query is not None else "",
                DockerEngine.ip.like("%" + query + "%") if query is not None else ""),
            (DockerEngine.env.in_(env)) if env is not None else "",
            (DockerEngine.cluster_name.like("%" + cluster_name + "%")) if cluster_name is not None else ""
            ).order_by(
            desc(eval('DockerEngine.' + order_by)) if order_desc else (eval('DockerEngine.' + order_by)))
        return result

    @staticmethod
    def get_engine(engine_id):
        return DockerEngine.query.get(engine_id)

    @staticmethod
    def get_engine_by_host_id(host_id):
        return DockerEngine.query.filter(DockerEngine.host_id == host_id).first()

    @staticmethod
    def sync_engine():
        ecs_list = Aliyun.list_docker_ecs()
        DockerEngine.query.update(dict(sync=False))
        for ecs in ecs_list:
            host_ip = ecs.get('in_ip')
            host_port = app.config.get('DOCKER_ENGINE_DEFAULT_PORT')
            info = Docker.info(host_ip, host_port)
            if info:
                registry_list = [k for (k, v) in info.get('RegistryConfig').get('IndexConfigs').items() if k != 'docker.io']
                registry = registry_list[0] if registry_list else None
                labels = info.get('Labels')
                env, cluster_name, org = '', '', ''
                for label in labels:
                    if label[0:16] == 'com.zhongan.env=':
                        env = label[16:]
                    if label[0:23] == 'com.zhongan.bizcluster=':
                        cluster_name = label[23:]
                if registry in app.config['ZA_REGISTRY']:
                    org = 'ZA'
                elif registry in app.config['ZATECH_REGISTRY']:
                    org = 'ZATECH'
                d = DockerEngine(id=info.get('ID'), host_id=ecs.get('instance_id'), name=info.get('Name'), ip=host_ip, port=host_port,
                                 version=info.get('ServerVersion'), cpu=info.get('NCPU'), memory=info.get('MemTotal'), org=org,
                                 env=env, registry=registry, cluster_name=cluster_name, cluster_store=info.get('ClusterStore'),
                                 kernel_version=info.get('KernelVersion'), sync=True)
                db.session.merge(d)
        db.session.flush()
        engine_new_list = DockerEngine.query.filter(DockerEngine.core_sync == False)
        for engine_new in engine_new_list:
            engine_new.core_sync = True
        db.session.flush()
        db.session.commit()

    @staticmethod
    def get_list_engine(cluster_name, env):
        return DockerEngine.query.filter(DockerEngine.cluster_name == cluster_name, DockerEngine.env == env).all()

    @staticmethod
    def get_node_by_res_id(res_id):
        return DockerEngine.query.filter(DockerEngine.host_id == res_id).first()

    @staticmethod
    def get_cluster_name_by_ip(ip):
        result = DockerEngine.query.filter(DockerEngine.ip == ip).first()
        return result