"""Security utilities: JWT authentication, password hashing, etc."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Optional

import bcrypt
from flask import Flask, g, jsonify
import jwt

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def init_security(app: Flask) -> None:
    """Initialize security configuration on the Flask app."""
    pass


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8'),
    )


def create_jwt(payload: dict, expires_hours: Optional[int] = None) -> str:
    """Create a JWT token."""
    if expires_hours is None:
        expires_hours = settings.JWT_EXPIRATION_HOURS

    exp = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    token_payload = {**payload, 'exp': exp, 'iat': datetime.now(timezone.utc)}

    return jwt.encode(
        token_payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_jwt(token: str) -> dict:
    """Decode and validate a JWT token."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def verify_token(token: str) -> Optional[dict]:
    """Verify a JWT token (alias for decode_jwt with error handling).

    Returns payload dict if valid, None if invalid/expired.
    """
    try:
        return decode_jwt(token)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        logger.warning("Token verification failed: %s", e)
        return None


def require_auth(f):
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(g, 'user', None):
            return jsonify({'error': 'Authentication required', 'code': 401}), 401
        return f(*args, **kwargs)
    return decorated_function


def require_role(*roles: str):
    """Decorator to require specific roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = getattr(g, 'user', None)
            if not user:
                return jsonify({'error': 'Authentication required', 'code': 401}), 401
            user_role = user.get('role', 'user')
            if user_role not in roles:
                return jsonify({'error': 'Insufficient permissions', 'code': 403}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def generate_api_key() -> str:
    """Generate a secure API key."""
    import secrets
    return f"{settings.OPENCLAW_API_KEY_PREFIX}{secrets.token_hex(16)}"
