# -*- coding: utf8 -*-

import re
import time
import datetime
import cStringIO
from lxml import etree
from sqlalchemy import desc
from pymongo import ASCENDING, DESCENDING

from app.out.nexus import Nexus
from app.models.Dependency import MavenDependency
from app.models import db
from app.mongodb import maven_dependency_log_collection, maven_dependency_preallocation_collection
from app.util import Util
from app import root_logger


class NexusService(object):

    @staticmethod
    def sync_dependency_from_svn_pom():
        parent_version = Nexus.get_share_version("parent")
        data = Nexus.resolv_parent(parent_version)
        if data:
            parent = MavenDependency(artifact_id='parent', type='parent', version=data.get('version'), modify_at=datetime.datetime.now())
            db.session.merge(parent)
            for dependency in data.get('dependencies'):
                d = MavenDependency(artifact_id=dependency.get('artifactId'), type='share', version=dependency.get('version'), modify_at=datetime.datetime.now())
                db.session.merge(d)
            db.session.commit()

    @staticmethod
    def list_app_dependency(query, order_by='create_at', order_desc=None):
        result = MavenDependency.query.filter(MavenDependency.type == 'share', MavenDependency.artifact_id.like(
            "%" + query + "%") if query else "").order_by(
            desc(eval('MavenDependency.' + order_by)) if order_desc else (eval('MavenDependency.' + order_by)))
        return result

    @staticmethod
    def list_app_dependency_log(share_name, asc=True, order_by='operate_time'):
        regx = re.compile(share_name, re.IGNORECASE)
        pipeline = [
            {'$project': {
                '_id': False
            }},
            {'$match': {
                'artifact_id': regx
            }}
        ]
        if asc:
            pipeline.append({'$sort': {order_by: ASCENDING}})
        else:
            pipeline.append({'$sort': {order_by: DESCENDING}})
        return pipeline, maven_dependency_log_collection

    @staticmethod
    def get_parent_version(project_id=None):
        related_version = maven_dependency_preallocation_collection.find_one({'project_id': project_id, 'artifact_id': 'parent'})
        parent = MavenDependency.query.get('parent')
        if parent:
            if related_version:
                one_version = re.search(r'(\d*)\.(\d*)\.(\d*)', parent.version).groups()
                parent_version = "{}.{}.{}".format(one_version[0], one_version[1], related_version.get('sub_version'))
                return parent_version
            else:
                return parent.version

    @staticmethod
    def get_share_version(artifact_id, project_id=None):
        related_version = maven_dependency_preallocation_collection.find_one({'project_id': project_id, 'artifact_id': artifact_id})
        share = MavenDependency.query.get(artifact_id)
        if share:
            if related_version:
                one_version = re.search(r'(\d*)\.(\d*)\.(\d*)', share.version).groups()
                share_version = "{}.{}.{}".format(one_version[0], one_version[1], related_version.get('sub_version'))
                return share_version
            else:
                return share.version
        elif related_version:
            return "1.0.{}".format(related_version.get('sub_version'))

    @staticmethod
    def preallocate_share_version(artifact_id, project_id):
        while not Util.redis.setnx("lock_{}".format(artifact_id), 1):
            root_logger.info("increase_share_version locked wait 1s for release")
            time.sleep(1)
        try:
            Util.redis.expire("lock_{}".format(artifact_id), 3)
            one = MavenDependency.query.get(artifact_id)
            if one:
                # ArtifactId已存在
                version = re.search(r'(\d*)\.(\d*)\.(\d*)', one.version).groups()
                existed_list = maven_dependency_preallocation_collection.find({'artifact_id': artifact_id}).sort(
                    'sub_version', DESCENDING).limit(1)
                existed_list = [e.get('sub_version') for e in existed_list]
                if existed_list:
                    sub_version = existed_list[0] + 1
                else:
                    sub_version = int(version[2]) + 1
                new_version = "{}.{}.{}".format(version[0], version[1], sub_version)
                maven_dependency_preallocation_collection.insert_one(
                    {'artifact_id': artifact_id, 'sub_version': sub_version, 'project_id': project_id,
                     'create_at': datetime.datetime.utcnow()})
                maven_dependency_log_collection.insert_one(
                    {'artifact_id': artifact_id, 'project_id': project_id, 'version': new_version,
                     'operate_time': datetime.datetime.utcnow(), 'status': 'preallocation'})
            else:
                # 新ArtifactId
                maven_dependency_preallocation_collection.insert_one(
                    {'artifact_id': artifact_id, 'sub_version': 0, 'project_id': project_id,
                     'create_at': datetime.datetime.utcnow()})
                maven_dependency_log_collection.insert_one(
                    {'artifact_id': artifact_id, 'project_id': project_id, 'version': '1.0.0',
                     'operate_time': datetime.datetime.utcnow()})
        except Exception, e:
            root_logger.exception("preallocate_share_version error: %s", e)
        finally:
            Util.redis.delete("lock_{}".format(artifact_id))

    @staticmethod
    def preallocate_parent_version(project_id):
        while not Util.redis.setnx("lock_parent", 1):
            root_logger.info("increase_parent_version locked wait 1s for release")
            time.sleep(1)
        try:
            Util.redis.expire("lock_parent", 3)
            one = MavenDependency.query.get('parent')
            if one:
                version = re.search(r'(\d*)\.(\d*)\.(\d*)', one.version).groups()
                existed_list = maven_dependency_preallocation_collection.find({'artifact_id': 'parent'}).sort(
                    'sub_version', DESCENDING).limit(1)
                existed_list = [e.get('sub_version') for e in existed_list]
                if existed_list:
                    sub_version = existed_list[0] + 1
                else:
                    sub_version = int(version[2]) + 1
                new_version = "{}.{}.{}".format(version[0], version[1], sub_version)
                maven_dependency_preallocation_collection.insert_one(
                    {'artifact_id': 'parent', 'sub_version': sub_version, 'project_id': project_id,
                     'create_at': datetime.datetime.utcnow()})
                maven_dependency_log_collection.insert_one(
                    {'artifact_id': 'parent', 'project_id': project_id, 'version': new_version,
                     'operate_time': datetime.datetime.utcnow(), 'status': 'preallocation'})
        except Exception, e:
            root_logger.exception("preallocate_parent_version error: %s", e)
        finally:
            Util.redis.delete("lock_parent")

    @staticmethod
    def commit_version_by_project_id(project_id):
        try:
            related_version = maven_dependency_preallocation_collection.find({'project_id': project_id})
            for version in related_version:
                artifact_id = version.get('artifact_id')
                sub_version = version.get('sub_version')
                one = MavenDependency.query.get(artifact_id)
                new_version = ''
                if one:
                    # ArtifactId已存在
                    one_version = re.search(r'(\d*)\.(\d*)\.(\d*)', one.version).groups()
                    if int(one_version[2]) < sub_version:
                        new_version = "{}.{}.{}".format(one_version[0], one_version[1], sub_version)
                        one.version = new_version
                        db.session.commit()
                else:
                    # 新ArtifactId
                    if 0 < sub_version:
                        new_version = "1.0.{}".format(sub_version)
                    else:
                        new_version = "1.0.0"
                    d = MavenDependency(artifact_id=artifact_id, type='share', version=new_version,
                                        modify_at=datetime.datetime.now())
                    db.session.merge(d)
                    db.session.commit()
                maven_dependency_preallocation_collection.delete_one({'project_id': project_id, 'artifact_id': artifact_id})
                maven_dependency_log_collection.update_many({'artifact_id': artifact_id, 'project_id': project_id, 'version': new_version}, {'$set': {'status': 'commited'}})
            return True
        except Exception, e:
            root_logger.exception("commit_version_by_project_id error: %s", e)

    @staticmethod
    def release_version_by_project_id(project_id):
        try:
            maven_dependency_preallocation_collection.delete_many({'project_id': project_id})
            maven_dependency_log_collection.update_many(
                {'project_id': project_id, 'status': 'preallocation'}, {'$set': {'status': 'released'}})
            return True
        except Exception, e:
            root_logger.exception("release_version_by_project_id error: %s", e)

    @staticmethod
    def mod_version(artifact_id, version, modifier='system'):
        try:
            one = MavenDependency.query.get(artifact_id)
            if one:
                one.version = version
                one.modify_at = datetime.datetime.now()
                db.session.commit()
                maven_dependency_log_collection.insert_one(
                    {'artifact_id': artifact_id, 'project_id': "-1", 'version': version,
                     'operate_time': datetime.datetime.utcnow(), 'modifier': modifier})
                return True
        except Exception, e:
            root_logger.exception("mod_version error: %s", e)

    @staticmethod
    def generate_pom(project_id=None):
        related_version_dict = dict()
        if project_id:
            related_version = maven_dependency_preallocation_collection.find({'project_id': project_id})
            for version in related_version:
                artifact_id = version.get('artifact_id')
                sub_version = version.get('sub_version')
                related_version_dict[artifact_id] = sub_version
        l = MavenDependency.query.filter()
        app_version_list = list()
        parent_version = ''
        for one in l:
            if one.type == 'parent':
                parent_version = one.version
                pv = related_version_dict.pop('parent') if 'parent' in related_version_dict.keys() else None
                if pv is not None:
                    one_version = re.search(r'(\d*)\.(\d*)\.(\d*)', parent_version).groups()
                    parent_version = "{}.{}.{}".format(one_version[0], one_version[1], pv)
            else:
                av = related_version_dict.pop(one.artifact_id) if one.artifact_id in related_version_dict.keys() else None
                if av is not None:
                    one_version = re.search(r'(\d*)\.(\d*)\.(\d*)', one.version).groups()
                    share_version = "{}.{}.{}".format(one_version[0], one_version[1], av)
                    app_version_list.append({'artifactId': one.artifact_id, 'version': share_version})
                else:
                    app_version_list.append({'artifactId': one.artifact_id, 'version': one.version})
        for artifact_id, sub_version in related_version_dict.items():
            share_version = "1.0.{}".format(sub_version)
            app_version_list.append({'artifactId': artifact_id, 'version': share_version})
        return Nexus.generate_parent(parent_version, app_version_list)

    @staticmethod
    def update_app_pom(stream, parent_version=True, self_version=False, project_id=None):
        related_version_dict = dict()
        if project_id:
            related_version = maven_dependency_preallocation_collection.find({'project_id': project_id})
            for version in related_version:
                artifact_id = version.get('artifact_id')
                sub_version = version.get('sub_version')
                related_version_dict[artifact_id] = sub_version
        parent_latest_version = NexusService.get_parent_version()

        pv = related_version_dict.pop('parent') if 'parent' in related_version_dict.keys() else None
        if pv is not None:
            one_version = re.search(r'(\d*)\.(\d*)\.(\d*)', parent_latest_version).groups()
            parent_latest_version = "{}.{}.{}".format(one_version[0], one_version[1], pv)
        doc = etree.parse(stream)
        if parent_version:
            if doc.xpath('./p:parent/p:groupId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'}) and doc.xpath('./p:parent/p:groupId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text == 'com.zhongan':
                if doc.xpath('./p:parent/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'}):
                    doc.xpath('./p:parent/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text = parent_latest_version
            else:
                group_id_list = doc.xpath('./p:dependencyManagement/p:dependencies/p:dependency/p:groupId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
                for i in range(len(group_id_list)):
                    if group_id_list[i].text == 'com.zhongan':
                        if doc.xpath('./p:dependencyManagement/p:dependencies/p:dependency/p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[i].text == 'parent':
                            doc.xpath('./p:dependencyManagement/p:dependencies/p:dependency/p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[i].text = parent_latest_version
        if self_version:
            artifact_id = doc.xpath('./p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text
            share_latest_version = NexusService.get_share_version(artifact_id, project_id=project_id)
            if share_latest_version:
                if doc.xpath('./p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'}):
                    doc.xpath('./p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text = share_latest_version
        strIO = cStringIO.StringIO()
        etree.ElementTree(doc.getroot()).write(strIO, pretty_print=True, xml_declaration=True, encoding='utf-8')
        return strIO

    @staticmethod
    def upload_parent_pom(project_id=None):
        parent_pom_file = NexusService.generate_pom(project_id=project_id)
        result = Nexus.upload_parent_pom(parent_pom_file)
        return result
