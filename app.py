"""
Main Flask application.
"""

from flask import Flask, render_template, session, g
from dotenv import load_dotenv
import os
import pathlib



env_path = pathlib.Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from config import config
from db import db
from auth import get_current_user


from blueprints.auth_bp import auth_bp
from blueprints.dashboard_bp import dashboard_bp
from blueprints.invoices_bp import invoices_bp
from blueprints.customers_bp import customers_bp
from blueprints.templates_bp import templates_bp
from blueprints.settings_bp import settings_bp
from blueprints.customer_portal_bp import customer_portal_bp


def create_app(config_name=None):
    """Create and configure Flask application"""
    app = Flask(__name__)


    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])


    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(invoices_bp, url_prefix='/invoices')
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(templates_bp, url_prefix='/templates')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(customer_portal_bp, url_prefix='/customer')


    @app.context_processor
    def inject_user():
        from auth import get_current_customer
        user = get_current_user()
        customer = get_current_customer()
        return {
            'current_user': user,
            'current_customer': customer,
            'current_org_id': session.get('org_id')
        }


    @app.template_filter('currency')
    def currency_filter(value):
        """Format number as currency"""
        if value is None:
            return '$0.00'
        try:
            return f'${float(value):,.2f}'
        except (ValueError, TypeError):
            return '$0.00'


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

