"""
WSGI entry point for Railway deployment
"""

from app import create_app
import os

app = create_app(config_name=os.getenv('FLASK_ENV', 'production'))

if __name__ == '__main__':
    app.run()

