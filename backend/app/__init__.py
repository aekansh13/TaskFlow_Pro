from werkzeug.middleware.proxy_fix import ProxyFix
import mongoengine
from flask import Flask
from .config import config_map
from .extensions import jwt, cors, socketio


def create_app(config_name: str = 'development') -> Flask:
    """Application factory — creates and configures the Flask app."""
    app = Flask(__name__)
    
    # Handle Proxy headers (essential for Render/Heroku SSL)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Load environment-based config
    app.config.from_object(config_map[config_name])

    # Connect MongoEngine
    mongoengine.connect(host=app.config['MONGODB_SETTINGS']['host'])

    # Register Flask extensions
    frontend_url = app.config.get('FRONTEND_URL', '*')
    
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r'/api/*': {
            'origins': [frontend_url, 'http://localhost:5500', 'http://127.0.0.1:5500'],
            'methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
            'allow_headers': ['Content-Type', 'Authorization', 'X-Requested-With'],
            'expose_headers': ['Content-Type', 'Set-Cookie'],
            'supports_credentials': True,
            'max_age': 86400,
        }},
        supports_credentials=True,
    )
    socketio.init_app(
        app,
        cors_allowed_origins=[frontend_url, 'http://localhost:5500', 'http://127.0.0.1:5500'],
        async_mode=None
    )

    # Register blueprints
    from .auth.routes import auth_bp, init_oauth
    from .tasks.routes import tasks_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')

    # Initialise Google OAuth client (requires app context)
    init_oauth(app)

    return app
