"""认证 API — 登录、Token 验证."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.config import get_settings
from app.core.security import create_jwt, verify_password, verify_token

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.route('/login', endpoint='login', methods=['POST'])
def login():
    """用户登录（开发环境简化版）.

    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              default: admin
            password:
              type: string
    responses:
      200:
        description: 登录成功，返回 JWT Token
      401:
        description: 认证失败
    """
    data = request.get_json() or {}
    username = data.get('username', 'admin')
    password = data.get('password', '')

    if not username:
        return jsonify({'error': 'Username required', 'code': 400}), 400

    settings = get_settings()
    if settings.APP_ENV != 'development':
        if not password:
            return jsonify({'error': 'Password required', 'code': 401}), 401
        if not settings.ADMIN_PASSWORD:
            return jsonify({'error': 'Login disabled: no admin password configured', 'code': 401}), 401
        if not verify_password(password, settings.ADMIN_PASSWORD):
            return jsonify({'error': 'Invalid credentials', 'code': 401}), 401

    token = create_jwt({
        'sub': username,
        'username': username,
        'role': 'admin' if username == 'admin' else 'user'
    })

    return jsonify({
        'access_token': token,
        'token_type': 'Bearer',
        'expires_in': 86400,
        'user': {
            'id': username,
            'username': username,
            'role': 'admin' if username == 'admin' else 'user'
        }
    })


@auth_bp.route('/verify', endpoint='verify', methods=['GET'])
def verify():
    """验证 Token 有效性.

    ---
    tags:
      - Auth
    security:
      - BearerAuth: []
    responses:
      200:
        description: Token 有效
      401:
        description: Token 无效或过期
    """
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None

    if not token:
        return jsonify({'error': 'Token required', 'code': 401}), 401

    payload = verify_token(token)
    if payload is None:
        return jsonify({'error': 'Invalid or expired token', 'code': 401}), 401

    return jsonify({
        'valid': True,
        'user': {
            'id': payload.get('sub'),
            'username': payload.get('username'),
            'role': payload.get('role', 'user')
        }
    })


@auth_bp.route('/refresh', endpoint='refresh', methods=['POST'])
def refresh():
    """刷新 Token.

    ---
    tags:
      - Auth
    security:
      - BearerAuth: []
    responses:
      200:
        description: 新 Token
      401:
        description: Token 无效
    """
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None

    if not token:
        return jsonify({'error': 'Token required', 'code': 401}), 401

    payload = verify_token(token)
    if payload is None:
        return jsonify({'error': 'Invalid or expired token', 'code': 401}), 401

    new_token = create_jwt({
        'sub': payload.get('sub'),
        'username': payload.get('username'),
        'role': payload.get('role', 'user')
    })

    return jsonify({
        'access_token': new_token,
        'token_type': 'Bearer',
        'expires_in': 86400
    })
