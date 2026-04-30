"""Plugins & Extensions API — Plugin lifecycle management (DB)."""

from __future__ import annotations

import logging
import uuid
from flask import Blueprint, g, jsonify, request
from sqlalchemy import select

from app.core.async_utils import run_async, get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import require_auth, require_role
from app.models.plugin import Plugin

logger = logging.getLogger(__name__)
plugins_bp = Blueprint('plugins', __name__)

_BUILTIN_PLUGINS = [
    {'name': 'commit-commands', 'version': '1.0.0', 'description': 'Git commit, push, PR workflows', 'source': 'builtin'},
    {'name': 'security-guidance', 'version': '1.0.0', 'description': 'Security warnings on file edits', 'source': 'builtin'},
]



@plugins_bp.route('', methods=['GET'])
@require_auth
def list_plugins():
    """已安装插件列表 (DB + 内置)."""
    return run_async(_list_plugins_impl())


async def _list_plugins_impl():
    builtin = [dict(p) for p in _BUILTIN_PLUGINS]

    custom = []
    async with await get_db() as db:
        result = await db.execute(select(Plugin).order_by(Plugin.name))
        custom = [p.to_dict() for p in result.scalars().all()]

    return jsonify({
        'data': builtin + custom,
        'total_builtin': len(builtin),
        'total_custom': len(custom),
    })


@plugins_bp.route('/available', endpoint='available', methods=['GET'])
@require_auth
def list_available_plugins():
    """可用插件市场."""
    return jsonify({
        'available': [
            {'name': 'feature-dev', 'version': '1.0.0', 'description': 'Feature development workflow'},
            {'name': 'code-review', 'version': '1.0.0', 'description': 'Multi-agent PR review'},
            {'name': 'hookify', 'version': '1.0.0', 'description': 'Create custom behavior hooks'},
        ],
    })


@plugins_bp.route('/install', endpoint='install', methods=['POST'])
@require_role('admin')
def install_plugin():
    """安装插件."""
    return run_async(_install_impl())


async def _install_impl():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    if not name:
        raise ValidationError('Plugin name is required', field='name')

    async with await get_db() as db:
        existing = await db.execute(select(Plugin).where(Plugin.name == name))
        if existing.scalar_one_or_none():
            raise ValidationError(f'Plugin already exists: {name}')

        plugin = Plugin(
            id=str(uuid.uuid4()),
            name=name,
            version=data.get('version', '1.0.0'),
            description=data.get('description'),
            source=data.get('source_type', 'local'),
            source_url=data.get('source'),
            enabled=False,
            installed_by=g.user.get('user_id') if g.user else None,
        )
        db.add(plugin)
        await db.commit()

        logger.info(f"Installed plugin: {name}")
        return jsonify({'plugin': plugin.to_dict()}), 201


@plugins_bp.route('/<plugin_name>', endpoint='plugin_name_delete', methods=['DELETE'])
@require_role('admin')
def uninstall_plugin(plugin_name: str):
    """卸载插件."""
    return run_async(_uninstall_impl(plugin_name))


async def _uninstall_impl(plugin_name: str):
    async with await get_db() as db:
        result = await db.execute(select(Plugin).where(Plugin.name == plugin_name))
        plugin = result.scalar_one_or_none()
        if not plugin:
            raise NotFoundError('Plugin', plugin_name)
        await db.delete(plugin)
        await db.commit()
        return jsonify({'message': f"Plugin '{plugin_name}' uninstalled"})


@plugins_bp.route('/<plugin_name>/enable', endpoint='plugin_name_enable', methods=['PUT'])
@require_auth
def enable_plugin(plugin_name: str):
    """启用插件."""
    return run_async(_toggle_plugin(plugin_name, True))


@plugins_bp.route('/<plugin_name>/disable', endpoint='plugin_name_disable', methods=['PUT'])
@require_auth
def disable_plugin(plugin_name: str):
    """禁用插件."""
    return run_async(_toggle_plugin(plugin_name, False))


async def _toggle_plugin(name: str, enabled: bool):
    action = 'enable' if enabled else 'disable'

    async with await get_db() as db:
        result = await db.execute(select(Plugin).where(Plugin.name == name))
        plugin = result.scalar_one_or_none()
        if plugin:
            plugin.enabled = enabled
            await db.commit()
            return jsonify({'message': f"Plugin '{name}' {action}d", 'enabled': enabled})

    raise NotFoundError('Plugin', name)


@plugins_bp.route('/<plugin_name>/detail', endpoint='plugin_name_detail', methods=['GET'])
@require_auth
def get_plugin_detail(plugin_name: str):
    """插件详情（commands, hooks, agents）."""
    return run_async(_get_detail_impl(plugin_name))


async def _get_detail_impl(name: str):
    detail = None

    # 查数据库
    async with await get_db() as db:
        result = await db.execute(select(Plugin).where(Plugin.name == name))
        plugin = result.scalar_one_or_none()
        if plugin:
            detail = {**plugin.to_dict(), 'commands': [], 'hooks': [], 'agents': []}

    # 查内置
    if not detail:
        for bp in _BUILTIN_PLUGINS:
            if bp['name'] == name:
                detail = {
                    **bp, 'enabled': True, 'source': 'builtin',
                    'has_commands': bp['name'] == 'commit-commands',
                    'has_hooks': bp['name'] == 'security-guidance',
                    'has_agents': False,
                    'commands': [],
                    'hooks': [],
                    'agents': [],
                }
                break

    if not detail:
        raise NotFoundError('Plugin', name)

    if detail.get('has_commands'):
        detail['commands'] = [
            {'name': '/commit', 'description': 'Create a git commit'},
            {'name': '/push', 'description': 'Push to remote'},
        ]
    if detail.get('has_hooks'):
        detail['hooks'] = [
            {'event': 'PreToolUse', 'handler': 'check_security'},
            {'event': 'PostToolWrite', 'handler': 'log_write'},
        ]

    return jsonify(detail)
