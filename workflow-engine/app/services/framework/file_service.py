# -*- coding:utf8 -*-

import os
from app import app, root_logger


class FileService(object):

    @staticmethod
    def upload(file, name, directory):
        try:
            ori_filename = file.filename
            extname = ''
            if ori_filename.find('.'):
                extname = ori_filename[ori_filename.rindex('.'):]
            filename = name + extname
            file.save(os.path.join(
                app.config.get('UPLOAD_FOLDER'), directory, filename
            ))
            return filename
        except Exception, e:
            root_logger.exception("upload error: %s", e)
            raise
