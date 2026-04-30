"""Multi-Agent Coordination API — Teams, Subagents, Task delegation (DB)."""

from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict

from flask import Blueprint, g, jsonify, request
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.async_utils import run_async, get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import require_auth
from app.models.team import Team, TeamMember

logger = logging.getLogger(__name__)
coordinator_bp = Blueprint('coordinator', __name__)

_BUILTIN_AGENTS = {
    'code-reviewer': {
        'id': 'code-reviewer', 'name': 'Code Reviewer',
        'description': 'Reviews code for bugs, security issues, and quality',
        'system_prompt': '你是一个资深代码审查专家...',
        'capabilities': ['read_code', 'analyze_security', 'suggest_improvements'],
    },
    'debugger': {
        'id': 'debugger', 'name': 'Debugger',
        'description': 'Diagnoses and fixes bugs systematically',
        'system_prompt': '你是一个调试专家...',
        'capabilities': ['analyze_error', 'find_root_cause', 'propose_fix'],
    },
    'planner': {
        'id': 'planner', 'name': 'Planner',
        'description': 'Designs implementation plans before coding',
        'system_prompt': '你是一个架构规划专家...',
        'capabilities': ['design_architecture', 'break_down_tasks', 'estimate_effort'],
    },
}



@coordinator_bp.route('/teams', endpoint='teams', methods=['GET'])
@require_auth
def list_teams():
    """
    列出所有团队（含成员数量统计）
    ---
    tags:
      - Coordinator
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: status
        type: string
        enum: [active, dissolved]
        description: 按状态筛选
    responses:
      200:
        description: 团队列表（含 member_count）
      401:
        description: 未认证
    """
    return run_async(_list_teams_impl())


async def _list_teams_impl():
    status_filter = request.args.get('status')

    async with await get_db() as db:
        query = select(Team)
        if status_filter:
            query = query.where(Team.status == status_filter)

        result = await db.execute(query.order_by(Team.created_at.desc()))
        teams = result.scalars().all()

        teams_data = []
        for team in teams:
            d = team.to_dict()
            members_result = await db.execute(
                select(func.count(TeamMember.id)).where(TeamMember.team_id == team.id)
            )
            d['member_count'] = members_result.scalar() or 0
            teams_data.append(d)

        return jsonify({'data': teams_data, 'total': len(teams_data)})


@coordinator_bp.route('/teams', endpoint='teams_post', methods=['POST'])
@require_auth
def create_team():
    """创建团队（支持初始化成员列表）."""
    return run_async(_create_team_impl())


async def _create_team_impl():
    data = request.get_json(silent=True) or {}

    if not data.get('name'):
        raise ValidationError('Team name is required', field='name')

    async with await get_db() as db:
        team = Team(
            id=str(uuid.uuid4()),
            name=data['name'],
            description=data.get('description', ''),
            config=data.get('config', {}),
            created_by=g.user.get('user_id') if g.user else None,
        )
        db.add(team)
        await db.commit()
        await db.refresh(team)

        # 添加初始成员
        members_data = data.get('members', [])
        for m in members_data:
            member = TeamMember(
                id=str(uuid.uuid4()),
                team_id=team.id,
                agent_id=m.get('agent_id'),
                role=m.get('role', 'member'),
                capabilities=m.get('capabilities', []),
            )
            db.add(member)

        await db.commit()

        logger.info(f"Created team: {team.name} ({team.id})")
        return jsonify({'team': team.to_dict()}), 201


@coordinator_bp.route('/teams/<team_id>', endpoint='teams_team_id', methods=['GET'])
@require_auth
def get_team(team_id: str):
    """获取团队详情（含成员列表）."""
    return run_async(_get_team_impl(team_id))


async def _get_team_impl(team_id: str):
    async with await get_db() as db:
        result = await db.execute(
            select(Team)
            .options(selectinload(Team.members))
            .where(Team.id == team_id)
        )
        team = result.scalar_one_or_none()

        if not team:
            raise NotFoundError('Team', team_id)

        response = team.to_dict()
        response['members'] = [m.to_dict() for m in team.members]
        return jsonify(response)


@coordinator_bp.route('/teams/<team_id>', endpoint='teams_team_id_put', methods=['PUT'])
@require_auth
def update_team(team_id: str):
    """更新团队配置."""
    return run_async(_update_team_impl(team_id))


async def _update_team_impl(team_id: str):
    data = request.get_json(silent=True) or {}

    async with await get_db() as db:
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()

        if not team:
            raise NotFoundError('Team', team_id)

        for field in ('name', 'description', 'status', 'config'):
            if field in data:
                setattr(team, field, data[field])

        team.updated_at = datetime.now(timezone.utc)
        await db.commit()

        return jsonify({'message': f'Team {team_id} updated'})


