# -*- coding: utf8 -*-

import os
import logging.config
from flask_socketio import SocketIO
from flask import Flask
from flask_session import Session
from elasticapm.contrib.flask import ElasticAPM

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')

apm = ElasticAPM(app)

root_logger = logging.getLogger('')
api_logger = logging.getLogger('api')
salt_logger = logging.getLogger('salt')
out_logger = logging.getLogger('out')
workflow_logger = logging.getLogger('workflow')
jenkins_logger = logging.getLogger('jenkins')
apprepo_logger = logging.getLogger('apprepo')
kafka_logger = logging.getLogger('kafka')
task_logger = logging.getLogger('task')
idb_logger = logging.getLogger('idb')

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,  # this fixes the problem
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(module)s[%(levelname)s] %(funcName)s@%(lineno)d: %(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'api': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': app.config['LOG_DIR']+'api.log'
        },
        'salt': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': app.config['LOG_DIR']+'salt.log'
        },
        'out': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': app.config['LOG_DIR']+'out.log'
        },
        'workflow': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': app.config['LOG_DIR']+'workflow.log'
        },
        'jenkins': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': app.config['LOG_DIR']+'jenkins.log'
        },
        'apprepo': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': app.config['LOG_DIR']+'apprepo.log'
        },
        'kafka': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': app.config['LOG_DIR']+'kafka.log'
        },
        'task': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': app.config['LOG_DIR']+'task.log'
        },
        'idb': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': app.config['LOG_DIR']+'idb.log'
        }
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        },
        'api': {
            'handlers': ['api'],
            'level': 'INFO',
            'propagate': False
        },
        'salt': {
            'handlers': ['salt'],
            'level': 'INFO',
            'propagate': False
        },
        'out': {
            'handlers': ['out'],
            'level': 'INFO',
            'propagate': False
        },
        'workflow': {
            'handlers': ['workflow'],
            'level': 'INFO',
            'propagate': False
        },
        'jenkins': {
            'handlers': ['jenkins'],
            'level': 'INFO',
            'propagate': False
        },
        'apprepo': {
            'handlers': ['apprepo'],
            'level': 'INFO',
            'propagate': False
        },
        'kafka': {
            'handlers': ['kafka'],
            'level': 'INFO',
            'propagate': False
        },
        'task': {
            'handlers': ['task'],
            'level': 'INFO',
            'propagate': False
        },
        'sqlalchemy.engine': {
            'handlers': ['default'],
            'level': 'ERROR',
            'propagate': False
        },
        'requests': {
            'handlers': ['out'],
            'level': 'WARNING',
            'propagate': False
        },
        'socketio': {
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False
        },
        'engineio': {
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False
        },
        'idb': {
            'handlers': ['idb'],
            'level': 'INFO',
            'propagate': False
        }
    }
})

api_list = set()

from app.util import Util
app.config['SESSION_REDIS'] = Util.redis

Session(app)

celery = Util.make_celery(app)

mongodb = None

if os.environ.get('_IN_CELERY') == '1':
    socketio = SocketIO(message_queue="redis://:{}@{}:{}/{}".format(app.config['REDIS_PASS'], app.config['REDIS_HOST'], app.config['REDIS_PORT'], app.config['REDIS_DB']))
else:
    socketio = SocketIO(app, message_queue="redis://:{}@{}:{}/{}".format(app.config['REDIS_PASS'], app.config['REDIS_HOST'], app.config['REDIS_PORT'], app.config['REDIS_DB']))

from app.views.framework.base_view import baseProfile
app.register_blueprint(baseProfile, url_prefix='')

from app.views.flow_view import flowProfile
app.register_blueprint(flowProfile, url_prefix='/flow')

from app.views.filter import filterProfile
app.register_blueprint(filterProfile)

from app.views.func_view import funcProfile
app.register_blueprint(funcProfile, url_prefix='/func')

from app.views.antx_view import antxProfile
app.register_blueprint(antxProfile, url_prefix='/antx')

from app.views.diamond_view import diamondProfile
app.register_blueprint(diamondProfile, url_prefix='/diamond')

from app.views.nexus_view import nexusProfile
app.register_blueprint(nexusProfile, url_prefix='/nexus')

from app.views.operation_view import operationProfile
app.register_blueprint(operationProfile, url_prefix="/operation")

from app.views.api.common_api import commonApiProfile
app.register_blueprint(commonApiProfile, url_prefix="/api/common")

from app.views.api.flow_api import flowApiProfile
app.register_blueprint(flowApiProfile, url_prefix="/api/flow")

from app.views.app_branch_view import appBranchProfile
app.register_blueprint(appBranchProfile, url_prefix="/app-branch")

from app.views.publish_view import publishProfile
app.register_blueprint(publishProfile, url_prefix='/publish')

from app.views.notice_system import noticeSystem
app.register_blueprint(noticeSystem, url_prefix='/notice-system')

from app.views.project_view import projectProfile
app.register_blueprint(projectProfile, url_prefix="/project")

from app.views.jira_view import jiraProfile
app.register_blueprint(jiraProfile, url_prefix="/jira")

from app.views.framework.kafka_view import kafkaProfile
app.register_blueprint(kafkaProfile, url_prefix="/kafka")

from app.views.api.project_api import projectApiProfile
app.register_blueprint(projectApiProfile, url_prefix="/api/project")

from app.views.api.publish_api import publishApiProfile
app.register_blueprint(publishApiProfile, url_prefix="/api/publish")

from app.views.publish_statistics_view import publishStatisticsProfile
app.register_blueprint(publishStatisticsProfile, url_prefix="/publish/statistics")

from app.views.ci_project_view import ciProjectProfile
app.register_blueprint(ciProjectProfile, url_prefix="/ci-project")

from app.views.apprepo_view import appRepoProfile
app.register_blueprint(appRepoProfile, url_prefix="/apprepo")

from app.views.aut_ci_project_view import autciProjectProfile
app.register_blueprint(autciProjectProfile, url_prefix="/aut-ci-project")