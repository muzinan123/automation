# -*- coding:utf-8 -*-

from app import app, socketio

app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True


socketio.run(app, host='0.0.0.0', port=6011, debug=True)