@coordinator_bp.route('/teams/<team_id>', endpoint='teams_team_id_delete', methods=['DELETE'])
@require_auth
def delete_team(team_id: str):
    """解散团队."""
    return run_async(_delete_team_impl(team_id))


async def _delete_team_impl(team_id: str):
    async with await get_db() as db:
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()

        if not team:
            raise NotFoundError('Team', team_id)

        team.status = 'dissolved'
        team.dissolved_at = datetime.now(timezone.utc)
        await db.commit()

        logger.info(f"Dissolved team {team_id}")
        return jsonify({'message': f'Team {team_id} dissolved'})


@coordinator_bp.route('/agents', endpoint='agents', methods=['GET'])
@require_auth
def list_agent_definitions():
    """列出可用的子 Agent 定义（内置 + DB 中的）."""
    return run_async(_list_agents_impl())


async def _list_agents_impl():
    from app.models.agent import Agent

    builtin = list(_BUILTIN_AGENTS.values())

    custom_agents = []
    async with await get_db() as db:
        result = await db.execute(
            select(Agent).where(Agent.is_active.is_(True)).limit(20)
        )
        custom_agents = [
            {
                'id': a.id, 'name': a.name, 'description': a.description,
                'capabilities': ['chat', 'tool_use'],
                'source': 'custom',
            }
            for a in result.scalars().all()
        ]

    return jsonify({
        'agents': builtin + custom_agents,
        'total_builtin': len(builtin),
        'total_custom': len(custom_agents),
    })


@coordinator_bp.route('/agents/<agent_id>', endpoint='agents_agent_id', methods=['GET'])
@require_auth
def get_agent_definition(agent_id: str):
    """获取 Agent 定义详情."""
    if agent_id in _BUILTIN_AGENTS:
        return jsonify(_BUILTIN_AGENTS[agent_id])
    raise NotFoundError('Agent Definition', agent_id)


@coordinator_bp.route('/spawn', endpoint='spawn', methods=['POST'])
@require_auth
def spawn_subagent():
    """
    在团队中生成子 Agent 执行任务
    ---
    tags:
      - Coordinator
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - agent_definition
            - task
          properties:
            agent_definition:
              type: object
              description: Agent 定义 (id/name/description/system_prompt/capabilities)
            task:
              type: string
              description: 任务描述
            team_id:
              type: string
              description: 所属团队 ID
    responses:
      201:
        description: 子 Agent 任务已生成（返回 task_id 和状态）
      400:
        description: 缺少必填字段
      401:
        description: 未认证
    """
    return run_async(_spawn_impl())


async def _spawn_impl():
    data = request.get_json(silent=True) or {}

    if not data.get('agent_definition'):
        raise ValidationError('agent_definition is required', field='agent_definition')
    if not data.get('task'):
        raise ValidationError('task description is required', field='task')

    task_id = str(uuid.uuid4())

    async with await get_db() as db:
        member = TeamMember(
            id=str(uuid.uuid4()),
            team_id=data.get('team_id'),
            role='worker',
            capabilities=[],
            status='busy',
            assigned_task_id=task_id,
        )
        db.add(member)
        await db.commit()

    return jsonify({
        'task': {
            'id': task_id,
            'agent_definition': data['agent_definition'],
            'task': data['task'],
            'team_id': data.get('team_id'),
            'status': 'spawning',
        }
    }), 201


@coordinator_bp.route('/tasks', endpoint='tasks', methods=['GET'])
@require_auth
def list_coordination_tasks():
    """列出协调任务."""
    return run_async(_list_coord_tasks_impl())


async def _list_coord_tasks_impl():
    async with await get_db() as db:
        result = await db.execute(
            select(TeamMember)
            .where(TeamMember.status.in_(['busy', 'idle']))
            .order_by(TeamMember.joined_at.desc())
        )
        members = result.scalars().all()

        tasks = []
        for m in members:
            if m.assigned_task_id:
                tasks.append({
                    'id': m.assigned_task_id,
                    'member_id': m.id,
                    'role': m.role,
                    'status': m.status,
                })

        return jsonify({'tasks': tasks, 'total': len(tasks)})


# ============================================================
# P1-3: AutonomousWorker 集成 (来自 openharness/coordinator/)
# 自治 Worker：空闲轮询认领任务 + 超时自动关机 + 身份注入
# ============================================================

_active_workers: Dict[str, Any] = {}
_workers_lock = threading.Lock()
MAX_ACTIVE_WORKERS = 100


