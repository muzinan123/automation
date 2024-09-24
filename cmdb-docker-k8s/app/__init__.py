# -*- coding:utf-8 -*-

import logging.config
from flask import Flask
from flask_session import Session
from pymongo import MongoClient
from elasticapm.contrib.flask import ElasticAPM


app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')

apm = ElasticAPM(app)

root_logger = logging.getLogger('')
api_logger = logging.getLogger('api')
out_logger = logging.getLogger('out')
rds_logger = logging.getLogger('white')

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,  # this fixes the problem

    'formatters': {
        'standard': {
            'format': '%(asctime)s %(module)s[%(levelname)s] %(funcName)s@%(lineno)d: %(message)s'
        },
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
        'out': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': app.config['LOG_DIR']+'out.log'
        },
        'white': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': app.config['LOG_DIR']+'white.log'
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
        'out': {
            'handlers': ['out'],
            'level': 'INFO',
            'propagate': False
        },
        'requests': {
            'level': 'WARNING'
        },
        'white': {
            'handlers': ['white'],
            'level': 'INFO',
            'propagate': False
        },
    }
})

api_list = set()

from util import Util
app.config['SESSION_REDIS'] = Util.redis

Session(app)

mongo_client = MongoClient(app.config['MONGO_URI'])
mongodb = mongo_client[app.config['MONGO_DBNAME']]

from app.util import Util
celery = Util.make_celery(app)

from app.views.framework.base_view import baseProfile
app.register_blueprint(baseProfile)

from app.views.docker.engine_view import engineProfile
app.register_blueprint(engineProfile)

from app.views.docker.cluster_view import clusterProfile
app.register_blueprint(clusterProfile)

from app.views.filters import filterProfile
app.register_blueprint(filterProfile)

from app.views.api.core_api_view import coreApiProfile
app.register_blueprint(coreApiProfile)

from app.views.api.api_view import apiProfile
app.register_blueprint(apiProfile)

from app.views.docker.k8s_cluster_view import k8sClusterProfile
app.register_blueprint(k8sClusterProfile)

from app.views.docker.k8s_node_view import k8sNodeProfile
app.register_blueprint(k8sNodeProfile)

from app.views.api.k8s_api_view import k8sApiProfile
app.register_blueprint(k8sApiProfile)
