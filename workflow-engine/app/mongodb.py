# -*- coding: utf8 -*-

from pymongo import MongoClient

from app import app, mongodb

if mongodb is None:
    mongo_client = MongoClient(app.config['MONGO_URI'], maxPoolSize=20)
    mongodb = mongo_client[app.config['MONGO_DBNAME']]

recycle_collection = mongodb.recycle_collection

flow_template_collection = mongodb.flow_template_collection

flow_data_collection = mongodb.flow_data_collection

operation_template_collection = mongodb.operation_template_collection

result_detail_collection = mongodb.result_detail_collection

antx_base_collection = mongodb.antx_base_collection

antx_project_collection = mongodb.antx_project_collection

diamond_collection = mongodb.diamond_collection

app_branch_collection = mongodb.app_branch_collection

maven_dependency_log_collection = mongodb.maven_dependency_log_collection

experienced_app_list_collection = mongodb.experienced_app_list_collection

hot_pool_pre_server_collection = mongodb.hot_pool_pre_server_collection

publish_switch_collection = mongodb.publish_switch_collection

message_collection = mongodb.message_collection

operation_result_collection = mongodb.operation_result_collection

hot_pool_diamond_collection = mongodb.hot_pool_diamond_collection

hot_pool_prd_app_collection = mongodb.hot_pool_prd_app_collection

project_test_collection = mongodb.project_test_collection

notice_system_collection = mongodb.notice_system_collection

# 该集合记录按部门及产品模块统计完成以及废弃的发布信息
product_publish_statistics_collection = mongodb.product_publish_statistics_collection

# 该集合记录按项目统计发布成功及回退的次数信息
project_publish_statistics_collection = mongodb.project_publish_statistics_collection

# 该集合记录不同发布回退原因的次数信息
publish_abandon_statistics_collection = mongodb.publish_abandon_statistics_collection

ci_project_collection = mongodb.ci_project_collection

maven_dependency_preallocation_collection = mongodb.maven_dependency_preallocation_collection

sql_scripts_project_collection = mongodb.sql_scripts_project_collection

aut_ci_project_collection = mongodb.aut_ci_project_collection