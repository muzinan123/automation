# -*- coding:utf-8 -*-

from flask import Blueprint, Markup
from app import app

filterProfile = Blueprint('filterProfile', __name__)


@app.template_filter('notnone')
def notnone_filter(s):
    if s is not None:
        return s
    else:
        return '-'
