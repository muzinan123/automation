# -*- coding: utf8 -*-
import time, datetime
from app.models import db
from app.models.docker_engine import DockerEngine
from app.services.k8s_app_cluster_service import K8SAppClusterService
from app.out.k8s_core_app import K8SCoreApp
from app.services.k8s_api_service import K8SApiService


class AliyunWhiteK8sTemp(db.Model):
    __bind_key__ = 'main'
    __tablename__ = 'aliyun_white_k8s_temp'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    res_id = db.Column(db.String(128))
    app_tag_name = db.Column(db.String(128))
    env = db.Column(db.String(32))
    org_name = db.Column(db.String(64))
    is_exist = db.Column(db.Boolean)
    org = db.Column(db.String(32))
    app_id = db.Column(db.Integer())
    flag = db.Column(db.String(255))
    department = db.Column(db.String(255))
    product = db.Column(db.String(255))
    cluster = db.Column(db.String(255))
    ips = db.Column(db.String(255))

    def serialize(self):
        return {
            'id': self.id,
            'res_id': self.res_id,
            'app_tag_name': self.app_tag_name,
            'env': self.env,
            'org_name': self.org_name,
            'is_exist': self.is_exist,
            'org': self.org,
            'app_id': self.app_id,
            'cluster': self.cluster,
            'ips': self.ips
        }


# 先导入BOOM1应用与集群的临时数据表，将集群所对应的所有IP同步到临时表的IPS字段
def sync_ips():
    ali_list = AliyunWhiteK8sTemp.query.filter(AliyunWhiteK8sTemp.is_exist == 1).all()
    i = 0
    AliyunWhiteK8sTemp.query.update(dict(flag=False))
    for ali in ali_list:
        i = i + 1
        print i, ali.app_tag_name
        dockerNodes = DockerEngine.query.filter(DockerEngine.cluster_name == ali.cluster).all()
        if dockerNodes:
            ip_list = list()
            for dockerNode in dockerNodes:
                ip_list.append(dockerNode.ip)
            ip_str = ','.join(ip_list)
            ali.ips = ip_str
            ali.flag = 1
            db.session.merge(ali)
    db.session.commit()


# 插入应用与集群之间的关系，并将集群所对应的IPS跑入阿里云RDS白名单中
def sync_aliyun_white():
    # 查询所有BOOM1中含有IP的集群及应用信息
    ali_list = AliyunWhiteK8sTemp.query.filter(AliyunWhiteK8sTemp.is_exist == 1, AliyunWhiteK8sTemp.flag == 1).all()
    i = 0
    for ali in ali_list:
        i = i + 1
        print i, ali.app_tag_name
        # 检查该应用是否有对应的RDS信息
        flag_rds, rds_list = K8SCoreApp.select_rds_by_app_name(ali.app_id, ali.app_tag_name, 'rds', ali.env, ali.org)
        if rds_list:
            # 白名单组的名称
            cluster_name_str = ali.cluster + "_" + ali.env + "_b1"
            rr = K8SAppClusterService.update_app_cluster(ali.app_id, ali.app_tag_name, ali.env, ali.cluster, 'boom1', 1, ali.org)
            if rr:
                # 调用阿里云更新白名单接口
                fl, msg_rds = K8SApiService.add_rds_white_ip(cluster_name_str, ali.ips, rds_list, 'system','add_app_cluster')
                if not fl:
                    print cluster_name_str, ali.ips, rds_list


if __name__ == '__main__':
    start_time = datetime.datetime.now()
    sync_ips()
    sync_aliyun_white()
    end_time = datetime.datetime.now()
    print "First step total time: " + str((end_time - start_time).seconds)