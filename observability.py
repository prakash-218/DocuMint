"""
Logging and health checks for Railway.

- Logs are single-line JSON on Railway (or LOG_FORMAT=json): `message` and `level` are
  what the Log Explorer shows; every other field is filterable, e.g. @path:/projects
  @status:500 @requestId:... @durationMs:>500
- One line per request: method, path, status, durationMs, requestId, userId, orgId.
- /healthz: database and storage reachability, for Railway's health check and uptime monitors.
"""

import json
import logging
import os
import sys
import time
import uuid

from flask import g, jsonify, request

LEVELS = {'WARNING': 'warn', 'CRITICAL': 'error'}
_STANDARD = set(vars(logging.LogRecord('', 0, '', 0, '', (), None)).keys()) | {'message', 'asctime'}


class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {'message': record.getMessage(), 'level': LEVELS.get(record.levelname, record.levelname.lower()),
                 'logger': record.name}
        for key, value in vars(record).items():
            if key not in _STANDARD and not key.startswith('_'):
                entry[key] = value if isinstance(value, (str, int, float, bool, type(None))) else str(value)
        if record.exc_info:
            entry['exception'] = self.formatException(record.exc_info)
        rid = _request_id()
        if rid and 'requestId' not in entry:
            entry['requestId'] = rid
        return json.dumps(entry, default=str)


def _request_id():
    try:
        return getattr(g, 'request_id', None)
    except RuntimeError:            # outside a request
        return None


def configure_logging():
    json_logs = os.getenv('LOG_FORMAT') == 'json' or (os.getenv('RAILWAY_ENVIRONMENT_NAME') and os.getenv('LOG_FORMAT') != 'text')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if json_logs else logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(os.getenv('LOG_LEVEL', 'INFO').upper())
    for noisy in ('werkzeug', 'botocore', 'urllib3', 'fontTools', 'xhtml2pdf', 'reportlab', 'PIL'):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def init_app(app):
    log = logging.getLogger('request')

    @app.before_request
    def _start():
        g.request_started = time.perf_counter()
        g.request_id = (request.headers.get('X-Request-Id') or uuid.uuid4().hex)[:64]

    @app.after_request
    def _log(response):
        if request.path.startswith('/static') or request.path == '/healthz':
            return response
        duration = (time.perf_counter() - getattr(g, 'request_started', time.perf_counter())) * 1000
        user = (getattr(g, 'current_user', None) or {})
        level = logging.ERROR if response.status_code >= 500 else (logging.WARNING if duration > 2000 else logging.INFO)
        log.log(level, f'{request.method} {request.path} {response.status_code}', extra={
            'method': request.method, 'path': request.path, 'status': response.status_code,
            'durationMs': round(duration, 1), 'userId': user.get('user_id'),
            'orgId': getattr(g, 'current_org_id', None), 'endpoint': request.endpoint})
        response.headers['X-Request-Id'] = g.request_id
        return response

    @app.errorhandler(Exception)
    def _unhandled(error):
        from werkzeug.exceptions import HTTPException
        if isinstance(error, HTTPException):
            return error
        logging.getLogger('app').exception('Unhandled error on %s %s', request.method, request.path)
        from flask import render_template
        return render_template('errors/500.html'), 500

    @app.route('/healthz')
    def healthz():
        from db import db
        import storage
        checks = {}
        try:
            db.ping()
            checks['database'] = 'ok'
        except Exception as e:      # noqa: BLE001 - report, don't crash
            checks['database'] = f'error: {type(e).__name__}'
        try:
            storage.check()
            checks['storage'] = 'ok'
        except Exception as e:      # noqa: BLE001
            checks['storage'] = f'error: {type(e).__name__}'
        healthy = checks['database'] == 'ok'
        return jsonify(status='ok' if healthy else 'degraded', checks=checks,
                       version=os.getenv('RAILWAY_GIT_COMMIT_SHA', 'dev')[:12]), (200 if healthy else 503)
