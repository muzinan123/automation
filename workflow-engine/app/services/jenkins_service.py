# -*- coding: utf8 -*-

from app.out.jenkins_client import JenkinsClient
from app.out.apprepo import Apprepo
from app import root_logger, app


class JenkinsService(object):

    @staticmethod
    def build_java(env, project_id, publish_id, app_id, svn_path, revision, ext_name, has_first_time):
        try:
            application = Apprepo.get_app_info(app_id)
            if application:
                app_name = application.get('name')
                app_type = application.get('type')
                configs = application.get('configs')
                if configs:
                    jdk_version = configs.get('jdk_version')
                    build_cmd = configs.get('{}_build_cmd'.format(env))
                    if not build_cmd:
                        build_cmd = app.config['APP_DEFAULT_CONFIG'].get('{}-{}'.format(application.get('language'), application.get('type'))).get('{}_build_cmd'.format(env))
                    job_name = "{}_{}_{}".format(publish_id, env, app_name)
                    template_file = 'java-job.xml'
                    description = "env:{}; project_id:{}; publish_id:{}; app_name:{};".format(env, project_id, publish_id, app_name)
                    antx_download_url = app.config['SERVER_URL'] + '/api/common/antx/{}/{}/{}'.format(env, project_id, app_id)
                    api_token = app.config['API_TOKEN_FOR_JENKINS']
                    package_server = app.config['PACKAGE_SERVER']
                    result = JenkinsClient.save_job(env, job_name, template_file, description=description, app=app_name,
                                                    jdk_version=jdk_version, svn_path=svn_path, revision=revision,
                                                    project_id=project_id, publish_id=publish_id, build_cmd=build_cmd,
                                                    antx_download_url=antx_download_url, api_token=api_token,
                                                    app_id=app_id, package_server=package_server, ext_name=ext_name,
                                                    app_type=app_type, has_first_time=has_first_time)
                    if result:
                        job_info = JenkinsClient.get_job_info(env, job_name)
                        if job_info:
                            next_build_number = job_info.get('nextBuildNumber')
                            if JenkinsClient.build_job(env, job_name):
                                return job_name, next_build_number
        except Exception, e:
            root_logger.exception("create_and_build_java error: %s", e)
        return None, None

    @staticmethod
    def build_ci_java(env, app_name, branch_name, jdk_version, vcs_type, vcs_full_url):
        try:
            job_name = "ci_{}_{}".format(app_name, branch_name)
            template_file = 'ci-java-job.xml'
            description = "app_name:{};branch_name:{};".format(app_name, branch_name)
            result = JenkinsClient.save_job(env, job_name, template_file, description=description, app=app_name,
                                            jdk_version=jdk_version, vcs_type=vcs_type, vcs_path=vcs_full_url,
                                            branch_name=branch_name, credentials_id=app.config['CREDENTIALS_ID'])
            if result:
                job_info = JenkinsClient.get_job_info(env, job_name)
                if job_info:
                    next_build_number = job_info.get('nextBuildNumber')
                    if JenkinsClient.build_job(env, job_name):
                        return job_name, next_build_number
        except Exception, e:
            root_logger.exception("create_and_build_ci_java error: %s", e)
        return None, None

    @staticmethod
    def build_aut_ci_java(env, project_id, publish_id, app_id, branch_name, jdk_version, vcs_type, vcs_full_url):
        try:
            application = Apprepo.get_app_info(app_id)
            if application:
                app_name = application.get('name')
                app_type = application.get('type')
                configs = application.get('configs')
                if configs:
                    build_cmd = configs.get('{}_build_cmd'.format(env))
                    if not build_cmd:
                        build_cmd = app.config['APP_DEFAULT_CONFIG'].get('{}-{}'.format(application.get('language'), application.get('type'))).get('{}_build_cmd'.format(env))
                    job_name = "aut_ci_{}_{}".format(app_name, project_id)
                    template_file = 'aut-ci-java-job.xml'
                    description = "app_name:{};branch_name:{};".format(app_name, branch_name)
                    antx_download_url = app.config['SERVER_URL'] + '/api/common/antx/{}/{}/{}'.format(env, project_id, app_id)
                    api_token = app.config['API_TOKEN_FOR_JENKINS']
                    package_server = app.config['PACKAGE_SERVER']
                    result = JenkinsClient.save_job(env, job_name, template_file, description=description, app=app_name,
                                                    jdk_version=jdk_version, vcs_type=vcs_type, vcs_path=vcs_full_url,
                                                    project_id=project_id, publish_id=publish_id, build_cmd=build_cmd,
                                                    antx_download_url=antx_download_url, api_token=api_token,
                                                    app_id=app_id, package_server=package_server, app_type=app_type,
                                                    branch_name=branch_name)
                    if result:
                        job_info = JenkinsClient.get_job_info(env, job_name)
                        if job_info:
                            next_build_number = job_info.get('nextBuildNumber')
                            if JenkinsClient.build_job(env, job_name):
                                return job_name, next_build_number
        except Exception, e:
            root_logger.exception("create_and_build_ci_java error: %s", e)
        return None, None

    @staticmethod
    def rebuild_java(env, job_name):
        try:
            return JenkinsClient.build_job(env, job_name)
        except Exception, e:
            root_logger.exception("rebuild_java error: %s", e)

    @staticmethod
    def get_job_status(env, job_name, build_number):
        return JenkinsClient.get_build_info(env, job_name, build_number)

    @staticmethod
    def get_build_result(env, job_name, build_number):
        return JenkinsClient.get_build_console_output(env, job_name, build_number)
