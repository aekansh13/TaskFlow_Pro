from datetime import timedelta
import os


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
    MONGODB_SETTINGS = {'host': os.environ.get('MONGO_URI', 'mongodb://localhost:27017/taskflow')}
    FRONTEND_URL = os.environ.get('FRONTEND_URL', '*')

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-me')
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_COOKIE_CSRF_PROTECT = False  # Enable in production with HTTPS

    # Celery / Redis
    CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

    # Flask-SocketIO
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')


class DevelopmentConfig(Config):
    """Development configuration — debug mode on, cookies not secure."""
    DEBUG = True
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_SAMESITE = 'Lax'
    # Store token in both cookies AND allow reading from headers
    JWT_TOKEN_LOCATION = ['cookies', 'headers']


class ProductionConfig(Config):
    """Production configuration — debug off, cookies must be HTTPS."""
    DEBUG = False
    JWT_COOKIE_SECURE = True
    # If frontend and backend are on different domains, we need None/Secure
    JWT_COOKIE_SAMESITE = 'None' if os.environ.get('FRONTEND_URL') else 'Lax'


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
