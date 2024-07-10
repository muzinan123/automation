# -*- coding: utf8 -*-

from app.out.apprepo import Apprepo
from app import root_logger


class ApprepoService(object):

    @staticmethod
    def get_app_info(app_id):
        return Apprepo.get_app_info(app_id)

    @staticmethod
    def get_app_list(query):
        return Apprepo.get_app_list(query)

    @staticmethod
    def list_branch(app_id, directory='branch'):
        return Apprepo.list_branch(app_id, directory=directory)

    @staticmethod
    def create_branch(app_id, branch_name, directory='branch', source='trunk'):
        result = Apprepo.delete_branch(app_id, branch_name, directory=directory)
        if result:
            if result.get('result') == 1 or result.get('info') == 'not existe':
                result = Apprepo.create_branch(app_id, branch_name, directory=directory, source=source)
                if result and result.get('result') == 1:
                    return True, result.get('info')
                else:
                    return False, result.get('info')
            else:
                return False, result.get('info')
        return False, "internal error"

    @staticmethod
    def get_current_revision_or_commit(app_id, branch_name=None, directory='branch'):
        return Apprepo.get_current_revision_or_commit(app_id, svn_relative_path="{}/{}".format(
            directory, branch_name), git_branch_name=branch_name)

    @staticmethod
    def merge(app_id, source, target, svn_revision=None, git_commit_hash=None, commit=False, update_pom=True,
              duang_project_id=None, update_parent_version=True, update_self_version=False, exclude_list=None,
              accept=None):
        try:
            result = Apprepo.merge(app_id, source, target, svn_revision=svn_revision, git_commit_hash=git_commit_hash,
                                   commit=commit, update_pom=update_pom, duang_project_id=duang_project_id,
                                   update_parent_version=update_parent_version, update_self_version=update_self_version,
                                   exclude_list=exclude_list, accept=accept
                                   )
            if result:
                if result.get('result') == 1:
                    return True, result.get('data', None), result.get('info', 'merge success')
                elif result.get('result') == -1:
                    return False, None, "invalid request"
                elif result.get('result') == -2:
                    if result.get('info'):
                        return False, None, result.get('info')
                    elif result.get('data'):
                        return False, None, "conflict: {}".format(",".join(result.get('data')))
                elif result.get('result') == -3:
                    return False, None, result.get('info')
                elif result.get('result') == -10:
                    return False, None, "update pom.xml error"
                elif result.get('result') == -99:
                    return False, None, "unknown error"
        except Exception, e:
            root_logger.exception("merge error: %s", e)
        return False, None, "internal error"

    @staticmethod
    def get_info_from_pom(app_id, branch_name=None, directory='branch', svn_revision=None, git_commit_hash=None):
        return Apprepo.get_info_from_pom(app_id, relative_path="{}/{}".format(directory, branch_name),
                                         branch_name=branch_name, svn_revision=svn_revision,
                                         git_commit_hash=git_commit_hash)

    @staticmethod
    def get_app_id_by_name(name):
        return Apprepo.get_app_id_by_name(name)

    @staticmethod
    def list_app_id_by_user_id(user_id):
        return Apprepo.list_app_id_by_user_id(user_id)

    @staticmethod
    def create_sql_scripts_project(project_id, server_id):
        result, info = Apprepo.create_sql_scripts_project(project_id, server_id)
        return result, info

    @staticmethod
    def get_sql_scripts_project_current_revision(project_id, relative_path):
        result,info = Apprepo.get_sql_scripts_project_current_revision(project_id, relative_path)
        return result, info

    @staticmethod
    def list_project_code_review_status(project_id):
        return Apprepo.list_project_code_review_status(project_id)
