# -*- coding:utf8 -*-

import docker
import json
from app import out_logger


class Docker(object):

    @staticmethod
    def ping(host_ip, host_port=2375):
        try:
            client = docker.DockerClient(base_url="tcp://{}:{}".format(host_ip, host_port), version='auto', timeout=2)
            return client.ping()
        except Exception, e:
            # out_logger.exception("ping error: %s", e)
            out_logger.error("docker ping error: {}".format(host_ip))

    @staticmethod
    def info(host_ip, host_port=2375):
        try:
            client = docker.DockerClient(base_url="tcp://{}:{}".format(host_ip, host_port), version='auto', timeout=2)
            return client.info()
        except Exception, e:
            out_logger.exception("info error: %s", e)

    @staticmethod
    def list_image(host_ip, host_port=2375, all=False):
        try:
            client = docker.DockerClient(base_url="tcp://{}:{}".format(host_ip, host_port), version='auto', timeout=2)
            ret = list()
            for image in client.images.list(all=all):
                ret.append({'short_id': image.short_id, 'tags': image.tags})
            return ret
        except Exception, e:
            out_logger.exception("list_image error: %s", e)
        return list()

    @staticmethod
    def list_container(host_ip, host_port=2375, all=False):
        try:
            client = docker.DockerClient(base_url="tcp://{}:{}".format(host_ip, host_port), version='auto', timeout=2)
            ret = list()
            for container in client.containers.list(all=all):
                config = container.attrs.get('Config')
                image = None
                if config:
                    image = config.get('Image')
                ret.append({
                    'short_id': container.short_id,
                    'name': container.name,
                    'status': container.status,
                    'image': image
                })
            return ret
        except Exception, e:
            out_logger.exception("list_container error: %s", e)
