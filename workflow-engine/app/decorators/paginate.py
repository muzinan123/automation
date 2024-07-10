# -*- coding:utf8 -*-

from functools import wraps
from bson import json_util
import json
from flask import request, jsonify, Response

from app.models import paginate
from app.util import Util

perPage = 20


def make_paging_mongo(result_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['GET']:
                page = request.values.get('p', 1)
                if Util.can_tune_to(page, int):
                    pipeline, collection = f(*args, **kwargs)
                    sort_info = pipeline.pop()
                    pipeline.append({'$count': 'total'})
                    total = [e for e in collection.aggregate(pipeline, allowDiskUse=True)]
                    total = total[0].get('total') if total else 0
                    pipeline.pop()
                    pipeline.append(sort_info)
                    pipeline.append({'$skip': (int(page) - 1) * perPage})
                    pipeline.append({'$limit': perPage})
                    items = collection.aggregate(pipeline, allowDiskUse=True)
                    data = dict()
                    data[result_name] = [e for e in items]
                    data['prevNum'] = (int(page) - 1) if int(page) > 0 else 0
                    data['nextNum'] = (int(page) + 1) if int(page) * perPage < total else int(page)
                    data['total'] = total
                    data['perPage'] = perPage
                    ret = dict()
                    ret['result'] = 1
                    ret['data'] = data
                    return Response(json.dumps(ret, default=json_util.default), mimetype='application/json')
                else:
                    return "error", 400
            else:
                return f(*args, **kwargs)

        return decorated_function

    return decorator


def make_paging(result_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['GET']:
                page = request.values.get('p', 1)
                if Util.can_tune_to(page, int):
                    data = f(*args, **kwargs)
                    pager = paginate(data, int(page), perPage, False)
                    items = pager.items
                    data = dict()
                    data[result_name] = [e.serialize() for e in items]
                    data['prevNum'] = pager.prev_num
                    data['nextNum'] = pager.next_num
                    data['total'] = pager.total
                    data['perPage'] = perPage
                    data['pageNum'] = int(page)
                    ret = dict()
                    ret['result'] = 1
                    ret['data'] = data
                    return jsonify(ret)
                else:
                    return "error", 400
            else:
                return f(*args, **kwargs)

        return decorated_function

    return decorator


def make_paging_api_for_java(result_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['GET']:
                page = request.values.get('currentPage', 1)
                page_size = request.values.get('pageSize', 20)
                if Util.can_tune_to(page, int):
                    data = f(*args, **kwargs)
                    pager = paginate(data, int(page), page_size, False)
                    items = pager.items
                    data = dict()
                    serialize_data = [e.serialize() for e in items]
                    data[result_name] = [
                        {"id": p.get("id"), "issueId": p.get("jira_issue_id"),
                         "completedDate": p.get("expect_publish_date"),
                         "deptName": p.get("dept_label"),
                         "projectName": p.get("name")} for p in serialize_data]
                    data["totalItem"] = pager.total
                    data["totalPage"] = pager.pages
                    data['pageSize'] = page_size
                    data['prevPage'] = pager.prev_num
                    data['nextPage'] = pager.next_num
                    data['currentPage'] = int(page)
                    ret = dict()
                    ret['result'] = 1
                    return jsonify(data)
                else:
                    return "error", 400
            else:
                return f(*args, **kwargs)

        return decorated_function

    return decorator
