# -*- coding:utf-8 -*-

import hashlib
import datetime
from sqlalchemy import desc, or_

from app.services.framework.recycle_service import RecycleService
from app.services.core.core_service import CoreService
from app.models.docker_engine import DockerEngine
from app.models.docker_cluster import DockerCluster
from app.models import db
from app import app, root_logger


class DockerClusterService(object):

    @staticmethod
    def add_cluster(name, org, env, creator='system'):
        try:
            cluster_id = hashlib.md5(name+"@"+env+"@"+org).hexdigest()
            r = DockerCluster(id=cluster_id, name=name, org=org, env=env, create_at=datetime.datetime.now(), creator=creator, core_sync=True)
            db.session.add(r)
            db.session.flush()
            if CoreService.register(cluster_id, "true", name+"@"+env+"@"+org, ["docker_cluster"], "docker_cluster"):
                db.session.commit()
                return True
        except Exception, e:
            root_logger.exception("add_cluster error: %s", e)

    @staticmethod
    def check_exist(name, org, env):
        r = DockerCluster.query.filter(DockerCluster.name == name, DockerCluster.org == org, DockerCluster.env == env).first()
        if r:
            return True

    @staticmethod
    def del_cluster(cluster_id, delete_by='system'):
        try:
            r = DockerCluster.query.get(cluster_id)
            if CoreService.unregister(cluster_id, 'docker_cluster'):
                RecycleService.recycle(r, delete_by=delete_by, commit=False)
                db.session.delete(r)
                db.session.commit()
                return True
        except Exception, e:
            root_logger.exception("del_cluster error: %s", e)

    @staticmethod
    def list_cluster(query, order_by='create_at', order_desc=None, org=None):
        result = DockerCluster.query.filter(
            DockerCluster.name.like("%" + query + "%") if query else "",
            DockerCluster.org.in_(org) if org is not None else ""
        ).order_by(desc(eval('DockerCluster.' + order_by)) if order_desc else (eval('DockerCluster.' + order_by)))
        return result

    @staticmethod
    def get_cluster(cluster_id):
        return DockerCluster.query.get(cluster_id)

    @staticmethod
    def get_cluster_by_name(name, org, env):
        return DockerCluster.query.filter(DockerCluster.name == name, DockerCluster.org == org, DockerCluster.env == env).first()

    @staticmethod
    def sync_cluster():
        cluster_list = db.session.query(DockerEngine.org, DockerEngine.env, DockerEngine.cluster_name).group_by(DockerEngine.registry, DockerEngine.env, DockerEngine.cluster_name)
        DockerCluster.query.update(dict(sync=False))
        for cluster in cluster_list:
            org = cluster[0]
            env = cluster[1]
            cluster_name = cluster[2]
            cluster_id = hashlib.md5(cluster_name+"@"+env+"@"+org).hexdigest()
            c = DockerCluster(id=cluster_id, name=cluster_name, org=org, env=env, create_at=datetime.datetime.now(), creator='system', sync=True)
            db.session.merge(c)
        db.session.flush()
        cluster_new_list = DockerCluster.query.filter(DockerCluster.core_sync == False)
        for cluster_new in cluster_new_list:
            if CoreService.register(cluster_new.id, "true", cluster_new.name+"@"+cluster_new.env+"@"+cluster_new.org, ['docker_cluster'], 'docker_cluster'):
                cluster_new.core_sync = True
        db.session.commit()
        '''
        cluster_old_list = DockerCluster.query.filter(DockerCluster.sync == False)
        for cluster_old in cluster_old_list:
            CoreService.unregister(cluster_old.id)
            RecycleService.recycle(cluster_old, commit=False)
            db.session.delete(cluster_old)
        db.session.commit()
        '''

    @staticmethod
    def get_cluster_by_env_org(env, org):
        if env and org:
            return DockerCluster.query.filter(DockerCluster.env == env, DockerCluster.org == org).all()
        elif not env and org:
            return DockerCluster.query.filter(DockerCluster.org == org).all()
        elif not org and env:
            return DockerCluster.query.filter(DockerCluster.env == env).all()
        else:
            return DockerCluster.query.all()

    @staticmethod
    def get_info_by_cluster(name, env, org):
        if name and env and org:
            return DockerCluster.query.filter(DockerCluster.name == name, DockerCluster.env == env,
                                               DockerCluster.org == org)
        elif name and not env and org:
            return DockerCluster.query.filter(DockerCluster.name == name, DockerCluster.org == org)
        elif name and env and not org:
            return DockerCluster.query.filter(DockerCluster.name == name, DockerCluster.env == env)
        elif name and not env and not org:
            return DockerCluster.query.filter(DockerCluster.name == name)
        elif not name and env and org:
            return DockerCluster.query.filter(DockerCluster.env == env, DockerCluster.org == org)
        elif not name and not env and org:
            return DockerCluster.query.filter(DockerCluster.org == org)
        elif not name and env and not org:
            return DockerCluster.query.filter(DockerCluster.env == env)
        elif not name and not env and not org:
            return DockerCluster.query




