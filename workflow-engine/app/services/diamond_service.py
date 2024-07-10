# -*- coding:utf-8 -*-

import datetime

from app.out.diamond import Diamond
from app.models.Diamond import DiamondVersion
from app.models import db
from app.mongodb import diamond_collection
from app import root_logger


class DiamondService(object):

    @staticmethod
    def check_exist(env, data_id):
        diamond_version = DiamondVersion.query.get((data_id, env))
        if diamond_version:
            return True
        content = Diamond.query_diamond(env, data_id)
        if content is not None:
            return True

    @staticmethod
    def query_diamond(env, data_id):
        diamond_version = DiamondVersion.query.get((data_id, env))
        version = 1
        if diamond_version:
            version = diamond_version.version
        content = Diamond.query_diamond(env, data_id)
        ret = dict()
        ret['base_version'] = version
        ret['base_content'] = content
        return ret

    @staticmethod
    def create_project_diamond(project_id, env, data_id, m_type, status, base_version, base_content, content, creator_id):
        try:
            diamond_version = DiamondVersion.query.get((data_id, env))
            if not diamond_version:
                d = DiamondVersion(data_id=data_id, env=env, version=1, create_at=datetime.datetime.now(), creator=creator_id)
                db.session.add(d)
                db.session.commit()
            diamond_collection.insert_one({'project_id': project_id, 'env': env, 'data_id': data_id, 'm_type': m_type,
                                          'status': status, 'version': base_version + 1, 'base_version': base_version,
                                          'content': content, 'base_content': base_content, 'review_status': 'init'})
            return True
        except Exception, e:
            root_logger.exception("create project diamond error: %s", e)

    @staticmethod
    def delete_project_diamond(project_id, env, data_id):
        try:
            diamond_collection.delete_one({"project_id": project_id, "env": env, "data_id": data_id})
            return True
        except Exception, e:
            root_logger.exception("delete project diamond error: %s", e)

    @staticmethod
    def mod_project_diamond(project_id, env, data_id, m_type=None, content=None, review_status=None):
        try:
            change = dict()
            if m_type:
                change['m_type'] = m_type
            if content is not None:
                change['content'] = content
            if review_status is not None:
                change['review_status'] = review_status
            diamond_collection.update_one({'project_id': project_id, 'env': env, 'data_id': data_id}, {'$set': change})
            return True
        except Exception, e:
            root_logger.exception("mod project diamond error: %s", e)

    @staticmethod
    def list_project_diamond(project_id, env=None):
        if env:
            records = diamond_collection.find({"project_id": project_id, "env": env},
                                              {"_id": False, "content": False, "base_content": False})
        else:
            records = diamond_collection.find({"project_id": project_id},
                                              {"_id": False, "content": False, "base_content": False})
        return [e for e in records]

    @staticmethod
    def get_project_diamond(project_id, env, data_id):
        record = diamond_collection.find_one({"project_id": project_id, "env": env, "data_id": data_id}, {"_id": False})
        return record

    @staticmethod
    def commit_project_diamond(project_id, env, m_type):
        project_diamond_list = diamond_collection.find({'project_id': project_id, 'env': env, 'm_type': m_type,
                                                        'status': 'init'})
        error_data_id_list = list()
        for project_diamond in project_diamond_list:
            data_id = project_diamond.get('data_id')
            base_version = project_diamond.get('base_version')
            base_diamond = DiamondVersion.query.get((data_id, env))
            if base_diamond.version != base_version:
                # Diamond已经被另外的发布更新了，需要重新拉取修改再提交
                error_data_id_list.append(data_id)

        if error_data_id_list:
            return False, u"Diamond[{}]已经被另外的发布更新了，需要重新拉取修改再提交".format("; ".join(error_data_id_list))

        project_diamond_list.rewind()
        success_list = list()
        error_list = list()
        for project_diamond in project_diamond_list:
            data_id = project_diamond.get('data_id')
            version = project_diamond.get('version')
            content = project_diamond.get('content')
            base_diamond = DiamondVersion.query.get((data_id, env))
            result = Diamond.save_diamond(env, data_id, content)
            if result:
                diamond_collection.update_one({'project_id': project_id, 'env': env, 'data_id': data_id},
                                              {'$set': {'status': 'success'}})
                base_diamond.version = version
                db.session.commit()
                success_list.append(data_id)
            else:
                error_list.append(data_id)

        if error_list:
            return False, u"部分Diamond提交成功[{}]\n部分Diamond提交失败[{}]".format("; ".join(success_list), "; ".join(error_list))

        return True, u"Diamond提交成功[{}]".format("; ".join(success_list))

    @staticmethod
    def commit_single_diamond(project_id, env, data_id):
        # 用于test和aut环境的直接提交，不进行版本管理控制
        project_diamond = diamond_collection.find_one({'project_id': project_id, 'env': env, 'data_id': data_id})
        content = project_diamond.get('content')
        result = Diamond.save_diamond(env, data_id, content)
        if result:
            diamond_collection.update_one({'project_id': project_id, 'env': env, 'data_id': data_id},
                                          {'$set': {'status': 'success'}})
            return True, u"Diamond提交成功[{}]".format(data_id)
        else:
            return False, u"Diamond提交失败[{}]".format(data_id)

    @staticmethod
    def rollback_project_diamond(project_id, env, m_type):
        project_diamond_list = diamond_collection.find({'project_id': project_id, 'env': env, 'm_type': m_type,
                                                        'status': 'success'})
        for project_diamond in project_diamond_list:
            data_id = project_diamond.get('data_id')
            version = project_diamond.get('version')
            base_version = project_diamond.get('base_version')
            base_content = project_diamond.get('base_content')
            base_diamond = DiamondVersion.query.get((data_id, env))
            if base_diamond.version != version:
                # Diamond已经被另外的发布更新了，无法回滚
                return False, u"Diamond已经被另外的发布更新了，无法回滚"
            result = Diamond.save_diamond(env, data_id, base_content)
            if result:
                diamond_collection.update_one({'project_id': project_id, 'env': env, 'data_id': data_id},
                                              {'$set': {'status': 'init'}})
                base_diamond.version = base_version
                db.session.commit()
        return True, u"成功"

    @staticmethod
    def query_diamond_version(data_id, env):
        # 给老duang使用,接口-查询engine_diamond_version的version
        diamond_version = DiamondVersion.query.get((data_id, env))
        version = 0
        if diamond_version:
            version = diamond_version.version
        return version

    @staticmethod
    def add_diamond_version(data_id, env):
        # 给老duang使用,接口-新增engine_diamond_version
        try:
            d = DiamondVersion(data_id=data_id, env=env, version=1, create_at=datetime.datetime.now(), modify_at=datetime.datetime.now())
            db.session.add(d)
            db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("add engine_diamond_version error: %s", e)

    @staticmethod
    def update_diamond_version(data_id, env):
        # 给老duang使用,接口-更新engine_diamond_version version + 1,如果木有记录则新增
        # 老Duang里已经有判断了，无需再判断version
        try:
            diamond_version = DiamondVersion.query.get((data_id, env))
            if diamond_version:
                diamond_version.version += 1
                diamond_version.modify_at = datetime.datetime.now()
            else:
                d = DiamondVersion(data_id=data_id, env=env, version=1, modify_at=datetime.datetime.now())
                db.session.add(d)
            db.session.commit()
            return True
        except Exception, e:
            root_logger.exception("update engine_diamond_version version error: %s", e)

    @staticmethod
    def query_diamond_by_env(env):
        # westworld使用的接口,根据环境查询DiamondVersion
        dimond_version_list = DiamondVersion.query.filter(DiamondVersion.env == env)
        return [e.serialize() for e in dimond_version_list]

    @staticmethod
    def update_diamond_content_version(data_id, env, content, version, modifier):
        # westworld 更新content和diamond版本
        try:
            diamond_version = DiamondVersion.query.get((data_id, env))
            if diamond_version:
                if diamond_version.version != version:
                    return False, u"Diamond[data_id]已经被另外的发布更新了，需要重新拉取修改再提交"
                diamond_version.version = version + 1
                diamond_version.modifier = modifier
                update_result = Diamond.save_diamond(env, data_id, content)
                if update_result:
                    db.session.commit()
                    return True, ''
                else:
                    return False, u'Diamond 修改server content失败,检查与diamond server连接'
            else:
                return False, u'engine_diamond_version未查到该记录'
        except Exception, e:
            root_logger.exception("update content and version error: %s", e)
            return False, e.message

    @staticmethod
    def sync_diamond_version_from_duang():
        # 临时用于同步新老diamond_version
        import requests, json
        from app.models.Diamond import DiamondVersion
        for env in ['local', 'pre', 'prd']:
            try:
                response = requests.get("https://duang.zhonganonline.com/api/appconfig/queryDiamondByEnv.do?env={}".format(env), timeout=20)
                res = json.loads(response.content)
                if res.get("success") == "true":
                    for diamond_record in res.get("data"):
                        version = diamond_record.get("currentVersion")
                        data_id = diamond_record.get("dataId")
                        env = diamond_record.get("env")
                        d = DiamondVersion(data_id=data_id, env=env, version=version, create_at=datetime.datetime.now(), modify_at=datetime.datetime.now())
                        db.session.add(d)
            except Exception, e:
                print e.message
        db.session.commit()

    @staticmethod
    def sync_antx_base_info_from_duang():
        import requests, json

        from app.services.apprepo_service import ApprepoService

        antx_list = list()
        #for env in ['local', 'test' 'pre', 'prd']:
        response = requests.get("https://duang.zhonganonline.com/api/project/queryList.do", timeout=60)
        file_json = response.content
        for line in json.loads(file_json):
            # line是个dict
            dic = dict()
            app_name = line.get("appName")
            env = line.get('env')
            if env == 'test' or env == 'local':
                continue
            app_id = ApprepoService.get_app_id_by_name(app_name)
            modified_at = datetime.datetime.now()

            content_list = list()
            for row in line.get('fileContent').split("\n"):
                try:
                    content_dict = dict()
                    if row:
                        keys = row.split("=", 1)[0].strip()
                        values = row.split("=", 1)[1].strip()
                        content_dict['k'] = keys
                        content_dict['v'] = values
                        content_list.append(content_dict)
                        #print content_dict
                except Exception, e:
                    pass
                    #print row
                    #print app_name,env,"==================="
                    #f = open("bb.txt", "a+")

                    #f.write(unicode(row) + "--" + unicode(app_name) + "\n")
                    #pass
            dic['app_name'] = app_name
            dic['app_id'] = app_id
            dic['modified_at'] = modified_at
            dic['content'] = content_list
            dic['env'] = env
            if app_id:
                dic['app_id'] = app_id
            else:
                continue
                # dic['app_id'] = ''
                # f = open("aa.txt",'a+')
                # f.write(app_name+"+++")
                # print app_name,"+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
            antx_list.append(dic)
        #print antx_list
        from app.mongodb import antx_base_collection
        antx_base_collection.insert(antx_list)
