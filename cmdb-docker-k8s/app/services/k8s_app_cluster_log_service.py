# -*- coding:utf8 -*-

import datetime
from app.models.k8s_app_cluster_log import K8SAppClusterLog
from app.models import db
from app import app, root_logger


class K8SAppClusterLogService(object):

    @staticmethod
    def add_app_cluster_log(app_id, app_name, env, cluster_name, platform, org, type, ips=None):
        try:

            now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            e = K8SAppClusterLog(app_id=app_id, app_name=app_name, env=env, cluster_name=cluster_name,
                                 platform=platform, type=type, org=org, create_at=now_time, ips=ips)
            db.session.add(e)
            db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("add_app_cluster error: %s", e)
