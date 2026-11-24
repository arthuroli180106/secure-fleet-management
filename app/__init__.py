import os
from flask import Flask
from dotenv import load_dotenv
from .extensions import db, login_manager, csrf, limiter
from .security import apply_security_headers

def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-this-secret"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///fleet.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
        WTF_CSRF_TIME_LIMIT=3600,
        MAX_CONTENT_LENGTH=12 * 1024 * 1024,
        RATELIMIT_STORAGE_URI=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    csrf.init_app(app)
    limiter.init_app(app)

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .auth import auth_bp
    from .fleet import fleet_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(fleet_bp)

    @app.after_request
    def security_headers(response):
        return apply_security_headers(response)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
