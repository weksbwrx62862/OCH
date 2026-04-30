"""Agent Management API — Complete CRUD with database operations."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request
from sqlalchemy import select, func, case
from sqlalchemy.orm import selectinload

from app.core.async_utils import run_async, get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import require_auth, require_role
from app.models.agent import Agent, ToolPermission

logger = logging.getLogger(__name__)
agents_bp = Blueprint('agents', __name__)



@agents_bp.route('', methods=['GET'], endpoint='list_agents')
@require_auth
def list_agents():
    """
    列出所有 Agent，支持分页、筛选和搜索
    ---
    tags:
      - Agents
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: page
        schema:
          type: integer
          default: 1
        description: 页码（从 1 开始）
      - in: query
        name: per_page
        schema:
          type: integer
          maximum: 100
          default: 20
        description: 每页数量
      - in: query
        name: is_active
        schema:
          type: string
          enum: [true, false]
        description: 按激活状态筛选
      - in: query
        name: search
        schema:
          type: string
        description: 搜索关键词（匹配名称或描述）
    responses:
      200:
        description: Agent 列表
        content:
          application/json:
            schema:
              type: object
              properties:
                data:
                  type: array
                  items:
                    $ref: '#/components/schemas/Agent'
                total:
                  type: integer
                  example: 42
                page:
                  type: integer
                  example: 1
                per_page:
                  type: integer
                  example: 20
                total_pages:
                  type: integer
                  example: 3
      401:
        description: 未认证
      403:
        description: 权限不足
    """
    return run_async(_list_agents_impl())


async def _list_agents_impl():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    is_active = request.args.get('is_active')
    search = request.args.get('search', '')

    async with await get_db() as db:
        query = select(Agent)

        if is_active is not None:
            is_active_bool = is_active.lower() in ('true', '1', 'yes')
            query = query.where(Agent.is_active == is_active_bool)

        if search:
            search_pattern = f'%{search}%'
            query = query.where(
                (Agent.name.ilike(search_pattern)) |
                (Agent.description.ilike(search_pattern))
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Agent.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await db.execute(query)
        agents = result.scalars().all()

        return jsonify({
            'data': [agent.to_dict() for agent in agents],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
        })


@agents_bp.route('', methods=['POST'], endpoint='create_agent')
@require_auth
@require_role('admin')
def create_agent():
    """
    创建新 Agent（需要 Admin 权限）
    ---
    tags:
      - Agents
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - name
              - model
            properties:
              name:
                type: string
                example: "Code Reviewer"
                description: 智能体唯一名称
              model:
                type: string
                example: "claude-sonnet-4-20250514"
                description: LLM 模型标识符
              description:
                type: string
                example: "代码审查专家，专注于代码质量和最佳实践"
                description: 智能体描述
              system_prompt:
                type: string
                example: "你是一个专业的代码审查助手..."
                description: 系统提示词（覆盖默认）
              is_active:
                type: boolean
                default: true
                description: 是否激活
    responses:
      201:
        description: 创建成功
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Agent'
      400:
        description: 参数错误（名称为空或重复）
      401:
        description: 未认证
      403:
        description: 需要 Admin 权限
    """
    return run_async(_create_agent_impl())


async def _create_agent_impl():
    data = request.get_json(silent=True)

    if not data:
        raise ValidationError('Request body is required')

    if 'name' not in data or not data['name'].strip():
        raise ValidationError('Agent name is required and cannot be empty', field='name')

    async with await get_db() as db:
        existing = await db.execute(
            select(Agent).where(Agent.name == data['name'].strip())
        )
        if existing.scalar_one_or_none():
            raise ValidationError(
                f"Agent with name '{data['name']}' already exists",
                field='name'
            )

        agent = Agent(
            id=str(uuid.uuid4()),
            name=data['name'].strip(),
            description=data.get('description', '').strip(),
            system_prompt=data.get('system_prompt'),
            model=data.get('model', 'claude-sonnet-4-20250514'),
            max_turns=data.get('max_turns', 8),
            max_tokens=data.get('max_tokens', 4096),
            workspace=data.get('workspace', './workspace'),
            config=data.get('config', {}),
            is_active=data.get('is_active', True),
            created_by=g.user.get('user_id') if g.user else None,
        )

        db.add(agent)

        default_permissions = data.get('tool_permissions', [])
        for perm_data in default_permissions:
            perm = ToolPermission(
                id=str(uuid.uuid4()),
                agent_id=agent.id,
                tool_name=perm_data['tool_name'],
                permission=perm_data.get('permission', 'ask'),
                path_rules=perm_data.get('path_rules'),
                approved_commands=perm_data.get('approved_commands'),
                denied_commands=perm_data.get('denied_commands'),
            )
            db.add(perm)

        await db.commit()
        await db.refresh(agent)

        logger.info(f"Created agent: {agent.name} ({agent.id}) by {g.user}")

        return jsonify({
            'agent': agent.to_dict(),
            'message': 'Agent created successfully',
        }), 201


@agents_bp.route('/quick-create', methods=['POST'], endpoint='quick_create_agent')
@require_auth
def quick_create_agent():
    """快速创建聊天用 Agent（普通用户可用，受限参数）."""
    from flask import request as flask_request, g
    from app.core.async_utils import run_async, get_db
    from app.models.agent import Agent

    data = flask_request.get_json(silent=True) or {}
    name = data.get('name', f'ChatBot-{uuid.uuid4().hex[:8]}')
    model = data.get('model', 'claude-sonnet-4-20250514')

    async def _create():
        async with await get_db() as db:
            agent = Agent(
                id=str(uuid.uuid4()),
                name=name,
                description=f'Quick-created chat agent',
                system_prompt='你是一个有帮助的 AI 助手。',
                model=model,
                config={'source': 'quick-create'},
                created_by=g.user.get('sub') if g.user else None,
            )
            db.add(agent)
            await db.commit()
            await db.refresh(agent)
            return agent.to_dict()

    agent_dict = run_async(_create())
    return jsonify({'agent': agent_dict}), 201


@agents_bp.route('/<agent_id>', methods=['GET'], endpoint='get_agent')
@require_auth
def get_agent(agent_id: str):
    """获取 Agent 详情（含权限配置）."""
    return run_async(_get_agent_impl(agent_id))


async def _get_agent_impl(agent_id: str):
    async with await get_db() as db:
        result = await db.execute(
            select(Agent)
            .options(selectinload(Agent.permissions))
            .where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()

        if not agent:
            raise NotFoundError('Agent', agent_id)

        response = agent.to_dict()
        response['permissions'] = [p.to_dict() for p in agent.permissions]

        return jsonify(response)


@agents_bp.route('/<agent_id>', methods=['PUT'], endpoint='update_agent')
@require_auth
@require_role('admin')
def update_agent(agent_id: str):
    """更新 Agent 配置."""
    return run_async(_update_agent_impl(agent_id))


async def _update_agent_impl(agent_id: str):
    data = request.get_json(silent=True)

    if not data:
        raise ValidationError('Request body is required')

    async with await get_db() as db:
        result = await db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()

        if not agent:
            raise NotFoundError('Agent', agent_id)

        if 'name' in data and data['name'] != agent.name:
            existing = await db.execute(
                select(Agent).where(
                    (Agent.name == data['name']) & (Agent.id != agent_id)
                )
            )
            if existing.scalar_one_or_none():
                raise ValidationError(
                    f"Agent with name '{data['name']}' already exists",
                    field='name'
                )

        updatable_fields = [
            'name', 'description', 'system_prompt', 'model',
            'max_turns', 'max_tokens', 'workspace', 'config',
            'is_active',
        ]

        updated_fields = []
        for field in updatable_fields:
            if field in data:
                setattr(agent, field, data[field])
                updated_fields.append(field)

        agent.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(agent)

        logger.info(f"Updated agent {agent_id}: fields={updated_fields}")

        return jsonify({
            'agent': agent.to_dict(),
            'updated_fields': updated_fields,
        })


@agents_bp.route('/<agent_id>', methods=['DELETE'], endpoint='delete_agent')
@require_auth
@require_role('admin')
def delete_agent(agent_id: str):
    """删除 Agent（级联删除权限和会话）."""
    return run_async(_delete_agent_impl(agent_id))


async def _delete_agent_impl(agent_id: str):
    async with await get_db() as db:
        result = await db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = result.scalar_one_or_none()

        if not agent:
            raise NotFoundError('Agent', agent_id)

        agent_name = agent.name
        await db.delete(agent)
        await db.commit()

        logger.warning(f"Deleted agent: {agent_name} ({agent_id})")

        return jsonify({
            'message': f"Agent '{agent_name}' deleted successfully",
            'deleted_id': agent_id,
        })


@agents_bp.route('/<agent_id>/duplicate', methods=['POST'], endpoint='duplicate_agent')
@require_auth
def duplicate_agent(agent_id: str):
    """复制 Agent（含配置和权限）."""
    return run_async(_duplicate_agent_impl(agent_id))


async def _duplicate_agent_impl(agent_id: str):
    data = request.get_json(silent=True) or {}
    new_name = data.get('name')

    async with await get_db() as db:
        result = await db.execute(
            select(Agent)
            .options(selectinload(Agent.permissions))
            .where(Agent.id == agent_id)
        )
        source_agent = result.scalar_one_or_none()

        if not source_agent:
            raise NotFoundError('Agent', agent_id)

        final_name = new_name or f"{source_agent.name} (copy)"

        existing = await db.execute(
            select(Agent).where(Agent.name == final_name)
        )
        if existing.scalar_one_or_none():
            counter = 1
            while True:
                test_name = f"{final_name} {counter}"
                existing = await db.execute(
                    select(Agent).where(Agent.name == test_name)
                )
                if not existing.scalar_one_or_none():
                    final_name = test_name
                    break
                counter += 1

        new_agent = Agent(
            id=str(uuid.uuid4()),
            name=final_name,
            description=source_agent.description,
            system_prompt=source_agent.system_prompt,
            model=source_agent.model,
            max_turns=source_agent.max_turns,
            max_tokens=source_agent.max_tokens,
            workspace=source_agent.workspace,
            config=dict(source_agent.config),
            is_active=False,
            created_by=g.user.get('user_id') if g.user else None,
        )
        db.add(new_agent)

        for source_perm in source_agent.permissions:
            new_perm = ToolPermission(
                id=str(uuid.uuid4()),
                agent_id=new_agent.id,
                tool_name=source_perm.tool_name,
                permission=source_perm.permission,
                path_rules=list(source_perm.path_rules) if source_perm.path_rules else None,
                approved_commands=list(source_perm.approved_commands) if source_perm.approved_commands else None,
                denied_commands=list(source_perm.denied_commands) if source_perm.denied_commands else None,
            )
            db.add(new_perm)

        await db.commit()
        await db.refresh(new_agent)

        logger.info(f"Duplicated agent {agent_id} -> {new_agent.id} ({final_name})")

        return jsonify({
            'agent': new_agent.to_dict(),
            'message': f"Agent duplicated as '{final_name}'",
        }), 201


@agents_bp.route('/<agent_id>/stats', methods=['GET'], endpoint='agent_stats')
@require_auth
def agent_stats(agent_id: str):
    """获取 Agent 统计数据（会话数、Token 用量等）."""
    return run_async(_agent_stats_impl(agent_id))


async def _agent_stats_impl(agent_id: str):
    from app.models.session import Session

    async with await get_db() as db:
        agent_result = await db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = agent_result.scalar_one_or_none()

        if not agent:
            raise NotFoundError('Agent', agent_id)

        session_stats = await db.execute(
            select(
                func.count(Session.id).label('total_sessions'),
                func.sum(Session.total_messages).label('total_messages'),
                func.sum(Session.total_turns).label('total_turns'),
                func.sum(Session.total_tokens_input).label('total_tokens_input'),
                func.sum(Session.total_tokens_output).label('total_tokens_output'),
                func.sum(Session.total_cost_usd).label('total_cost_usd'),
                func.sum(
                    case((Session.status == 'active', 1), else_=0)
                ).label('active_sessions'),
            ).where(Session.agent_id == agent_id)
        )

        stats = session_stats.one()

        return jsonify({
            'agent_id': agent_id,
            'agent_name': agent.name,
            'total_sessions': stats.total_sessions or 0,
            'total_messages': stats.total_messages or 0,
            'total_turns': stats.total_turns or 0,
            'total_tokens_input': stats.total_tokens_input or 0,
            'total_tokens_output': stats.total_tokens_output or 0,
            'total_cost_usd': round(stats.total_cost_usd or 0, 4),
            'active_sessions': stats.active_sessions or 0,
            'created_at': agent.created_at.isoformat() if agent.created_at else None,
        })


@agents_bp.route('/<agent_id>/permissions', methods=['GET'], endpoint='get_agent_permissions')
@require_auth
def get_agent_permissions(agent_id: str):
    """获取 Agent 权限配置."""
    return run_async(_get_agent_permissions_impl(agent_id))


async def _get_agent_permissions_impl(agent_id: str):
    async with await get_db() as db:
        agent_result = await db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = agent_result.scalar_one_or_none()

        if not agent:
            raise NotFoundError('Agent', agent_id)

        perms_result = await db.execute(
            select(ToolPermission)
            .where(ToolPermission.agent_id == agent_id)
            .order_by(ToolPermission.tool_name)
        )
        permissions = perms_result.scalars().all()

        return jsonify({
            'agent_id': agent_id,
            'mode': agent.config.get('permission_mode', 'default'),
            'tool_permissions': [p.to_dict() for p in permissions],
            'total_permissions': len(permissions),
        })


@agents_bp.route('/<agent_id>/permissions', methods=['PUT'], endpoint='update_agent_permissions')
@require_auth
@require_role('admin')
def update_agent_permissions(agent_id: str):
    """更新 Agent 权限配置."""
    return run_async(_update_agent_permissions_impl(agent_id))


async def _update_agent_permissions_impl(agent_id: str):
    data = request.get_json(silent=True)

    if not data:
        raise ValidationError('Request body is required')

    async with await get_db() as db:
        agent_result = await db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = agent_result.scalar_one_or_none()

        if not agent:
            raise NotFoundError('Agent', agent_id)

        if 'mode' in data:
            agent.config['permission_mode'] = data['mode']

        if 'tool_permissions' in data:
            await db.execute(
                ToolPermission.__table__.delete()
                .where(ToolPermission.agent_id == agent_id)
            )

            for perm_data in data['tool_permissions']:
                perm = ToolPermission(
                    id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    tool_name=perm_data['tool_name'],
                    permission=perm_data.get('permission', 'ask'),
                    path_rules=perm_data.get('path_rules'),
                    approved_commands=perm_data.get('approved_commands'),
                    denied_commands=perm_data.get('denied_commands'),
                )
                db.add(perm)

        agent.updated_at = datetime.now(timezone.utc)
        await db.commit()

        logger.info(f"Updated permissions for agent {agent_id}")

        return jsonify({
            'message': f"Agent {agent_id} permissions updated",
            'mode': agent.config.get('permission_mode'),
        })
