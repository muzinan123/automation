# -*- coding: utf8 -*-

import datetime
from pymongo import ASCENDING, DESCENDING

from app.services.apprepo_service import ApprepoService
from app.mongodb import app_branch_collection
from app.util import Util
from app import root_logger


class AppBranchService(object):

    @staticmethod
    def add_app_branch(project_id, app_id, f_type, vcs_type, app_name, app_type, vcs_full_url):
        try:
            version = AppBranchService.get_app_branch_next_version(project_id, app_id)
            order = AppBranchService.get_app_branch_next_order(project_id, app_type)
            branch_name = "{}_{}_{}".format(datetime.date.strftime(datetime.date.today(), '%Y%m%d'), project_id, version)
            result, info = ApprepoService.create_branch(app_id, branch_name)
            if result:
                if vcs_type == 'svn':
                    app_branch_collection.insert_one({'project_id': project_id, 'app_id': app_id, 'version': version,
                                                      'app_name': app_name, 'app_type': app_type, 'f_type': f_type,
                                                      'vcs_type': vcs_type, 'vcs_full_url': vcs_full_url, 'branch': branch_name,
                                                      'original': info, 'submit_test': 0, "order": order, "enabled": True})
                    return True
                elif vcs_type == 'git':
                    original_commit = ApprepoService.get_current_revision_or_commit(app_id, branch_name=branch_name)
                    app_branch_collection.insert_one({'project_id': project_id, 'app_id': app_id, 'version': version,
                                                      'app_name': app_name, 'app_type': app_type, 'f_type': f_type,
                                                      'vcs_type': vcs_type, 'vcs_full_url': vcs_full_url, 'branch': branch_name,
                                                      'original': original_commit, 'submit_test': "", "order": order, "enabled": True})
                    return True
        except Exception, e:
            root_logger.exception("add_app_branch error: %s", e)

    @staticmethod
    def disable_app_branch(project_id, app_id, version):
        try:
            result = app_branch_collection.update_one({"project_id": project_id, "app_id": app_id, "version": version}, {'$set': {"enabled": False}})
            if result.modified_count == 1:
                return True
        except Exception, e:
            root_logger.exception("del_app_branch error: %s", e)

    @staticmethod
    def mod_app_branch(project_id, app_id, version, f_type=None, order=None, submit_test=None):
        try:
            change = dict()
            if f_type:
                change['f_type'] = f_type
            if submit_test:
                change['submit_test'] = submit_test
            if not order is None:
                change['order'] = order
            result = app_branch_collection.update_one({"project_id": project_id, "app_id": app_id, "version": version},
                                                      {'$set': change})
            if result.modified_count == 1:
                return True
        except Exception, e:
            root_logger.exception("mod_app_branch error: %s", e)

    @staticmethod
    def list_app_branch(project_id, app_type_list):
        records = app_branch_collection.find({"project_id": project_id, "app_type": {"$in": app_type_list}, "enabled": True}, {'_id': False}).sort([('order', ASCENDING)])
        return [e for e in records]

    @staticmethod
    def get_app_branch(project_id, app_id):
        return app_branch_collection.find_one({'project_id': project_id, 'app_id': app_id, 'enabled': True})

    @staticmethod
    def get_app_branch_next_version(project_id, app_id):
        records = app_branch_collection.find({"project_id": project_id, "app_id": app_id}).sort([('version', DESCENDING)]).limit(1)
        version = 0
        for one in records:
            return one.get('version')+1
        return version + 1

    @staticmethod
    def get_app_branch_next_order(project_id, app_type):
        if app_type == 'app':
            records = app_branch_collection.find({"project_id": project_id, "app_type": app_type, "enabled": True}).sort([('order',DESCENDING)]).limit(1)
            for one in records:
                return one.get('order')+1
            return 0
        elif app_type in ['open', 'module']:
            records = app_branch_collection.find({"project_id": project_id, "app_type": {"$in": ['open', 'module']}, "enabled": True}).sort([('order',DESCENDING)]).limit(1)
            for one in records:
                return one.get('order')+1
            return 0
        return 0

    @staticmethod
    def signiture_app_branch(project_id, app_id, branch, original, submit_test):
        message = "{}||{}||{}||{}||{}||{}".format("duang", project_id, app_id, "branch/" + branch, original, submit_test)
        return Util.rsa_encrypt(message)