@coordinator_bp.route('/workers', endpoint='workers', methods=['GET'])
@require_auth
def list_workers():
    """
    列出所有活跃的自治 Worker（空闲轮询 + 超时关机模式）
    ---
    tags:
      - Coordinator
    security:
      - BearerAuth: []
    responses:
      200:
        description: Worker 列表（含 agent_id/team/state/statistics）
      401:
        description: 未认证
    """
    with _workers_lock:
        workers = []
        for wid, w in _active_workers.items():
            worker_obj = w.get('worker')
            if worker_obj:
                workers.append({
                    'id': wid,
                    'agent_id': worker_obj.agent_id,
                    'team': getattr(worker_obj._config, 'team', 'default'),
                    'state': worker_obj.state.value,
                    'statistics': asdict(worker_obj.statistics),
                })
        return jsonify({'workers': workers, 'total': len(workers)})


@coordinator_bp.route('/workers', endpoint='workers_post', methods=['POST'])
@require_auth
def spawn_worker():
    """启动一个新的自治 Worker."""
    return run_async(_spawn_worker_impl())


async def _spawn_worker_impl():
    from openharness.coordinator.autonomous_worker import (
        AutonomousWorkerConfig, spawn_autonomous_worker,
    )

    data = request.get_json(silent=True) or {}

    config = AutonomousWorkerConfig(
        agent_id=data.get('agent_id', f"worker-{uuid.uuid4().hex[:6]}"),
        team=data.get('team', 'default'),
        idle_poll_interval_sec=float(data.get('poll_interval', 5.0)),
        max_idle_time_sec=float(data.get('max_idle', 60.0)),
        min_context_length=int(data.get('min_context', 500)),
    )

    async def _dummy_agent_loop(prompt: str):
        import asyncio
        yield {'type': 'text_delta', 'content': f'[{config.agent_id}] 处理: {prompt[:50]}'}
        await asyncio.sleep(0.1)
        yield {'type': 'turn_complete'}

    try:
        worker = await spawn_autonomous_worker(
            config=config,
            agent_loop=_dummy_agent_loop,
        )

        wid = worker.agent_id
        with _workers_lock:
            while len(_active_workers) >= MAX_ACTIVE_WORKERS:
                oldest_key = next(iter(_active_workers))
                oldest_worker = _active_workers.pop(oldest_key)
                try:
                    oldest_worker.get('worker').force_shutdown()
                except Exception:
                    pass
                logger.info("淘汰最旧 Worker: %s", oldest_key)
            _active_workers[wid] = {
                'worker': worker,
                'started_at': datetime.now(timezone.utc).isoformat(),
                'config': data,
            }

        logger.info("启动自治 Worker: %s (team=%s)", wid, config.team)
        return jsonify({
            'worker_id': wid,
            'agent_id': config.agent_id,
            'team': config.team,
            'state': worker.state.value,
        }), 201

    except Exception as e:
        logger.exception("启动 Worker 失败")
        raise ValidationError(f'Failed to start worker: {e}')


@coordinator_bp.route('/workers/<worker_id>/stop', endpoint='workers_stop', methods=['POST'])
@require_auth
def stop_worker(worker_id: str):
    """强制关闭指定 Worker."""
    with _workers_lock:
        entry = _active_workers.get(worker_id)
        if not entry:
            raise NotFoundError('Worker', worker_id)

        worker = entry['worker']
        worker.force_shutdown()
        del _active_workers[worker_id]

    return jsonify({'message': f'Worker {worker_id} stopped'})


@coordinator_bp.route('/workers/stats', endpoint='workers_stats', methods=['GET'])
@require_auth
def workers_stats():
    """所有 Worker 的聚合统计."""
    total_completed = 0
    total_failed = 0
    total_uptime = 0.0

    with _workers_lock:
        for w in _active_workers.values():
            worker_obj = w.get('worker')
            if worker_obj:
                stats = worker_obj.statistics
                total_completed += stats.tasks_completed
                total_failed += stats.tasks_failed
                total_uptime += stats.total_uptime_sec

    return jsonify({
        'active_workers': len(_active_workers),
        'total_tasks_completed': total_completed,
        'total_tasks_failed': total_failed,
        'total_uptime_sec': round(total_uptime, 1),
        'description': '自治 Worker 统计（空闲轮询 + 超时关机）',
    })


# ============================================================
# P2-3: 双线程池子代理执行器 (参考 DeerFlow SubagentExecutor)
# 调度池 + 执行池分离, 并发限制, 超时保护
# ============================================================

