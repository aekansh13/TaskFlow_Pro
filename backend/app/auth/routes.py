"""
Auth routes for TaskFlow Pro.
Covers: register, login, logout, /me, Google OAuth 2.0
JWTs are stored in httpOnly cookies (XSS-safe).
"""
from datetime import datetime

from flask import jsonify, redirect, request, url_for
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)
from marshmallow import Schema, ValidationError, fields, validate, validates

from app.models.user import User
from . import auth_bp

# ---------------------------------------------------------------------------
# OAuth client (initialised lazily per-app via init_oauth())
# ---------------------------------------------------------------------------

oauth = None


def init_oauth(app):
    """Attach and configure the Google OAuth client to the Flask app."""
    global oauth
    from authlib.integrations.flask_client import OAuth as _OAuth
    oauth = _OAuth(app)
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )


# ---------------------------------------------------------------------------
# Marshmallow schemas
# ---------------------------------------------------------------------------

class RegisterSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))

    @validates('password')
    def validate_password_strength(self, value):
        if not any(c.isupper() for c in value):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not any(c.isdigit() for c in value):
            raise ValidationError('Password must contain at least one digit.')


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


_register_schema = RegisterSchema()
_login_schema = LoginSchema()


# ---------------------------------------------------------------------------
# Local auth endpoints
# ---------------------------------------------------------------------------

@auth_bp.post('/register')
def register():
    json_data = request.get_json(silent=True) or {}
    errors = _register_schema.validate(json_data)
    if errors:
        return jsonify({'errors': errors}), 422

    data = _register_schema.load(json_data)

    if User.objects(email=data['email']).first():
        return jsonify({'error': 'An account with this email already exists.'}), 409

    user = User(name=data['name'], email=data['email'], oauth_provider='local')
    user.set_password(data['password'])
    user.save()

    token = create_access_token(identity=str(user.id))
    user_dict = user.to_dict()
    user_dict['token'] = token          # expose token for header-based auth
    response = jsonify(user_dict)
    response.status_code = 201
    set_access_cookies(response, token)
    return response


@auth_bp.post('/login')
def login():
    json_data = request.get_json(silent=True) or {}
    errors = _login_schema.validate(json_data)
    if errors:
        return jsonify({'errors': errors}), 422

    data = _login_schema.load(json_data)

    user = User.objects(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password.'}), 401

    user.last_login = datetime.utcnow()
    user.save()

    token = create_access_token(identity=str(user.id))
    user_dict = user.to_dict()
    user_dict['token'] = token          # expose token for header-based auth
    response = jsonify(user_dict)
    set_access_cookies(response, token)
    return response


@auth_bp.post('/logout')
def logout():
    response = jsonify({'message': 'Logged out'})
    unset_jwt_cookies(response)
    return response


@auth_bp.get('/me')
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    return jsonify(user.to_dict())


# ---------------------------------------------------------------------------
# Google OAuth 2.0 endpoints
# ---------------------------------------------------------------------------

@auth_bp.get('/google')
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.get('/google/callback')
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo') or oauth.google.userinfo()
    except Exception:
        return redirect('/index.html?error=oauth_failed')

    email = user_info.get('email')
    name = user_info.get('name', '')
    sub = user_info.get('sub')
    picture = user_info.get('picture')

    if not email:
        return redirect('/index.html?error=oauth_failed')

    user = User.objects(email=email).first()
    if user:
        user.last_login = datetime.utcnow()
        user.save()
    else:
        user = User(
            name=name,
            email=email,
            oauth_provider='google',
            oauth_id=sub,
            avatar_url=picture,
        )
        user.save()

    jwt_token = create_access_token(identity=str(user.id))
    response = redirect('/dashboard.html')
    set_access_cookies(response, jwt_token)
    return response
