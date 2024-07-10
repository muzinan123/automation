# -*- coding:utf8 -*-

from pepper import Pepper
from app.util import Util
from app import app, salt_logger


class Saltstack(object):

    @staticmethod
    def login(company, env):
        try:
            url = app.config.get('SALT_{}_{}_API_URL'.format(company, env.upper()))
            if url:
                api = Pepper(url)
                login_info = api.login(app.config['SALT_{}_{}_API_USER'.format(company, env.upper())], app.config['SALT_{}_{}_API_PASS'.format(company, env.upper())], 'pam')
                token = login_info.get('token')
                Util.redis.set('salt_token_{}_{}'.format(company, env), token)
                Util.redis.expire('salt_token_{}_{}'.format(company, env), 1800)
        except Exception, e:
            salt_logger.exception('login error: %s', e)

    @staticmethod
    def get_api(company, env):
        token = Util.redis.get('salt_token_{}_{}'.format(company, env))
        if not token:
            return None
        url = app.config.get('SALT_{}_{}_API_URL'.format(company, env.upper()))
        api = Pepper(url)
        api.auth['token'] = token
        return api

    @staticmethod
    def test_ping(company, env, target):
        api = Saltstack.get_api(company, env)
        if not api:
            Saltstack.login(company, env)
            api = Saltstack.get_api(company, env)
        if api:
            req = list()
            req.append({'client': 'local', 'tgt': target, 'fun': 'test.ping'})
            try:
                for r in api.low(req).get('return'):
                    for k, v in r.items():
                        if k == target:
                            return v
            except Exception, e:
                Util.redis.delete('salt_token_{}_{}'.format(company, env))
                salt_logger.exception("test_ping error: %s", e)

    @staticmethod
    def app_init_war(company, env, target, app_name="", jdk_ver="", start_port="", shut_port="", jvm_size="", new_size="", perm_size="", rpc_provider=""):
        pillar_params = {"appname": app_name,
                         "jdk_ver": jdk_ver,
                         "rpc_provider": rpc_provider
                         }
        if start_port:
            pillar_params['start_port'] = start_port
        if shut_port:
            pillar_params['shut_port'] = shut_port
        if jvm_size:
            pillar_params['jvm_size'] = jvm_size
        if new_size:
            pillar_params['new_size'] = new_size
        if perm_size:
            pillar_params['perm_size'] = perm_size
        pillar = {'pillar': pillar_params, 'mods': 'pe.app_init.war', 'queue': True}
        salt_logger.info("company, env, target: {}, {}, {}".format(company, env, target))
        salt_logger.info(pillar)
        api = Saltstack.get_api(company, env)
        if not api:
            Saltstack.login(company, env)
            api = Saltstack.get_api(company, env)
        if api:
            req = list()
            req.append({'client': 'local', 'tgt': target, 'fun': 'state.sls', 'kwarg': pillar})
            try:
                result = api.low(req).get('return')
                salt_logger.info(result)
                for r in result:
                    for k, v in r.items():
                        if k == target:
                            return Saltstack.check_result(v)
            except Exception, e:
                Util.redis.delete('salt_token_{}_{}'.format(company, env))
                salt_logger.exception("app init war error: %s", e)
                return False

    @staticmethod
    def app_init_jar(company, env, target, app_name="", jdk_ver="", extra_options="", jvm_size="", new_size="", perm_size="", rpc_provider=""):
        pillar_params = {"appname": app_name,
                         "jdk_ver": jdk_ver,
                         "rpc_provider": rpc_provider
                         }
        if jvm_size:
            pillar_params['jvm_size'] = jvm_size
        if new_size:
            pillar_params['new_size'] = new_size
        if perm_size:
            pillar_params['perm_size'] = perm_size
        if extra_options:
            pillar_params['extra_options'] = extra_options
        pillar = {'pillar': pillar_params, 'mods': 'pe.app_init.jar', 'queue': True}
        salt_logger.info("company, env, target: {}, {}, {}".format(company, env, target))
        salt_logger.info(pillar)
        api = Saltstack.get_api(company, env)
        if not api:
            Saltstack.login(company, env)
            api = Saltstack.get_api(company, env)
        if api:
            req = list()
            req.append({'client': 'local', 'tgt': target, 'fun': 'state.sls', 'kwarg': pillar})
            try:
                result = api.low(req).get('return')
                salt_logger.info(result)
                for r in result:
                    for k, v in r.items():
                        if k == target:
                            return Saltstack.check_result(v)
            except Exception, e:
                Util.redis.delete('salt_token_{}_{}'.format(company, env))
                salt_logger.exception("app init jar error: %s", e)
                return False

    @staticmethod
    def del_app(company, env, target, app_name=""):
        pillar = {'pillar': {"appname": app_name,
                             "action": "force"
                             },
                  'mods': 'pe.app_init.del_app',
                  'queue': True
                  }
        salt_logger.info("company, env, target: {}, {}, {}".format(company, env, target))
        salt_logger.info(pillar)
        api = Saltstack.get_api(company, env)
        if not api:
            Saltstack.login(company, env)
            api = Saltstack.get_api(company, env)
        if api:
            req = list()
            req.append({'client': 'local', 'tgt': target, 'fun': 'state.sls', 'kwarg': pillar})
            try:
                result = api.low(req).get('return')
                salt_logger.info(result)
                for r in result:
                    for k, v in r.items():
                        if k == target:
                            return Saltstack.check_result(v)
            except Exception, e:
                Util.redis.delete('salt_token_{}_{}'.format(company, env))
                salt_logger.exception("app del error: %s", e)
                return False

    @staticmethod
    def stop_app(company, env, target, app_name="", port=""):
        pillar = {'pillar': {"appname": app_name,
                             "start_port": port
                             },
                  'mods': 'pe.srv_control.stop',
                  'queue': True
                  }
        salt_logger.info("company, env, target: {}, {}, {}".format(company, env, target))
        salt_logger.info(pillar)
        api = Saltstack.get_api(company, env)
        if not api:
            Saltstack.login(company, env)
            api = Saltstack.get_api(company, env)
        if api:
            req = list()
            req.append({'client': 'local', 'tgt': target, 'fun': 'state.sls', 'kwarg': pillar})
            try:
                result = api.low(req).get('return')
                salt_logger.info(result)
                for r in result:
                    for k, v in r.items():
                        if k == target:
                            return Saltstack.check_result(v)
            except Exception, e:
                Util.redis.delete('salt_token_{}_{}'.format(company, env))
                salt_logger.exception("stop app error: %s", e)
                return False

    @staticmethod
    def start_app(company, env, target, app_name="", port=""):
        pillar = {'pillar': {"appname": app_name,
                             "start_port": port
                             },
                  'mods': 'pe.srv_control.start',
                  'queue': True
                  }
        salt_logger.info("company, env, target: {}, {}, {}".format(company, env, target))
        salt_logger.info(pillar)
        api = Saltstack.get_api(company, env)
        if not api:
            Saltstack.login(company, env)
            api = Saltstack.get_api(company, env)
        if api:
            req = list()
            req.append({'client': 'local', 'tgt': target, 'fun': 'state.sls', 'kwarg': pillar})
            try:
                result = api.low(req).get('return')
                salt_logger.info(result)
                for r in result:
                    for k, v in r.items():
                        if k == target:
                            return Saltstack.check_result(v)
            except Exception, e:
                Util.redis.delete('salt_token_{}_{}'.format(company, env))
                salt_logger.exception("start app error: %s", e)
                return False

    @staticmethod
    def restart_app(company, env, target, app_name="", port=""):
        pillar = {'pillar': {"appname": app_name,
                             "start_port": port
                             },
                  'mods': 'pe.srv_control.restart',
                  'queue': True
                  }
        salt_logger.info("company, env, target: {}, {}, {}".format(company, env, target))
        salt_logger.info(pillar)
        api = Saltstack.get_api(company, env)
        if not api:
            Saltstack.login(company, env)
            api = Saltstack.get_api(company, env)
        if api:
            req = list()
            req.append({'client': 'local', 'tgt': target, 'fun': 'state.sls', 'kwarg': pillar})
            try:
                result = api.low(req).get('return')
                salt_logger.info(result)
                for r in result:
                    for k, v in r.items():
                        if k == target:
                            return Saltstack.check_result(v)
            except Exception, e:
                Util.redis.delete('salt_token_{}_{}'.format(company, env))
                salt_logger.exception("restart app error: %s", e)
                return False

    @staticmethod
    def clean_env(company, env, target, app_name=""):
        pillar = {'pillar': {"appname": app_name},
                  'mods': 'pe.srv_control.cleaning_env',
                  'queue': True
                  }
        salt_logger.info("company, env, target: {}, {}, {}".format(company, env, target))
        salt_logger.info(pillar)
        api = Saltstack.get_api(company, env)
        if not api:
            Saltstack.login(company, env)
            api = Saltstack.get_api(company, env)
        if api:
            req = list()
            req.append({'client': 'local', 'tgt': target, 'fun': 'state.sls', 'kwarg': pillar})
            try:
                result = api.low(req).get('return')
                salt_logger.info(result)
                for r in result:
                    for k, v in r.items():
                        if k == target:
                            return Saltstack.check_result(v)
            except Exception, e:
                Util.redis.delete('salt_token_{}_{}'.format(company, env))
                salt_logger.exception("clean env error: %s", e)
                return False

    @staticmethod
    def upload_package(company, env, target, app_name=None, pack_serv_url=None, need_uncomp=False, unzip_dir=None):
        pillar = {'pillar': {"appname": app_name,
                             "pack_serv_url": pack_serv_url,
                             "need_uncomp": 'yes' if need_uncomp else 'no',
                             "unzip_dir": unzip_dir,
                             },
                  'mods': 'pe.srv_control.package_ctl',
                  'queue': True
                  }
        salt_logger.info("company, env, target: {}, {}, {}".format(company, env, target))
        salt_logger.info(pillar)
        api = Saltstack.get_api(company, env)
        if not api:
            Saltstack.login(company, env)
            api = Saltstack.get_api(company, env)
        if api:
            req = list()
            req.append({'client': 'local', 'tgt': target, 'fun': 'state.sls', 'kwarg': pillar})
            try:
                result = api.low(req).get('return')
                salt_logger.info(result)
                for r in result:
                    for k, v in r.items():
                        if k == target:
                            return Saltstack.check_result(v)
            except Exception, e:
                Util.redis.delete('salt_token_{}_{}'.format(company, env))
                salt_logger.exception("upload package error: %s", e)
                return False

    @staticmethod
    def dzbd_pre_publish(company, env, target, branch=None, svn_revision=None, dir_path=None, retry=None, user=None, password=None):
        pillar = {'pillar': {"branch": branch,
                             "svn_revision": svn_revision,
                             "dir_path": dir_path,
                             "retry": "yes" if retry else "no",
                             "user": user,
                             "passwd": password
                             },
                  'mods': 'pe.file_publish.dzbd_pre',
                  'queue': True
                  }
        salt_logger.info("company, env, target: {}, {}, {}".format(company, env, target))
        salt_logger.info(pillar)
        api = Saltstack.get_api(company, env)
        if not api:
            Saltstack.login(company, env)
            api = Saltstack.get_api(company, env)
        if api:
            req = list()
            req.append({'client': 'local', 'tgt': target, 'fun': 'state.sls', 'kwarg': pillar})
            try:
                result = api.low(req).get('return')
                salt_logger.info(result)
                for r in result:
                    for k, v in r.items():
                        if k == target:
                            return Saltstack.check_result(v)
            except Exception, e:
                Util.redis.delete('salt_token_{}_{}'.format(company, env))
                salt_logger.exception("dzbd pre publish error: %s", e)
                return False

    @staticmethod
    def dzbd_pre_rollback(company, env, target, user=None, password=None):
        pillar = {'pillar': {"user": user,
                             "passwd": password
                             },
                  'mods': 'pe.file_publish.dzbd_pre_rollback',
                  'queue': True
                  }
        salt_logger.info("company, env, target: {}, {}, {}".format(company, env, target))
        salt_logger.info(pillar)
        api = Saltstack.get_api(company, env)
        if not api:
            Saltstack.login(company, env)
            api = Saltstack.get_api(company, env)
        if api:
            req = list()
            req.append({'client': 'local', 'tgt': target, 'fun': 'state.sls', 'kwarg': pillar})
            try:
                result = api.low(req).get('return')
                salt_logger.info(result)
                for r in result:
                    for k, v in r.items():
                        if k == target:
                            return Saltstack.check_result(v)
            except Exception, e:
                Util.redis.delete('salt_token_{}_{}'.format(company, env))
                salt_logger.exception("dzbd pre roll back error: %s", e)
                return False

    @staticmethod
    def dzbd_prd_publish(company, env, target, svn_revision=None, dir_path=None, user=None, password=None):
        pillar = {'pillar': {"svn_revision": svn_revision,
                             "dir_path": dir_path,
                             "user": user,
                             "passwd": password
                             },
                  'mods': 'pe.file_publish.dzbd_prd',
                  'queue': True
                  }
        salt_logger.info("company, env, target: {}, {}, {}".format(company, env, target))
        salt_logger.info(pillar)
        api = Saltstack.get_api(company, env)
        if not api:
            Saltstack.login(company, env)
            api = Saltstack.get_api(company, env)
        if api:
            req = list()
            req.append({'client': 'local', 'tgt': target, 'fun': 'state.sls', 'kwarg': pillar})
            try:
                result = api.low(req).get('return')
                salt_logger.info(result)
                for r in result:
                    for k, v in r.items():
                        if k == target:
                            return Saltstack.check_result(v)
            except Exception, e:
                Util.redis.delete('salt_token_{}_{}'.format(company, env))
                salt_logger.exception("dzbd prd publish error: %s", e)
                return False

    @staticmethod
    def dzbd_prd_rollback(company, env, target, user=None, password=None):
        pillar = {'pillar': {"user": user,
                             "passwd": password
                             },
                  'mods': 'pe.file_publish.dzbd_prd_rollback',
                  'queue': True
                  }
        salt_logger.info("company, env, target: {}, {}, {}".format(company, env, target))
        salt_logger.info(pillar)
        api = Saltstack.get_api(company, env)
        if not api:
            Saltstack.login(company, env)
            api = Saltstack.get_api(company, env)
        if api:
            req = list()
            req.append({'client': 'local', 'tgt': target, 'fun': 'state.sls', 'kwarg': pillar})
            try:
                result = api.low(req).get('return')
                salt_logger.info(result)
                for r in result:
                    for k, v in r.items():
                        if k == target:
                            return Saltstack.check_result(v)
            except Exception, e:
                Util.redis.delete('salt_token_{}_{}'.format(company, env))
                salt_logger.exception("dzbd prd roll back error: %s", e)
                return False

    @staticmethod
    def archive_log(company, env, target, app_name=""):
        pillar = {'pillar': {"appname": app_name},
                  'mods': 'pe.archivelog.today',
                  'queue': True
                  }
        salt_logger.info("company, env, target: {}, {}, {}".format(company, env, target))
        salt_logger.info(pillar)
        api = Saltstack.get_api(company, env)
        if not api:
            Saltstack.login(company, env)
            api = Saltstack.get_api(company, env)
        if api:
            req = list()
            req.append({'client': 'local', 'tgt': target, 'fun': 'state.sls', 'kwarg': pillar})
            try:
                result = api.low(req).get('return')
                salt_logger.info(result)
                for r in result:
                    for k, v in r.items():
                        if k == target:
                            return Saltstack.check_result(v)
            except Exception, e:
                Util.redis.delete('salt_token_{}_{}'.format(company, env))
                salt_logger.exception("archive log error: %s", e)
                return False

    @staticmethod
    def check_result(v):
        if type(v).__name__ == 'dict':
            result_list = [e.get('result') for e in v.values()]
            if not False in result_list:
                return True
        return False