@coordinator_bp.route('/subagents', endpoint='subagents', methods=['GET'])
@require_auth
def list_subagent_tasks():
    """列出所有子代理任务."""
    from app.services.subagent_executor import get_subagent_executor

    executor = get_subagent_executor()
    status_filter = request.args.get('status')
    tasks = executor.list_tasks(
        status_filter=status_filter if status_filter else None,
    )
    return jsonify({'tasks': tasks, 'total': len(tasks)})


@coordinator_bp.route('/subagents', endpoint='subagents_post', methods=['POST'])
@require_auth
def submit_subagent_task():
    """
    提交子代理任务到双线程池执行器（调度池+执行池分离）

    架构特点：
    - 调度池：负责任务排队和分发
    - 执行池：负责实际运行，并发上限控制
    - 超时保护：每个任务有独立超时时间
    - 工具白/黑名单：可限制可用工具范围
    ---
    tags:
      - Coordinator
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - prompt
          properties:
            prompt:
              type: string
              description: 任务提示词
            agent_id:
              type: string
              description: 目标 Agent ID
            timeout_seconds:
              type: number
              default: 900.0
              description: 超时时间（秒）
            tools_allowlist:
              type: array
              items:
                type: string
              description: 允许的工具白名单
            tools_denylist:
              type: array
              items:
                type: string
              description: 禁止的工具黑名单
            model_override:
              type: string
              description: 模型覆盖
            parent_trace_id:
              type: string
              description: 父级追踪 ID（用于链路追踪）
            metadata:
              type: object
    responses:
      201:
        description: 任务已提交（返回 task_id/status/prompt_preview）
      400:
        description: 缺少必填参数 prompt
      401:
        description: 未认证
    """
    from app.services.subagent_executor import get_subagent_executor, SubagentTask

    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '')

    if not prompt:
        raise ValidationError('prompt is required', field='prompt')

    task = SubagentTask(
        task_id=f"sa-{uuid.uuid4().hex[:12]}",
        agent_id=data.get('agent_id', f"agent-{uuid.uuid4().hex[:6]}"),
        prompt=prompt,
        parent_trace_id=data.get('parent_trace_id'),
        tools_allowlist=data.get('tools_allowlist'),
        tools_denylist=data.get('tools_denylist'),
        model_override=data.get('model_override'),
        timeout_seconds=float(data.get('timeout_seconds', 900.0)),
        metadata={
            'submitted_by': str(g.user.get('id')) if g.user else None,
            **(data.get('metadata') or {}),
        },
    )

    executor = get_subagent_executor()
    executor.submit(task)

    logger.info("提交子代理任务: %s (agent=%s)", task.task_id[:12], task.agent_id)
    return jsonify({
        'task_id': task.task_id,
        'agent_id': task.agent_id,
        'status': task.status.value,
        'prompt_preview': prompt[:80],
    }), 201


@coordinator_bp.route('/subagents/<task_id>', endpoint='subagents_task_id', methods=['GET'])
@require_auth
def get_subagent_task(task_id: str):
    """获取子代理任务详情."""
    from app.services.subagent_executor import get_subagent_executor

    executor = get_subagent_executor()
    task = executor.get_task(task_id)

    if not task:
        raise NotFoundError('SubagentTask', task_id)

    result = {
        'task_id': task.task_id,
        'agent_id': task.agent_id,
        'status': task.status.value,
        'prompt_preview': task.prompt[:80],
        'created_at': task.created_at,
        'started_at': task.started_at,
        'completed_at': task.completed_at,
        'error': task.error,
    }

    if task.result:
        result['result'] = task.result

    return jsonify(result)


@coordinator_bp.route('/subagents/<task_id>/cancel', endpoint='subagents_cancel', methods=['POST'])
@require_auth
def cancel_subagent_task(task_id: str):
    """取消等待中的子代理任务."""
    from app.services.subagent_executor import get_subagent_executor

    executor = get_subagent_executor()
    success = executor.cancel_task(task_id)

    if not success:
        raise ValidationError(
            'Cannot cancel: task not found or already running/completed',
            field='task_id',
        )

    return jsonify({'message': f'Task {task_id} cancelled'})


@coordinator_bp.route('/subagents/stats', endpoint='subagents_stats', methods=['GET'])
@require_auth
def subagent_stats():
    """子代理执行器统计信息."""
    from app.services.subagent_executor import get_subagent_executor

    executor = get_subagent_executor()
    stats = executor.get_stats()

    return jsonify({
        'executor': stats,
        'description': (
            '双线程池子代理执行器 — 调度池(%d)+执行池(%d), 并发上限=%d'
            % (
                stats['config']['scheduler_workers'],
                stats['config']['execution_workers'],
                stats['max_concurrent'],
            )
        ),
    })
