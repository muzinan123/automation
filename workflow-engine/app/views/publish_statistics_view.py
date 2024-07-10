# -*- coding:utf8 -*-

from flask import Blueprint, jsonify, render_template, request, send_file
from app.decorators.access_controle import require_login
from app.services.publish.publish_statistics_service import PublishStatisticsService
from app.util import Util

publishStatisticsProfile = Blueprint('publishStatisticsProfile', __name__)


@publishStatisticsProfile.route('/list', methods=['GET'])
@require_login()
def publish_statistics():
    return render_template('publish/statistics/publish-statistics.html')

# 按产品模块统计发布成功率
@publishStatisticsProfile.route('/list/all', methods=['GET'])
@require_login()
def get_publish_statistics():
    ret = dict()
    query = request.values.get('query', None)
    begin_date = request.values.get('begin_date')
    end_date = request.values.get('end_date')
    group = request.values.get('group')
    result, total = PublishStatisticsService.get_publish_statistics(begin_date, end_date, group, query)
    ret['result'] = 1
    ret['data'] = result
    ret['total'] = total
    return jsonify(ret)

# 发布项目回退原因统计
@publishStatisticsProfile.route('/abandon', methods=['GET'])
@require_login()
def get_publish_abandon_statistics():
    begin_date = request.values.get('begin_date')
    end_date = request.values.get('end_date')
    ret = dict()
    result = PublishStatisticsService.get_abandon_statistics(begin_date, end_date)
    ret['result'] = 1
    ret['data'] = result
    return jsonify(ret)

# 发布项目退回次数前10统计
@publishStatisticsProfile.route('/abandon/top10', methods=['GET'])
@require_login()
def get_publish_abandon_statistics_top10():
    begin_date = request.values.get('begin_date')
    end_date = request.values.get('end_date')
    ret = dict()
    result = PublishStatisticsService.get_project_abandon_statistics(begin_date, end_date)
    ret['result'] = 1
    ret['data'] = result
    return jsonify(ret)


# 按部门以及项目负责人统计发布成功率
@publishStatisticsProfile.route('/owners', methods=['GET'])
@require_login()
def get_publish_statistics_by_owner():
    ret = dict()
    query_by = request.values.get('query_by')
    query = request.values.get('query')
    begin_date = request.values.get('begin_date')
    end_date = request.values.get('end_date')
    group = request.values.get('group')
    result= PublishStatisticsService.get_project_statistics(query_by, query, begin_date, end_date)
    ret['result'] = 1
    ret['data'] = result
    return jsonify(ret)


@publishStatisticsProfile.route('/export/export-statistics.xls', methods=['GET'])
@require_login()
def export_publish_statistics():
    type = request.values.get('type')
    begin_date = request.values.get('begin_date')
    end_date = request.values.get('end_date')
    group = request.values.get('group', None)
    query_by = request.values.get('query_by', None)
    query = request.values.get('query', None)

    if type == "all":
        headers = [{'key': 'department', 'name': '部门'}, {'key': 'product', 'name':'产品模块' },
                   {'key': 'total', 'name': '发布总数'}, {'key': 'complete', 'name':'成功数' },
                   {'key': 'abandon', 'name': '退回数'}, {'key': 'success_str', 'name': '发布成功率'}
                   ]
        data, total = PublishStatisticsService.get_publish_statistics(begin_date, end_date, group, query)
    elif type == "abandon_records":
        headers = [{'key': 'abandon_reason', 'name': '回退原因'}, {'key': 'total', 'name': '退回数'}]
        result = PublishStatisticsService.get_abandon_statistics(begin_date, end_date)
        data = list()
        for key, val in result.items():
            if key == "pre_not_pass_reason":
                prefix_name = "pre_not_pass_reason"
            else:
                prefix_name = "owner_rollback_reason"
            for k,v in val.items():
                name = prefix_name + '_' + k
                data.append({'abandon_reason': name, 'total': v})
    elif type == "project_abandon_records":
        headers = [{'key': 'project_id', 'name': '项目ID'}, {'key': 'name', 'name': '项目名称'},
                   {'key': 'product', 'name': '产品模块'}, {'key': 'department', 'name': '部门'},
                   {'key': 'type', 'name': '项目类型'}, {'key': 'owner', 'name': 'Owner'},
                   {'key': 'total_abandon', 'name': '退回次数'}]
        data = PublishStatisticsService.get_project_abandon_statistics(begin_date, end_date)
    elif type == "department_owner_publish_records" or type == "owner_publish_records":
        headers = [{'key': 'owner', 'name': '开发人员'}, {'key': 'total', 'name': '发布总数'},
                   {'key': 'complete', 'name': '成功数'}, {'key': 'abandon', 'name': '退回数'},
                   {'key': 'success_str', 'name': '发布成功率'}]
        data = PublishStatisticsService.get_project_statistics(query_by, query, begin_date, end_date).get('owner_record')
        if isinstance(data, dict):
            data = [data]
    elif type == "owner_publish_records_by_product":
        headers = [{'key': 'department', 'name': '部门'}, {'key': 'product', 'name': '产品模块'},
                   {'key': 'total', 'name': '发布总数'}, {'key': 'complete', 'name': '成功数'},
                   {'key': 'abandon', 'name': '退回数'}, {'key': 'success_str', 'name': '发布成功率'}
                   ]
        data = PublishStatisticsService.get_project_statistics(query_by, query, begin_date, end_date).get('owner_product_record')

    book = dict()
    book['statistics'] = dict()
    book['statistics']['data'] = data
    book['statistics']['headers'] = headers
    excel_file = Util.export_excel(book)

    return send_file(excel_file, mimetype='application/vnd.ms-excel')


@publishStatisticsProfile.route('/get/project/owners', methods=['GET'])
@require_login()
def get_project_owners():
    begin_date = request.values.get('begin_date')
    end_date = request.values.get('end_date')
    owners = PublishStatisticsService.get_project_owners(begin_date, end_date)
    ret = dict()
    ret['result'] = 1
    ret['data'] = list(owners)
    return jsonify(ret)
