from functools import wraps
from flask import abort, current_app, request
from flask_login import current_user
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

_password_hasher = PasswordHasher()

def hash_password(password: str) -> str:
    return _password_hasher.hash(password)

def verify_password(encoded: str, password: str) -> bool:
    try:
        return _password_hasher.verify(encoded, password)
    except (VerifyMismatchError, VerificationError):
        return False

def password_is_strong(password: str) -> bool:
    return (
        len(password) >= 12
        and any(c.islower() for c in password)
        and any(c.isupper() for c in password)
        and any(c.isdigit() for c in password)
        and any(not c.isalnum() for c in password)
    )

def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator

def apply_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; "
        "form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
    )
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if current_app.config.get("SESSION_COOKIE_SECURE"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
