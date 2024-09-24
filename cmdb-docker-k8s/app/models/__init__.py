#-*- coding: utf-8 -*-

from app import app
from flask import abort, has_request_context, request
from sqlalchemy import func
from flask_sqlalchemy import SQLAlchemy, Pagination

db = SQLAlchemy(app, session_options={"autoflush": False, "autocommit": False, "expire_on_commit": False})


def paginate(query, page=None, per_page=None, error_out=True):
    """Returns `per_page` items from page `page`.  By default it will
    abort with 404 if no items were found and the page was larger than
    1.  This behavor can be disabled by setting `error_out` to `False`.

    If page or per_page are None, they will be retrieved from the
    request query.  If the values are not ints and ``error_out`` is
    true, it will abort with 404.  If there is no request or they
    aren't in the query, they default to page 1 and 20
    respectively.

    Returns an :class:`Pagination` object.
    """
    if has_request_context():
        if page is None:
            try:
                page = int(request.args.get('page', 1))
            except (TypeError, ValueError):
                if error_out:
                    abort(404)

                page = 1

        if per_page is None:
            try:
                per_page = int(request.args.get('per_page', 20))
            except (TypeError, ValueError):
                if error_out:
                    abort(404)

                per_page = 20
    else:
        if page is None:
            page = 1

        if per_page is None:
            per_page = 20

    if error_out and page < 1:
        abort(404)

    items = query.limit(per_page).offset((page - 1) * per_page).all()

    if not items and page != 1 and error_out:
        abort(404)

    # No need to count if we're on the first page and there are fewer
    # items than we expected.
    if page == 1 and len(items) < per_page:
        total = len(items)
    else:
        # 对count进行性能优化
        count_q = query.statement.with_only_columns([func.count()]).order_by(None)
        total = query.session.execute(count_q).scalar()

    return Pagination(query, page, per_page, total, items)