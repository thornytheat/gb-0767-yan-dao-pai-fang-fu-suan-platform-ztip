import os
from pathlib import Path

from flask import Flask, jsonify

from app.api import api
from app.archive.store import Archive
from app.errors import InputError
from app.web import desk


def create_app(database=None):
    app = Flask(__name__)
    app.jinja_env.autoescape = lambda name: name is None or name.endswith(('.html', '.j2'))
    app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
    app.extensions['monitor_archive'] = Archive(database or os.getenv('MONITOR_DATABASE', Path('var') / 'monitor.sqlite3'))
    app.register_blueprint(api)
    app.register_blueprint(desk)

    @app.errorhandler(InputError)
    def domain_error(error):
        return jsonify(code=error.code, detail=str(error)), error.status

    @app.errorhandler(413)
    def oversized(_):
        return jsonify(code='BODY_LIMIT', detail='原件包超过 8 MiB'), 413

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    return app
