# -*- coding:utf8 -*-

from functools import wraps
from flask import request, jsonify
from app.models import paginate
from app.util import Util

perPage = 20


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
