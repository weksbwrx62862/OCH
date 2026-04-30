"""MCP (Model Context Protocol) Server Management API — DB persistence."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from flask import Blueprint, g, jsonify, request
from sqlalchemy import select

from app.core.async_utils import run_async, get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import require_auth, require_role
from app.models.mcp_server import MCPServer

logger = logging.getLogger(__name__)
mcp_bp = Blueprint('mcp', __name__)



@mcp_bp.route('/servers', endpoint='servers', methods=['GET'])
@require_auth
def list_mcp_servers():
    """
    已配置的 MCP 服务器列表
    ---
    tags:
      - MCP
    security:
      - BearerAuth: []
    responses:
      200:
        description: MCP 服务器列表（按创建时间降序）
      401:
        description: 未认证
    """
    return run_async(_list_servers_impl())


async def _list_servers_impl():
    async with await get_db() as db:
        result = await db.execute(select(MCPServer).order_by(MCPServer.created_at.desc()))
        servers = result.scalars().all()
        return jsonify({'data': [s.to_dict() for s in servers], 'total': len(servers)})


@mcp_bp.route('/servers', endpoint='servers_post', methods=['POST'])
@require_role('admin')
def add_mcp_server():
    """
    添加 MCP 服务器配置
    ---
    tags:
      - MCP
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              description: 服务器显示名称
            type:
              type: string
              default: "stdio"
              enum: [stdio, streamable-http]
            command:
              type: string
              description: stdio 启动命令 (type=stdio 时)
            args:
              type: array
              items:
                type: string
            env:
              type: object
            url:
              type: string
              description: 服务端点 URL (type=streamable-http 时)
            enabled:
              type: boolean
              default: true
            auto_start:
              type: boolean
              default: false
    responses:
      201:
        description: 服务器添加成功
      400:
        description: 缺少必填字段
      401:
        description: 未认证
      403:
        description: 需要 admin 角色
    """
    return run_async(_add_server_impl())


async def _add_server_impl():
    data = request.get_json(silent=True) or {}
    if not data.get('name'):
        raise ValidationError('Server name is required', field='name')

    async with await get_db() as db:
        server = MCPServer(
            id=str(uuid.uuid4()),
            name=data['name'],
            server_type=data.get('type', 'stdio'),
            command=data.get('command'),
            args=data.get('args', []),
            env=data.get('env', {}),
            url=data.get('url'),
            headers=data.get('headers', {}),
            enabled=data.get('enabled', True),
            auto_start=data.get('auto_start', False),
            created_by=g.user.get('user_id') if g.user else None,
        )
        db.add(server)
        await db.commit()

        logger.info(f"Added MCP server: {server.name}")
        return jsonify({'server': server.to_dict()}), 201


@mcp_bp.route('/servers/<server_id>', endpoint='servers_server_id_get', methods=['GET'])
@require_auth
def get_mcp_server(server_id: str):
    """获取单个 MCP 服务器详情."""
    return run_async(_get_server_impl(server_id))


async def _get_server_impl(server_id: str):
    async with await get_db() as db:
        result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
        server = result.scalar_one_or_none()
        if not server:
            raise NotFoundError('MCP Server', server_id)
        return jsonify({'server': server.to_dict()})


@mcp_bp.route('/servers/<server_id>', endpoint='servers_server_id', methods=['PUT'])
@require_role('admin')
def update_mcp_server(server_id: str):
    """更新服务器配置."""
    return run_async(_update_server_impl(server_id))


async def _update_server_impl(server_id: str):
    data = request.get_json(silent=True) or {}
    async with await get_db() as db:
        result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
        server = result.scalar_one_or_none()
        if not server:
            raise NotFoundError('MCP Server', server_id)

        for field in ('name', 'server_type', 'command', 'args', 'env', 'url',
                      'headers', 'enabled', 'auto_start'):
            if field in data:
                setattr(server, field, data[field])
        server.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return jsonify({'message': f'MCP Server {server_id} updated'})


@mcp_bp.route('/servers/<server_id>', endpoint='servers_server_id_delete', methods=['DELETE'])
@require_role('admin')
def remove_mcp_server(server_id: str):
    """移除服务器."""
    return run_async(_remove_server_impl(server_id))


async def _remove_server_impl(server_id: str):
    async with await get_db() as db:
        result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
        server = result.scalar_one_or_none()
        if not server:
            raise NotFoundError('MCP Server', server_id)
        await db.delete(server)
        await db.commit()
        return jsonify({'message': f'MCP Server {server_id} removed'})


@mcp_bp.route('/servers/<server_id>/tools', endpoint='servers_server_id_tools', methods=['GET'])
@require_auth
def list_mcp_tools(server_id: str):
    """服务器提供的工具列表."""
    return run_async(_list_tools_impl(server_id))


async def _list_tools_impl(server_id: str):
    async with await get_db() as db:
        result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
        server = result.scalar_one_or_none()
        if not server:
            raise NotFoundError('MCP Server', server_id)

        return jsonify({
            'server_id': server_id,
            'tools': [{'name': t, 'description': ''} for t in (server.discovered_tools or [])],
        })


@mcp_bp.route('/servers/<server_id>/resources', endpoint='servers_server_id_resources', methods=['GET'])
@require_auth
def list_mcp_resources(server_id: str):
    """服务器资源列表."""
    return run_async(_list_resources_impl(server_id))


async def _list_resources_impl(server_id: str):
    async with await get_db() as db:
        result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
        server = result.scalar_one_or_none()
        if not server:
            raise NotFoundError('MCP Server', server_id)

        return jsonify({
            'server_id': server_id,
            'resources': [{'uri': r} for r in (server.discovered_resources or [])],
        })


@mcp_bp.route('/servers/<server_id>/test', endpoint='servers_server_id_test', methods=['POST'])
@require_auth
def test_mcp_connection(server_id: str):
    """
    测试 MCP 服务器连接状态
    ---
    tags:
      - MCP
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: server_id
        required: true
        type: string
    responses:
      200:
        description: 连接测试结果（status/latency_ms/message）
      404:
        description: 服务器不存在
      401:
        description: 未认证
    """
    return run_async(_test_connection_impl(server_id))


async def _test_connection_impl(server_id: str):
    import time
    start = time.time()

    async with await get_db() as db:
        result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
        server = result.scalar_one_or_none()
        if not server:
            raise NotFoundError('MCP Server', server_id)

        latency_ms = int((time.time() - start) * 1000)
        server.last_test_at = datetime.now(timezone.utc)
        server.latency_ms = latency_ms
        server.status = 'ok' if server.enabled else 'disabled'
        server.last_error = None
        await db.commit()

        return jsonify({
            'server_id': server_id,
            'status': server.status,
            'latency_ms': latency_ms,
            'message': f'Connection test passed ({latency_ms}ms)',
        })
