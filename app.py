"""
Main Flask application.
"""

import logging
from flask import Flask, render_template, session, g
from dotenv import load_dotenv
import os
import pathlib
from app_helpers import invoice_is_overdue, to_date
from documents import DOC_TYPES, display_number, get_type, load_json
from money import amount_in_words, format_money



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
from blueprints.emails_bp import emails_bp
from blueprints.costings_bp import costings_bp
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
    app.register_blueprint(emails_bp, url_prefix='/emails')
    app.register_blueprint(costings_bp, url_prefix='/costings')


    @app.context_processor
    def inject_user():
        from auth import get_current_customer
        user = get_current_user()
        customer = get_current_customer()
        org_id = session.get('org_id')
        membership = next((o for o in session.get('user_organizations') or []
                           if str(o.get('org_id')) == str(org_id)), None)
        return {
            'doc_nav_group': _doc_nav_group(),
            'current_user': user,
            'current_customer': customer,
            'current_org_id': org_id,
            'nav_role': membership.get('role') if membership else None,
            'unread_notifications': _unread(user, org_id, membership),
        }

    def _unread(user, org_id, membership):
        if not user or not org_id or not membership or membership.get('role') not in ('owner', 'admin'):
            return 0
        from activity import unread_count
        return unread_count(user['user_id'], org_id)

    EVENT_ICONS = {'document_created': 'file-plus', 'document_sent': 'send', 'document_converted': 'arrow-right-left',
                   'quote_accepted': 'circle-check', 'quote_declined': 'circle-x', 'quote_revised': 'file-diff',
                   'payment': 'banknote', 'file_uploaded': 'paperclip', 'email_received': 'mail',
                   'email_sent': 'mail-check', 'project_created': 'briefcase', 'project_status': 'flag'}
    app.add_template_global(lambda kind: EVENT_ICONS.get(kind, 'bell'), 'event_icon')

    @app.template_filter('when')
    def when_filter(value):
        """'just now', '5 min ago', 'today 14:05', '12 Oct' - for activity lists."""
        from datetime import datetime, timezone
        if not value:
            return ''
        now = datetime.now(timezone.utc)
        value = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        seconds = (now - value).total_seconds()
        if seconds < 60:
            return 'just now'
        if seconds < 3600:
            return f'{int(seconds // 60)} min ago'
        local = value.astimezone()
        if seconds < 86400 and local.date() == now.astimezone().date():
            return local.strftime('today %H:%M')
        return local.strftime('%d %b %Y' if local.year != now.year else '%d %b, %H:%M')


    def _doc_nav_group():
        """Which documents nav entry is active: the /quotes, /proformas or /invoices section"""
        return {'quotes': 'quote', 'proformas': 'proforma'}.get(getattr(g, 'doc_path', None), 'invoices')

    @app.template_filter('currency')
    def currency_filter(value, code=None):
        """Format as money in the given currency (₹ uses Indian digit grouping)"""
        return format_money(value, code or 'USD')

    @app.template_filter('multiline')
    def multiline_filter(text):
        """Escape text and keep its line breaks; '-' / '•' lines are indented as break-up bullets."""
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

    @app.template_filter('amount_words')
    def amount_words_filter(value, code=None):
        return amount_in_words(value, code or 'USD')

    @app.template_filter('doc_number')
    def doc_number_filter(doc):
        return display_number(doc or {})

    @app.template_filter('doc_label')
    def doc_label_filter(doc_type):
        return get_type(doc_type).label

    @app.template_filter('project_label')
    def project_label_filter(project):
        from projects import project_label
        return project_label(project or {})

    @app.template_filter('customer_label')
    def customer_label_filter(row):
        import customers
        return customers.label(row or {})

    @app.template_filter('customer_groups')
    def customer_groups_filter(rows):
        import customers
        return customers.group(rows or [])

    @app.template_filter('filesize')
    def filesize_filter(n):
        from projects import human_size
        return human_size(n)

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

    @app.template_filter('compact_currency')
    def compact_currency_filter(value):
        """$950, $12.9K, $4.2M"""
        try:
            num = float(value or 0)
        except (ValueError, TypeError):
            return '$0'
        for size, suffix in ((1e6, 'M'), (1e3, 'K')):
            if abs(num) >= size:
                return f'${num / size:,.1f}'.rstrip('0').rstrip('.') + suffix
        return f'${num:,.0f}'

    @app.template_filter('date')
    def date_filter(value):
        """Format a date or ISO date string as 'Jan 5, 2026'"""
        d = to_date(value)
        if not d:
            return value or ''
        return f"{d.strftime('%b')} {d.day}, {d.year}"

    from pagination import page_url
    app.add_template_global(page_url, 'page_url')
    app.add_template_global(invoice_is_overdue, 'is_overdue')
    app.add_template_global(DOC_TYPES, 'DOC_TYPES')
    app.add_template_global(get_type, 'doc_type_info')
    from layout import printed_customer_fields, printed_org_fields
    app.add_template_global(printed_org_fields, 'printed_org_fields')
    app.add_template_global(printed_customer_fields, 'printed_customer_fields')

    @app.template_filter('is_currency_field')
    def is_currency_field_filter(field_label):
        """Check if field label suggests it's a currency field"""
        if not field_label:
            return False
        currency_keywords = ['amount', 'price', 'total', 'cost', 'fee', 'charge', 'payment', 'paid', 'due', 'balance', 'revenue', 'income', 'expense', 'discount', 'tax', 'subtotal']
        label_lower = field_label.lower()
        return any(keyword in label_lower for keyword in currency_keywords)


    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500


    @app.route('/')
    def index():
        user = get_current_user()
        if user:
            from flask import redirect, url_for
            return redirect(url_for('dashboard_bp.index'))
        return render_template('auth/login.html')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

