# -*- coing: utf8 -*-

import requests

from app import app, out_logger


class KubernetesAdmin(object):

    @staticmethod
    def get_url(org):
        for prefix, org_list in app.config['K8S_ORG_RELATIONSHIP'].items():
            if org in org_list:
                return prefix

    @staticmethod
    def list_bizcluster(org, env):
        try:
            prefix = KubernetesAdmin.get_url(org)
            url = app.config.get('K8S_ADMIN_{}_URL'.format(prefix.upper()))
            url += '/zcloud/api/v3/clusters/{}/bizclusters'.format(env)
            token = app.config.get('K8S_ADMIN_{}_TOKEN'.format(prefix.upper()))
            headers = dict()
            headers['Authorization'] = token
            response = requests.get(url, headers=headers)
            if response.status_code == 200 and response.json().get('IsSuccess'):
                data = response.json().get('Data')
                return data
        except Exception, e:
            out_logger.exception("list_bizcluster error: %s", e)

    @staticmethod
    def list_nodes(org, env):
        try:
            prefix = KubernetesAdmin.get_url(org)
            url = app.config.get('K8S_ADMIN_{}_URL'.format(prefix.upper()))
            url += '/zcloud/api/v3/clusters/{}/nodes'.format(env)
            token = app.config.get('K8S_ADMIN_{}_TOKEN'.format(prefix.upper()))
            headers = dict()
            headers['Authorization'] = token
            response = requests.get(url, headers=headers)
            if response.status_code == 200 and response.json().get('IsSuccess'):
                data = response.json().get('Data')
                return data
        except Exception, e:
            out_logger.exception("list_bizcluster error: %s", e)

    @staticmethod
    def get_node_info(org, env, node_name):
        try:
            prefix = KubernetesAdmin.get_url(org)
            url = app.config.get('K8S_ADMIN_{}_URL'.format(prefix.upper()))
            url += '/zcloud/api/v3/clusters/{}/nodes/{}'.format(env, node_name)
            token = app.config.get('K8S_ADMIN_{}_TOKEN'.format(prefix.upper()))
            headers = dict()
            headers['Authorization'] = token
            response = requests.get(url, headers=headers)
            if response.status_code == 200 and response.json().get('IsSuccess'):
                data = response.json().get('Data')
                return data
        except Exception, e:
            out_logger.exception("list_bizcluster error: %s", e)

    @staticmethod
    def get_node_pods(org, env, node_name):
        try:
            prefix = KubernetesAdmin.get_url(org)
            url = app.config.get('K8S_ADMIN_{}_URL'.format(prefix.upper()))
            url += '/zcloud/api/v3/clusters/{}/nodes/{}/pods'.format(env, node_name)
            token = app.config.get('K8S_ADMIN_{}_TOKEN'.format(prefix.upper()))
            headers = dict()
            headers['Authorization'] = token
            response = requests.get(url, headers=headers)
            if response.status_code == 200 and response.json().get('IsSuccess'):
                data = response.json().get('Data')
                return data
        except Exception, e:
            out_logger.exception("list_bizcluster error: %s", e)

    @staticmethod
    def add_node_labels(org, env, node_name, labels):
        try:
            prefix = KubernetesAdmin.get_url(org)
            url = app.config.get('K8S_ADMIN_{}_URL'.format(prefix.upper()))
            url += '/zcloud/api/v3/clusters/{}/nodes/{}'.format(env, node_name)
            token = app.config.get('K8S_ADMIN_{}_TOKEN'.format(prefix.upper()))
            headers = dict()
            headers['Authorization'] = token
            data = dict()
            data['labels'] = labels
            out_logger.info("url: {}".format(url))
            out_logger.info("data: {}".format(data))
            response = requests.put(url, headers=headers, json=data)
            out_logger.info(response.content)
            if response.status_code == 200 and response.json().get('IsSuccess'):
                return True
        except Exception, e:
            out_logger.exception("add_node_labels error: %s", e)

    @staticmethod
    def get_group(org, group):
        try:
            prefix = KubernetesAdmin.get_url(org)
            url = app.config.get('K8S_ADMIN_{}_URL'.format(prefix.upper()))
            url += '/passport/api/v1/groups/{}'.format(group)
            token = app.config.get('K8S_ADMIN_{}_TOKEN'.format(prefix.upper()))
            headers = dict()
            headers['Authorization'] = token
            response = requests.get(url, headers=headers)
            out_logger.debug(response.content)
            if response.status_code == 200 and response.json().get('IsSuccess'):
                return True
        except Exception, e:
            out_logger.exception("add_group error: %s", e)

    @staticmethod
    def add_group(org, group, description):
        try:
            prefix = KubernetesAdmin.get_url(org)
            url = app.config.get('K8S_ADMIN_{}_URL'.format(prefix.upper()))
            url += '/passport/api/v1/groups'
            token = app.config.get('K8S_ADMIN_{}_TOKEN'.format(prefix.upper()))
            headers = dict()
            headers['Authorization'] = token
            data = dict()
            data['group'] = group
            data['description'] = description
            out_logger.info("url: {}".format(url))
            out_logger.info("data: {}".format(data))
            response = requests.post(url, headers=headers, json=data)
            out_logger.info(response.content)
            if response.status_code == 200 and response.json().get('IsSuccess'):
                return True
        except Exception, e:
            out_logger.exception("add_group error: %s", e)

    @staticmethod
    def add_bizcluster(org, group, bizcluster, description):
        try:
            prefix = KubernetesAdmin.get_url(org)
            url = app.config.get('K8S_ADMIN_{}_URL'.format(prefix.upper()))
            url += '/passport/api/v1/groups/{}/bizclusters'.format(group)
            token = app.config.get('K8S_ADMIN_{}_TOKEN'.format(prefix.upper()))
            headers = dict()
            headers['Authorization'] = token
            data = dict()
            data['bizcluster'] = bizcluster
            data['description'] = description
            out_logger.info("url: {}".format(url))
            out_logger.info("data: {}".format(data))
            response = requests.post(url, headers=headers, json=data)
            out_logger.info(response.content)
            if response.status_code == 200 and response.json().get('IsSuccess'):
                return True
        except Exception, e:
            out_logger.exception("add_bizcluster error: %s", e)

    @staticmethod
    def list_group(org):
        try:
            prefix = KubernetesAdmin.get_url(org)
            url = app.config.get('K8S_ADMIN_{}_URL'.format(prefix.upper()))
            url += '/passport/api/v1/groups'
            token = app.config.get('K8S_ADMIN_{}_TOKEN'.format(prefix.upper()))
            headers = dict()
            headers['Authorization'] = token
            out_logger.info("url: {}".format(url))
            response = requests.get(url, headers=headers)
            out_logger.info(response.content)
            if response.status_code == 200 and response.json().get('IsSuccess'):
                data = response.json().get('Data')
                return data
        except Exception, e:
            out_logger.exception("list_group error: %s", e)

    @staticmethod
    def list_group_bizcluster(org, group):
        try:
            prefix = KubernetesAdmin.get_url(org)
            url = app.config.get('K8S_ADMIN_{}_URL'.format(prefix.upper()))
            url += '/passport/api/v1/groups/{}/bizclusters'.format(group)
            token = app.config.get('K8S_ADMIN_{}_TOKEN'.format(prefix.upper()))
            headers = dict()
            headers['Authorization'] = token
            out_logger.info("url: {}".format(url))
            response = requests.get(url, headers=headers)
            out_logger.info(response.content)
            if response.status_code == 200 and response.json().get('IsSuccess'):
                data = response.json().get('Data')
                return data
        except Exception, e:
            out_logger.exception("list_group error: %s", e)

    @staticmethod
    def add_node_with_label(org, env, node_name, labels):
        try:
            prefix = KubernetesAdmin.get_url(org)
            url = app.config.get('K8S_ADMIN_{}_URL'.format(prefix.upper()))
            url = '{}/zcloud/api/v3/clusters/{}/nodes'.format(url, env)
            token = app.config.get('K8S_ADMIN_{}_TOKEN'.format(prefix.upper()))
            headers = dict()
            headers['Authorization'] = token
            data = dict()
            data['deploy_mode'] = 'manual'
            data['node'] = [{
                'ip': node_name,
                'labels': labels
            }]
            out_logger.info("url: {}".format(url))
            out_logger.info("data: {}".format(data))
            response = requests.post(url, headers=headers, json=data)
            out_logger.info(response.content)
            if response.status_code == 200 and response.json().get('IsSuccess'):
                return True
        except Exception, e:
            out_logger.exception("add_node_with_label error: %s", e)
