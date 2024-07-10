# -*- coding: utf8 -*-

import requests
from requests.auth import HTTPBasicAuth
import datetime
from lxml import etree
import cStringIO

from app import app, out_logger


class Nexus(object):

    @staticmethod
    def get_share_version(app_name):
        try:
            url = "{}/nexus/service/local/repositories/{}/content/com/zhongan/{}".format(app.config['NEXUS_URL'], app.config['NEXUS_REPO_NAME'], app_name)
            response = requests.get(url, headers={'accept': 'application/json'})
            if response.status_code == 200:
                data = response.json().get('data')
                last_date = datetime.datetime.strptime("2000-01-01", "%Y-%m-%d")
                ret = dict()
                for one in data:
                    if not one.get('leaf'):
                        d = datetime.datetime.strptime(one.get('lastModified'), "%Y-%m-%d %H:%M:%S.0 UTC")
                        ret[d] = one.get('text')
                        if d > last_date:
                            last_date = d
                return ret.get(last_date)
        except Exception, e:
            out_logger.exception("get_share_version error: %s", e)

    @staticmethod
    def resolv_parent(parent_version):
        try:
            url = "{}/nexus/service/local/repositories/{}/content/com/zhongan/parent/{}/parent-{}.pom".format(app.config['NEXUS_URL'], app.config['NEXUS_REPO_NAME'], parent_version, parent_version)
            response = requests.get(url)
            if response.status_code == 200:
                root = etree.fromstring(response.content)
                ret = dict()
                ret['modelVersion'] = root.xpath('./p:modelVersion', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text
                ret['name'] = root.xpath('./p:name', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text
                ret['groupId'] = root.xpath('./p:groupId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text
                ret['artifactId'] = root.xpath('./p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text
                ret['version'] = root.xpath('./p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text
                ret['packaging'] = root.xpath('./p:packaging', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text
                ret['version'] = root.xpath('./p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text
                dependency_list = root.xpath('./p:dependencyManagement/p:dependencies/p:dependency',
                                             namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})
                ret['dependencies'] = list()
                for dependency in dependency_list:
                    groupId = dependency.xpath('./p:groupId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text
                    artifactId = dependency.xpath('./p:artifactId', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text
                    version = dependency.xpath('./p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text
                    ret['dependencies'].append({'groupId': groupId, 'artifactId': artifactId, 'version': version})
                return ret
        except Exception, e:
            out_logger.exception("resolv_parent error: %s", e)

    @staticmethod
    def generate_parent(parent_version, app_version_list):
        try:
            doc = etree.parse('nexus_parent/parent.pom.template.xml')
            doc.xpath('./p:version', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0].text = parent_version
            dependencies = doc.xpath('./p:dependencyManagement/p:dependencies', namespaces={'p': 'http://maven.apache.org/POM/4.0.0'})[0]

            for app_version in app_version_list:
                dependency = etree.Element('{http://maven.apache.org/POM/4.0.0}dependency',
                                           nsmap={'None': 'http://maven.apache.org/POM/4.0.0'})
                groupId = etree.Element('{http://maven.apache.org/POM/4.0.0}groupId',
                                        nsmap={'None': 'http://maven.apache.org/POM/4.0.0'})
                groupId.text = "com.zhongan"
                artifactId = etree.Element('{http://maven.apache.org/POM/4.0.0}artifactId',
                                        nsmap={'None': 'http://maven.apache.org/POM/4.0.0'})
                artifactId.text = app_version.get('artifactId')
                version = etree.Element('{http://maven.apache.org/POM/4.0.0}version',
                                        nsmap={'None': 'http://maven.apache.org/POM/4.0.0'})
                version.text = app_version.get('version')
                dependency.insert(0, groupId)
                dependency.insert(1, artifactId)
                dependency.insert(2, version)
                dependencies.insert(0, dependency)
            strIO = cStringIO.StringIO()
            etree.ElementTree(doc.getroot()).write(strIO, pretty_print=True,
                                                   xml_declaration=True, encoding='utf-8')
            return strIO
        except Exception, e:
            out_logger.exception("generate_parent error: %s", e)

    @staticmethod
    def upload_parent_pom(pom_file):
        try:
            pom_file.seek(0)
            files = {'file': ('pom.xml', pom_file, 'text/xml')}
            data = dict()
            data['hasPom'] = 'true'
            data['r'] = app.config['NEXUS_REPO_NAME']
            url = '{}/nexus/service/local/artifact/maven/content'.format(app.config['NEXUS_URL'])
            response = requests.post(url, data=data, files=files, auth=HTTPBasicAuth(app.config['NEXUS_USER'], app.config['NEXUS_PASSWORD']))
            out_logger.info(response.status_code)
            out_logger.info(response.content)
            if response.status_code == 201:
                return True, response.content
            else:
                return False, response.content
        except Exception, e:
            out_logger.exception("upload_parent_pom error: %s", e)
