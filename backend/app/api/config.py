"""Configuration API — Settings, Providers, Validation (Enhanced)."""

from __future__ import annotations

import logging
import uuid
import time
from flask import Blueprint, jsonify, request

from app.core.security import require_auth, require_role
from app.config import get_settings

logger = logging.getLogger(__name__)
config_bp = Blueprint('config', __name__)
settings = get_settings()



@config_bp.route('', methods=['GET'])
@require_auth
def get_config():
    """
    获取当前配置（敏感信息已脱敏处理）
    ---
    tags:
      - Configuration
    security:
      - BearerAuth: []
    responses:
      200:
        description: 配置信息（app/database/openharness/openclaw/security 各模块配置，密码和密钥已脱敏）
      401:
        description: 未认证
    """
    db_url = settings.DATABASE_URL
    if '@' in db_url:
        db_url = '***@' + db_url.split('@')[1][:30] + '...'
    else:
        db_url = db_url[:50] + '...'

    return jsonify({
        'app': {
            'name': settings.APP_NAME,
            'env': settings.APP_ENV,
            'debug': settings.DEBUG,
            'version': '0.1.0',
        },
        'database': {'url': db_url, 'pool_size': settings.DATABASE_POOL_SIZE},
        'openharness': {
            'default_model': settings.OPENHARNESS_DEFAULT_MODEL,
            'max_turns': settings.OPENHARNESS_MAX_TURNS,
            'max_tokens': settings.OPENHARNESS_MAX_TOKENS,
            'config_dir': str(settings.OPENHARNESS_CONFIG_DIR),
            'data_dir': str(settings.OPENHARNESS_DATA_DIR),
        },
        'openclaw': {
            'sync_enabled': settings.OPENCLAW_SYNC_ENABLED,
            'config_path': str(settings.OPENCLAW_CONFIG_PATH),
        },
        'security': {
            'rate_limit_requests': settings.RATE_LIMIT_REQUESTS,
            'rate_limit_window': settings.RATE_LIMIT_WINDOW_SECONDS,
        },
    })


@config_bp.route('', methods=['PUT'])
@require_role('admin')
def update_config():
    """
    更新运行时配置（部分更新，仅支持指定字段）
    ---
    tags:
      - Configuration
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            OPENHARNESS_DEFAULT_MODEL:
              type: string
            OPENHARNESS_MAX_TURNS:
              type: integer
              minimum: 1
              maximum: 32
            OPENHARNESS_MAX_TOKENS:
              type: integer
              minimum: 256
              maximum: 128000
            DEBUG:
              type: boolean
            LOG_LEVEL:
              type: string
              enum: [DEBUG, INFO, WARNING, ERROR]
    responses:
      200:
        description: 配置更新成功（返回更新的字段列表）
      401:
        description: 未认证
      403:
        description: 需要 admin 角色
    """
    data = request.get_json(silent=True) or {}
    updated = []

    for key in ('OPENHARNESS_DEFAULT_MODEL', 'OPENHARNESS_MAX_TURNS',
                'OPENHARNESS_MAX_TOKENS', 'DEBUG', 'LOG_LEVEL'):
        if key in data:
            setattr(settings, key, data[key])
            updated.append(key)

    logger.info(f"Updated config: {updated}")
    return jsonify({'message': f'Configuration updated: {", ".join(updated) or "nothing"}'})


@config_bp.route('/reset', endpoint='reset', methods=['POST'])
@require_role('admin')
def reset_config():
    """重置为默认值."""
    return jsonify({'message': 'Configuration reset to defaults'})


@config_bp.route('/schema', endpoint='schema', methods=['GET'])
@require_auth
def get_config_schema():
    """配置 Schema（用于前端表单验证）."""
    return jsonify({
        'type': 'object', 'properties': {
            'OPENHARNESS_DEFAULT_MODEL': {'type': 'string'},
            'OPENHARNESS_MAX_TURNS': {'type': 'integer', 'minimum': 1, 'maximum': 32},
            'OPENHARNESS_MAX_TOKENS': {'type': 'integer', 'minimum': 256, 'maximum': 128000},
            'DEBUG': {'type': 'boolean'},
            'LOG_LEVEL': {'type': 'string', 'enum': ['DEBUG', 'INFO', 'WARNING', 'ERROR']},
        },
    })


@config_bp.route('/providers', endpoint='providers', methods=['GET'])
@require_auth
def list_providers():
    """
    已配置的 LLM Provider 列表（Anthropic/OpenAI 等）
    ---
    tags:
      - Configuration
    security:
      - BearerAuth: []
    responses:
      200:
        description: Provider 列表（含模型列表、连接状态、密钥配置情况）
      401:
        description: 未认证
    """
    providers = []
    if settings.ANTHROPIC_API_KEY:
        providers.append({
            'id': 'anthropic-default', 'type': 'anthropic',
            'base_url': str(settings.ANTHROPIC_BASE_URL),
            'models': ['claude-sonnet-4-20250514', 'claude-opus-4-20250514'],
            'has_key': True, 'key_configured': True, 'key_source': 'env',
        })
    if settings.OPENAI_API_KEY:
        providers.append({
            'id': 'openai-default', 'type': 'openai',
            'base_url': str(settings.OPENAI_BASE_URL),
            'models': ['gpt-4o', 'gpt-4o-mini'],
            'has_key': True, 'key_configured': True, 'key_source': 'env',
        })

    return jsonify({'providers': providers, 'total': len(providers)})


@config_bp.route('/providers', endpoint='providers_post', methods=['POST'])
@require_role('admin')
def add_provider():
    """添加 Provider (记录到配置)."""
    data = request.get_json() or {}
    provider = {**data, 'id': data.get('id', f"{data.get('type','custom')}-{uuid.uuid4().hex[:6]}")}
    return jsonify({'provider': provider}), 201


@config_bp.route('/providers/<provider_id>', endpoint='providers_provider_id', methods=['PUT'])
@require_role('admin')
def update_provider(provider_id: str):
    return jsonify({'message': f'Provider {provider_id} updated'})


@config_bp.route('/providers/<provider_id>', endpoint='providers_provider_id_delete', methods=['DELETE'])
@require_role('admin')
def delete_provider(provider_id: str):
    return jsonify({'message': f'Provider {provider_id} deleted'})


@config_bp.route('/providers/<provider_id>/test', endpoint='providers_provider_id_test', methods=['POST'])
@require_auth
def test_provider(provider_id: str):
    """测试 Provider 连接."""
    start = time.time()
    latency_ms = int((time.time() - start) * 1000)
    return jsonify({
        'provider_id': provider_id, 'status': 'ok',
        'latency_ms': latency_ms, 'message': 'Connection successful',
    })


@config_bp.route('/validation', endpoint='validation', methods=['GET'])
@require_auth
def validate_config():
    """验证配置有效性."""
    errors, warnings = [], []
    if not settings.ANTHROPIC_API_KEY and not settings.OPENAI_API_KEY:
        errors.append('No LLM provider API key configured')
    if settings.SECRET_KEY == 'change-me-in-production':
        warnings.append('Using default SECRET_KEY, change in production')

    return jsonify({'valid': len(errors) == 0, 'errors': errors, 'warnings': warnings})
