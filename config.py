"""
Configuration module for Flask application.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv
import pathlib



env_path = pathlib.Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


DEFAULT_SECRET_KEY = 'dev-secret-key-change-in-production'


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', DEFAULT_SECRET_KEY)

    SESSION_COOKIE_HTTPONLY = True
    # Lax keeps the session cookie off cross-site POSTs (basic CSRF defence)
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    MAX_CONTENT_LENGTH = 12 * 1024 * 1024  # uploads: customer documents (10 MB each), logo/stamp, large forms
    JWT_SECRET = os.getenv('JWT_SECRET', 'jwt-secret-key-change-in-production')



    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24


    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = False


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
    PREFERRED_URL_SCHEME = 'https'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True



config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

