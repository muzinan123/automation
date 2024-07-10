# -*- coding: utf8 -*-

import jenkins
from jinja2 import Environment, PackageLoader

from app import app, jenkins_logger


class JenkinsClient(object):

    server = dict()

    jinja2_env = Environment(loader=PackageLoader('jenkins_job_config', 'templates'))

    @staticmethod
    def get_server(env):
        try:
            url = app.config['JENKINS_{}_URL'.format(env.upper())]
            username = app.config['JENKINS_{}_USERNAME'.format(env.upper())]
            password = app.config['JENKINS_{}_PASSWORD'.format(env.upper())]
            JenkinsClient.server[env] = jenkins.Jenkins(url, username=username, password=password)
        except Exception, e:
            jenkins_logger.exception("get_server error: %s", e)

    @staticmethod
    def get_version(env):
        server = JenkinsClient.server.get(env)
        if not server:
            JenkinsClient.get_server(env)
            server = JenkinsClient.server.get(env)
        try:
            return server.get_version()
        except Exception, e:
            jenkins_logger.exception("get_version error: %s", e)

    @staticmethod
    def get_whoami(env):
        server = JenkinsClient.server.get(env)
        if not server:
            JenkinsClient.get_server(env)
            server = JenkinsClient.server.get(env)
        try:
            return server.get_whoami()
        except Exception, e:
            jenkins_logger.exception("get_version error: %s", e)

    @staticmethod
    def get_all_jobs(env):
        server = JenkinsClient.server.get(env)
        if not server:
            JenkinsClient.get_server(env)
            server = JenkinsClient.server.get(env)
        try:
            return server.get_all_jobs()
        except Exception, e:
            jenkins_logger.exception("get_all_jobs error: %s", e)

    @staticmethod
    def get_job_info(env, name):
        server = JenkinsClient.server.get(env)
        if not server:
            JenkinsClient.get_server(env)
            server = JenkinsClient.server.get(env)
        try:
            return server.get_job_info(name, fetch_all_builds=True)
        except Exception, e:
            jenkins_logger.exception("get_job_info error: %s", e)

    @staticmethod
    def get_build_info(env, job_name, build_number):
        server = JenkinsClient.server.get(env)
        if not server:
            JenkinsClient.get_server(env)
            server = JenkinsClient.server.get(env)
        try:
            return server.get_build_info(job_name, build_number)
        except Exception, e:
            jenkins_logger.exception("get_build_info error: %s", e)

    @staticmethod
    def get_build_console_output(env, job_name, build_number):
        server = JenkinsClient.server.get(env)
        if not server:
            JenkinsClient.get_server(env)
            server = JenkinsClient.server.get(env)
        try:
            return server.get_build_console_output(job_name, build_number)
        except Exception, e:
            jenkins_logger.exception("get_build_console_output error: %s", e)

    @staticmethod
    def get_job_config(env, name):
        server = JenkinsClient.server.get(env)
        if not server:
            JenkinsClient.get_server(env)
            server = JenkinsClient.server.get(env)
        try:
            return server.get_job_config(name)
        except Exception, e:
            jenkins_logger.exception("get_job_config error: %s", e)

    @staticmethod
    def save_job(env, name, template_file, **kwargs):
        jenkins_logger.info("env: {}, name: {}, template_file: {}".format(env, name, template_file))
        jenkins_logger.info("kwargs: {}".format(kwargs))
        data = kwargs
        data['env'] = env
        template = JenkinsClient.jinja2_env.get_template(template_file)
        config_xml = template.render(data)
        server = JenkinsClient.server.get(env)
        if not server:
            JenkinsClient.get_server(env)
            server = JenkinsClient.server.get(env)
        try:
            exist_job_name = server.get_job_name(name)
            if exist_job_name:
                jenkins_logger.info(u"job name {} existed".format(name))
                jenkins_logger.info(u"reconfig_job: {}@{} with {}".format(name, env, template_file))
                jenkins_logger.info(u"data: {}".format(data))
                server.reconfig_job(name, config_xml)
                return True
            else:
                jenkins_logger.info(u"job name {} not exist".format(name))
                jenkins_logger.info(u"create_job: {}@{} with {}".format(name, env, template_file))
                jenkins_logger.info(u"data: {}".format(data))
                server.create_job(name, config_xml)
                return True
        except Exception, e:
            jenkins_logger.exception("save_job error: %s", e)

    @staticmethod
    def build_job(env, name):
        server = JenkinsClient.server.get(env)
        if not server:
            JenkinsClient.get_server(env)
            server = JenkinsClient.server.get(env)
        try:
            server.build_job(name)
            return True
        except Exception, e:
            jenkins_logger.exception("build_job error: %s", e)
