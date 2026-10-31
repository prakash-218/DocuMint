"""
Main Flask application.
"""

import logging
from flask import Flask, jsonify, render_template, request, session
from dotenv import load_dotenv
import os
import pathlib
from app_helpers import invoice_is_overdue, to_date
from documents import display_number, get_type, load_json
from money import format_money


env_path = pathlib.Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from config import config, DEFAULT_SECRET_KEY
from db import db
from auth import get_current_user


from blueprints.auth_bp import auth_bp
from blueprints.dashboard_bp import dashboard_bp
from blueprints.invoices_bp import invoices_bp
from blueprints.customers_bp import customers_bp
from blueprints.templates_bp import templates_bp
from blueprints.settings_bp import settings_bp
from blueprints.customer_portal_bp import customer_portal_bp
from blueprints.projects_bp import projects_bp
from blueprints.notifications_bp import notifications_bp
from blueprints.payments_bp import payments_bp
from blueprints.emails_bp import emails_bp
from blueprints.costings_bp import costings_bp
from blueprints.search_bp import search_bp
from blueprints.shared_bp import shared_bp
from blueprints.api_bp import api_bp
from frontend_assets import frontend_assets
import doc_urls


def create_app(config_name=None):
    """Create and configure Flask application"""
    app = Flask(__name__)

    import observability
    observability.configure_logging()

    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    if config_name == 'production':
        # Railway terminates TLS; trust its X-Forwarded-* so links are https and cookies are secure
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    observability.init_app(app)

    if config_name == 'production' and app.config['SECRET_KEY'] == DEFAULT_SECRET_KEY:
        # Sessions are signed with this key; the default lets anyone forge a login
        raise RuntimeError('SECRET_KEY must be set in production')


    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(invoices_bp, url_prefix='/' + doc_urls.SEGMENT)
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(templates_bp, url_prefix='/templates')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(customer_portal_bp, url_prefix='/customer')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(emails_bp, url_prefix='/emails')
    app.register_blueprint(costings_bp, url_prefix='/costings')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(shared_bp, url_prefix='/s')
    app.register_blueprint(api_bp, url_prefix='/api')


    @app.context_processor
    def inject_user():
        """What the pages (spa.html, _palette.html) need: the role in the current organization and its unread count."""
        user = get_current_user()
        org_id = session.get('org_id')
        membership = next((o for o in session.get('user_organizations') or []
                           if str(o.get('org_id')) == str(org_id)), None)
        return {'nav_role': membership.get('role') if membership else None,
                'unread_notifications': _unread(user, org_id, membership)}

    def _unread(user, org_id, membership):
        import permissions
        if not user or not org_id or not membership or not permissions.can('notifications.read', perms=membership):
            return 0
        from activity import unread_count
        return unread_count(user['user_id'], org_id)

    @app.template_filter('currency')
    def currency_filter(value, code=None, decimals=True):
        """Format as money in the given currency (₹ uses Indian digit grouping); decimals=False rounds to the rupee"""
        return format_money(value, code or 'USD', decimals=decimals)

    @app.template_filter('multiline')
    def multiline_filter(text, blocks=False):
        """Escape text and keep its line breaks; '-' / '•' lines are indented as break-up bullets.

        blocks=True (PDFs) puts each line in its own <div class="ln">: xhtml2pdf measures a table
        cell of <br>-separated lines short, so long descriptions ran over the next row."""
        from markupsafe import Markup, escape
        if not text:
            return ''
        lines = []
        for line in str(text).replace('\r\n', '\n').split('\n'):
            stripped = line.strip()
            if stripped[:1] in ('-', '•', '*') and len(stripped) > 1:
                lines.append(Markup('&nbsp;&nbsp;&nbsp;- ') + escape(stripped[1:].strip()))
            else:
                lines.append(escape(line))
        if blocks:
            return Markup('').join(Markup('<div class="ln">%s</div>') % (line or Markup('&nbsp;')) for line in lines)
        return Markup('<br>').join(lines)

    @app.template_filter('notes')
    def notes_filter(text):
        """Light formatting for quote notes / scope, as plain text is typed:
        'Scope:' -> underlined heading; 'Note: text' -> underlined label + text;
        '1. item' / '- item' -> indented list lines; leading spaces indent headings."""
        import re
        from markupsafe import Markup, escape
        if not text:
            return ''
        pad = lambda n: Markup('&nbsp;' * (n * 4))
        out = []
        for raw in str(text).replace('\r\n', '\n').split('\n'):
            indent = (len(raw) - len(raw.lstrip(' \t'))) // 2
            line = raw.strip()
            if not line:
                out.append(Markup(''))
                continue
            label = re.match(r'^([^:]{1,40}):\s*(.*)$', line)
            if re.match(r'^(\d+[.)]|[-•*])\s+', line):
                out.append(pad(indent + 2) + escape(line))
            elif label and not label.group(2):
                out.append(pad(indent) + Markup('<b><u>%s:</u></b>') % label.group(1))
            elif label:
                out.append(pad(indent) + Markup('<b><u>%s:</u></b> ') % label.group(1) + escape(label.group(2)))
            else:
                out.append(pad(indent) + escape(line))
        return Markup('<br>').join(out)

    @app.template_filter('money_totals')
    def money_totals_filter(totals):
        """{'INR': 28910, 'USD': 2497} -> '₹28,910.00 · $2,497.00' (or a zero amount)"""
        if not totals:
            return format_money(0, 'USD')
        return ' · '.join(format_money(v, k) for k, v in totals.items())

    @app.template_filter('doc_number')
    def doc_number_filter(doc):
        return display_number(doc or {})

    @app.template_filter('image_width')
    def image_width_filter(data_uri, height):
        """The width (pt) an image prints at for this height, from its own proportions. PDFs stretch an image
        given only a height across a table cell."""
        from app_helpers import image_ratio
        return round(height * image_ratio(data_uri), 1)

    @app.template_filter('fromjson')
    def fromjson_filter(value):
        return load_json(value)

    @app.template_filter('number')
    def number_filter(value):
        """Format number with commas and decimals"""
        if value is None:
            return '0'
        try:
            num = float(value)
            if num == int(num):
                return f'{int(num):,}'
            return f'{num:,.2f}'
        except (ValueError, TypeError):
            return '0'

    @app.template_filter('date')
    def date_filter(value):
        """Format a date or ISO date string as 'Jan 5, 2026'"""
        d = to_date(value)
        if not d:
            return value or ''
        return f"{d.strftime('%b')} {d.day}, {d.year}"

    app.add_template_global(invoice_is_overdue, 'is_overdue')
    app.add_template_global(get_type, 'doc_type_info')
    import nav
    app.add_template_global(nav.boot, 'spa_boot')
    app.add_template_global(frontend_assets, 'frontend_assets')
    from layout import printed_customer_fields, printed_org_fields
    app.add_template_global(printed_org_fields, 'printed_org_fields')
    app.add_template_global(printed_customer_fields, 'printed_customer_fields')

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify(error='Not found'), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/api/'):
            return jsonify(error='Something went wrong on our side'), 500
        return render_template('errors/500.html'), 500


    @app.route('/')
    def index():
        user = get_current_user()
        if user:
            from flask import redirect, url_for
            return redirect(url_for('dashboard_bp.index'))
        from blueprints.auth_bp import _login_page
        return _login_page()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

