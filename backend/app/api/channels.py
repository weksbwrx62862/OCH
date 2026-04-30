"""Channels API — IM 渠道集成框架.

基于 openharness/channels/ 的 12 个适配器:
- feishu, slack, telegram, wecom
- discord, dingtalk, email, matrix
- qq, mochat, whatsapp

架构模式:
    InboundMessage → ChannelManager → QueryEngine → OutboundMessage → ChannelAdapter
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from flask import Blueprint, jsonify, request

from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import require_auth

logger = logging.getLogger(__name__)
channels_bp = Blueprint('channels', __name__)

# 已注册的渠道配置（运行时注册，非持久化）
_registered_channels: Dict[str, Dict[str, Any]] = {}
MAX_REGISTERED_CHANNELS = 50

# 支持的渠道类型及其元信息
CHANNEL_TYPES = {
    'feishu': {'name': '飞书', 'protocol': 'WebSocket', 'builtin': True},
    'slack': {'name': 'Slack', 'protocol': 'Socket Mode', 'builtin': True},
    'telegram': {'name': 'Telegram', 'protocol': 'Bot API (long-polling)', 'builtin': True},
    'wecom': {'name': '企业微信', 'protocol': 'WebSocket', 'builtin': True},
    'discord': {'name': 'Discord', 'protocol': 'Gateway', 'builtin': True},
    'dingtalk': {'name': '钉钉', 'protocol': 'Robot', 'builtin': True},
    'email': {'name': '邮件', 'protocol': 'SMTP/IMAP', 'builtin': True},
    'matrix': {'name': 'Matrix', 'protocol': 'Application Service', 'builtin': True},
    'qq': {'name': 'QQ', 'protocol': 'Bot API', 'builtin': True},
    'mocha': {'name': '企业微信(摩可)', 'protocol': 'Robot', 'builtin': True},
    'whatsapp': {'name': 'WhatsApp', 'protocol': 'Cloud API', 'builtin': True},
}


@channels_bp.route('/types', endpoint='types', methods=['GET'])
@require_auth
def list_channel_types():
    """
    列出所有支持的 IM 渠道类型（12 种适配器）
    ---
    tags:
      - Channels
    security:
      - BearerAuth: []
    responses:
      200:
        description: 渠道类型列表（含名称/协议/内置标记）
        schema:
          type: object
          properties:
            channel_types:
              type: object
              additionalProperties:
                type: object
                properties:
                  name:
                    type: string
                  protocol:
                    type: string
                  builtin:
                    type: boolean
            total:
              type: integer
            description:
              type: string
      401:
        description: 未认证
    """
    return jsonify({
        'channel_types': CHANNEL_TYPES,
        'total': len(CHANNEL_TYPES),
        'description': '基于 openharness/channels/impl/ 下的 12 个适配器',
    })


@channels_bp.route('/registered', endpoint='registered', methods=['GET'])
@require_auth
def list_registered_channels():
    """列出已注册（已配置）的渠道实例."""
    return jsonify({
        'channels': [
            {**v, 'type': k} for k, v in _registered_channels.items()
        ],
        'total': len(_registered_channels),
    })


@channels_bp.route('/register', endpoint='register', methods=['POST'])
@require_auth
def register_channel():
    """
    注册一个新的渠道实例（基于 openharness/channels/impl/ 适配器）
    ---
    tags:
      - Channels
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - type
            - name
          properties:
            type:
              type: string
              enum: [feishu, slack, telegram, wecom, discord, dingtalk, email, matrix, qq, mocha, whatsapp]
              description: 渠道类型
            name:
              type: string
              description: 实例名称（同一类型下唯一）
            config:
              type: object
              description: 渠道配置（如 bot_token, chat_id 等）
            enabled:
              type: boolean
              default: true
    responses:
      201:
        description: 渠道注册成功（返回 channel_id）
      400:
        description: 缺少必填字段或类型不支持或已存在
      401:
        description: 未认证
    """
    data = request.get_json(silent=True) or {}

    channel_type = data.get('type')
    name = data.get('name')

    if not channel_type:
        raise ValidationError('type is required', field='type')
    if channel_type not in CHANNEL_TYPES:
        raise ValidationError(f'Unsupported channel type: {channel_type}. Supported: {list(CHANNEL_TYPES.keys())}', field='type')
    if not name:
        raise ValidationError('name is required', field='name')

    channel_id = f"{channel_type}:{name}"

    if channel_id in _registered_channels:
        raise ValidationError(f'Channel already registered: {channel_id}', field='name')

    while len(_registered_channels) >= MAX_REGISTERED_CHANNELS:
        oldest_key = next(iter(_registered_channels))
        del _registered_channels[oldest_key]
        logger.info("淘汰最旧渠道: %s", oldest_key)

    _registered_channels[channel_id] = {
        'name': name,
        'type': channel_type,
        'display_name': CHANNEL_TYPES[channel_type]['name'],
        'config': data.get('config', {}),
        'enabled': data.get('enabled', True),
        'status': 'configured',
        'created_at': str(datetime.now(timezone.utc)),
        'message_count': 0,
    }

    logger.info("注册渠道: %s (%s)", channel_id, CHANNEL_TYPES[channel_type]['name'])
    return jsonify({
        'channel_id': channel_id,
        'channel': _registered_channels[channel_id],
    }), 201


@channels_bp.route('/<channel_id>', endpoint='channel_detail', methods=['GET'])
@require_auth
def get_channel(channel_id: str):
    """获取渠道详情."""
    if channel_id not in _registered_channels:
        raise NotFoundError('Channel', channel_id)
    return jsonify({
        'channel_id': channel_id,
        **_registered_channels[channel_id],
    })


@channels_bp.route('/<channel_id>', endpoint='channel_update', methods=['PUT'])
@require_auth
def update_channel(channel_id: str):
    """更新渠道配置."""
    if channel_id not in _registered_channels:
        raise NotFoundError('Channel', channel_id)

    data = request.get_json(silent=True) or {}
    channel = _registered_channels[channel_id]

    for key in ('config', 'enabled', 'name'):
        if key in data:
            channel[key] = data[key]

    channel['updated_at'] = str(datetime.now(timezone.utc))
    return jsonify({'message': f'Channel {channel_id} updated'})


@channels_bp.route('/<channel_id>', endpoint='channel_delete', methods=['DELETE'])
@require_auth
def delete_channel(channel_id: str):
    """注销渠道."""
    if channel_id not in _registered_channels:
        raise NotFoundError('Channel', channel_id)

    del _registered_channels[channel_id]
    logger.info("注销渠道: %s", channel_id)
    return jsonify({'message': f'Channel {channel_id} deleted'})


@channels_bp.route('/<channel_id>/send', endpoint='channel_send', methods=['POST'])
@require_auth
def send_message(channel_id: str):
    """通过指定渠道发送消息（模拟）.

    POST body: {"text": "消息内容", "recipient": "用户ID"}
    """
    if channel_id not in _registered_channels:
        raise NotFoundError('Channel', channel_id)

    data = request.get_json(silent=True) or {}
    text = data.get('text', '')

    if not text:
        raise ValidationError('text is required', field='text')

    channel = _registered_channels[channel_id]
    channel['message_count'] = (channel.get('message_count') or 0) + 1

    # 实际实现中调用 openharness.channels.impl.{type}.send()
    # 这里模拟发送成功
    logger.info(
        "[%s] 发送消息 (%d): %s",
        channel['display_name'],
        channel['message_count'],
        text[:100],
    )

    return jsonify({
        'success': True,
        'channel_id': channel_id,
        'message_id': f"msg_{uuid.uuid4().hex[:12]}",
        'sent_at': str(datetime.now(timezone.utc)),
    })


@channels_bp.route('/<channel_id>/test', endpoint='channel_test', methods=['POST'])
@require_auth
def test_connection(channel_id: str):
    """测试渠道连接状态.

    POST body: {} (使用已保存的 config)
    """
    if channel_id not in _registered_channels:
        raise NotFoundError('Channel', channel_id)

    channel = _registered_channels[channel_id]

    try:

        adapter_info = {
            'channel_id': channel_id,
            'type': channel['type'],
            'config_keys': list((channel.get('config') or {}).keys()),
            'adapter_available': True,
            'note': '实际连接测试需要对应渠道的凭据',
        }
        return jsonify(adapter_info)
    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e),
        }), 500


@channels_bp.route('/stats', endpoint='stats', methods=['GET'])
@require_auth
def channels_stats():
    """所有渠道的聚合统计."""
    total_channels = len(_registered_channels)
    enabled_count = sum(1 for c in _registered_channels.values() if c.get('enabled'))
    total_messages = sum(c.get('message_count', 0) for c in _registered_channels.values())

    by_type = {}
    for cid, c in _registered_channels.items():
        t = c.get('type', 'unknown')
        by_type[t] = by_type.get(t, 0) + 1

    return jsonify({
        'total_channels': total_channels,
        'enabled_channels': enabled_count,
        'total_messages_sent': total_messages,
        'by_type': by_type,
        'available_types': len(CHANNEL_TYPES),
        'description': 'IM 渠道集成框架统计',
    })
