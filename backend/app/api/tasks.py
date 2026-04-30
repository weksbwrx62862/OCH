"""Tasks & Background Jobs API — DAG dependencies + DB persistence."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import select, func, case
from sqlalchemy.orm import selectinload

from app.core.async_utils import run_async, get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import require_auth
from app.models.task import Task, TaskDependency

logger = logging.getLogger(__name__)
tasks_bp = Blueprint('tasks', __name__)



@tasks_bp.route('', methods=['GET'], endpoint='list_tasks')
@require_auth
def list_tasks():
    """
    后台任务列表，支持分页、状态筛选.

    Query params:
    - page, per_page: 分页
    - status: pending/running/completed/failed/stopped/waiting
    - session_id: 按会话筛选
    - task_type: command/query/agent_spawn
    """
    return run_async(_list_tasks_impl())


async def _list_tasks_impl():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    status = request.args.get('status')
    session_id = request.args.get('session_id')
    task_type = request.args.get('task_type')

    async with await get_db() as db:
        query = select(Task)

        if status:
            query = query.where(Task.status == status)
        if session_id:
            query = query.where(Task.session_id == session_id)
        if task_type:
            query = query.where(Task.task_type == task_type)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        query = query.order_by(Task.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await db.execute(query)
        tasks = result.scalars().all()

        # 统计各状态数量
        stats_query = select(
            Task.status,
            func.count(Task.id).label('count'),
        ).group_by(Task.status)
        stats_result = await db.execute(stats_query)
        status_stats = {row[0]: row[1] for row in stats_result.all()}

        return jsonify({
            'data': [t.to_dict() for t in tasks],
            'total': total,
            'page': page,
            'per_page': per_page,
            'status_stats': status_stats,
        })


@tasks_bp.route('', methods=['POST'], endpoint='create_task')
@require_auth
def create_task():
    """
    创建单个后台任务
    ---
    tags:
      - Tasks
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              command:
                type: string
                example: "npm test --coverage"
                description: 要执行的命令（command/bash 类型必需）
              task_type:
                type: string
                enum: [command, bash, api_call]
                default: command
                description: 任务类型
              session_id:
                type: string
                description: 关联的会话 ID
              cwd:
                type: string
                description: 工作目录
              output_path:
                type: string
                description: 输出文件路径
              metadata:
                type: object
                description: 自定义元数据
            required:
              - command
    responses:
      201:
        description: 创建成功
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Task'
      400:
        description: 参数错误（command 为空）
      401:
        description: 未认证
    """
    return run_async(_create_task_impl())


async def _create_task_impl():
    data = request.get_json(silent=True) or {}

    task_type = data.get('type', data.get('task_type', 'command'))
    if not data.get('command') and task_type in ('command', 'bash'):
        raise ValidationError('Command is required for command-type tasks', field='command')

    async with await get_db() as db:
        task = Task(
            id=str(uuid.uuid4()),
            session_id=data.get('session_id'),
            task_type=task_type,
            command=data.get('command'),
            status='pending',
            cwd=data.get('cwd'),
            output_path=data.get('output_path'),
            metadata_=data.get('metadata', {}),
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        logger.info(f"Created task {task.id}: type={task_type}, cmd={str(task.command)[:80]}")

        return jsonify({'task': task.to_dict()}), 201


@tasks_bp.route('/create-with-deps', endpoint='create_with_deps', methods=['POST'])
@require_auth
def create_with_dependencies():
    """
    创建带依赖的任务组 (DAG).

    Request Body:
    {
      "session_id": "uuid",
      "tasks": [
        {"type": "command", "command": "npm install", "deps": []},
        {"type": "command", "command": "npm test", "deps": ["<prev_task_id>"]}
      ]
    }
    """
    return run_async(_create_with_deps_impl())


async def _create_with_deps_impl():
    data = request.get_json(silent=True) or {}
    tasks_data = data.get('tasks', [])

    if not tasks_data:
        raise ValidationError('tasks list is required and cannot be empty')

    async with await get_db() as db:
        created_tasks = []
        task_map = {}

        # 第一轮：创建所有任务
        for t in tasks_data:
            has_deps = bool(t.get('deps'))
            task = Task(
                id=str(uuid.uuid4()),
                session_id=data.get('session_id'),
                task_type=t.get('type', 'command'),
                command=t.get('command'),
                status='waiting' if has_deps else 'pending',
                cwd=t.get('cwd'),
                metadata_=t.get('metadata', {}),
            )
            db.add(task)
            created_tasks.append(task)
            task_map[task.id] = task

        await db.flush()

        # 第二轮：创建依赖关系（使用实际 ID 映射）
        dep_count = 0
        for i, t in enumerate(tasks_data):
            task = created_tasks[i]
            for dep_ref in t.get('deps', []):
                # dep_ref 可能是索引或 ID
                if isinstance(dep_ref, int) and 0 <= dep_ref < len(created_tasks):
                    dep_task = created_tasks[dep_ref]
                elif dep_ref in task_map:
                    dep_task = task_map[dep_ref]
                else:
                    continue

                dep = TaskDependency(
                    task_id=task.id,
                    dep_task_id=dep_task.id,
                    auto_unlock=t.get('auto_unlock', True),
                )
                db.add(dep)
                dep_count += 1

        await db.commit()

        logger.info(f"Created DAG: {len(created_tasks)} tasks, {dep_count} deps")

        return jsonify({
            'tasks': [t.to_dict() for t in created_tasks],
            'total': len(created_tasks),
            'dependency_count': dep_count,
        }), 201


@tasks_bp.route('/<task_id>', endpoint='get_task', methods=['GET'])
@require_auth
def get_task(task_id: str):
    """获取任务详情（含依赖树）."""
    return run_async(_get_task_impl(task_id))


async def _get_task_impl(task_id: str):
    async with await get_db() as db:
        result = await db.execute(
            select(Task)
            .options(selectinload(Task.dependencies), selectinload(Task.dependents))
            .where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise NotFoundError('Task', task_id)

        response = task.to_dict()
        response['dependencies'] = [d.to_dict() for d in task.dependencies]
        response['dependents'] = [d.to_dict() for d in task.dependents]

        return jsonify(response)


@tasks_bp.route('/<task_id>/output', endpoint='get_task_output', methods=['GET'])
@require_auth
def get_task_output(task_id: str):
    """获取任务输出."""
    return run_async(_get_task_output_impl(task_id))


async def _get_task_output_impl(task_id: str):
    async with await get_db() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise NotFoundError('Task', task_id)

        return jsonify({
            'output': task.result,
            'error': task.error,
            'exit_code': task.exit_code,
            'pid': task.pid,
            'status': task.status,
        })


@tasks_bp.route('/<task_id>/stop', endpoint='stop_task', methods=['PUT'])
@require_auth
def stop_task(task_id: str):
    """停止正在运行的任务."""
    return run_async(_stop_task_impl(task_id))


async def _stop_task_impl(task_id: str):
    valid_transitions = {'running': 'stopped', 'pending': 'cancelled'}

    async with await get_db() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise NotFoundError('Task', task_id)

        if task.status not in valid_transitions:
            raise ValidationError(
                f'Cannot stop task in status "{task.status}". '
                f'Valid statuses: {list(valid_transitions.keys())}'
            )

        old_status = task.status
        task.status = valid_transitions[old_status]
        task.completed_at = datetime.now(timezone.utc)
        await db.commit()

        logger.info(f"Stopped task {task_id}: {old_status} → {task.status}")

        return jsonify({
            'message': f'Task {task_id} stopped',
            'previous_status': old_status,
            'new_status': task.status,
        })


@tasks_bp.route('/<task_id>/update', endpoint='update_task_status', methods=['PUT'])
@require_auth
def update_task_status(task_id: str):
    """
    更新任务状态和结果.

    Request Body:
    {
      "status": "completed",
      "result": "输出内容",
      "error": null,
      "exit_code": 0
    }
    """
    return run_async(_update_task_status_impl(task_id))


async def _update_task_status_impl(task_id: str):
    VALID_STATUSES = {'pending', 'waiting', 'running', 'completed', 'failed', 'stopped', 'cancelled'}
    STATUS_TRANSITIONS = {
        'pending': {'running', 'cancelled'},
        'waiting': {'pending', 'cancelled'},
        'running': {'completed', 'failed', 'stopped'},
        'failed': {'pending'},  # 允许重试
        'stopped': {'pending'},  # 允许重启
    }

    data = request.get_json(silent=True) or {}
    new_status = data.get('status')

    async with await get_db() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise NotFoundError('Task', task_id)

        if new_status:
            if new_status not in VALID_STATUSES:
                raise ValidationError(f'Invalid status: {new_status}. Valid: {VALID_STATUSES}')

            allowed = STATUS_TRANSITIONS.get(task.status, set())
            if new_status not in allowed:
                raise ValidationError(
                    f'Cannot transition from "{task.status}" to "{new_status}". '
                    f'Allowed: {allowed}'
                )

            task.status
            task.status = new_status

            if new_status == 'running':
                task.started_at = datetime.now(timezone.utc)
            elif new_status in ('completed', 'failed', 'stopped', 'cancelled'):
                task.completed_at = datetime.now(timezone.utc)

        # 更新其他字段
        updatable = ('result', 'error', 'exit_code', 'pid', 'output_path')
        updated_fields = []
        for field in updatable:
            if field in data:
                setattr(task, field, data[field])
                updated_fields.append(field)

        await db.commit()
        await db.refresh(task)

        logger.info(f"Updated task {task_id}: fields={updated_fields}")

        return jsonify({
            'task': task.to_dict(),
            'updated_fields': updated_fields,
            'status_changed': new_status is not None,
        })


@tasks_bp.route('/<task_id>', endpoint='delete_task', methods=['DELETE'])
@require_auth
def delete_task(task_id: str):
    """删除任务及其所有依赖关系."""
    return run_async(_delete_task_impl(task_id))


async def _delete_task_impl(task_id: str):
    async with await get_db() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise NotFoundError('Task', task_id)

        # 级联删除依赖关系 (cascade 已在 relationship 中配置)
        await db.delete(task)
        await db.commit()

        logger.info(f"Deleted task {task_id}")

        return jsonify({
            'message': f'Task {task_id} deleted',
            'deleted_id': task_id,
        })


@tasks_bp.route('/<task_id>/deps', endpoint='list_task_deps', methods=['GET'])
@require_auth
def get_task_deps(task_id: str):
    """获取任务的依赖关系（双向）."""
    return run_async(_get_task_deps_impl(task_id))


async def _get_task_deps_impl(task_id: str):
    async with await get_db() as db:
        result = await db.execute(
            select(Task)
            .options(selectinload(Task.dependencies), selectinload(Task.dependents))
            .where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise NotFoundError('Task', task_id)

        return jsonify({
            'task_id': task_id,
            'dependencies': [
                {
                    **d.to_dict(),
                    'dep_task_command': d.dependent.command[:100] if d.dependent else None,
                }
                for d in task.dependencies
            ],
            'dependents': [
                {
                    **d.to_dict(),
                    'dependent_task_command': d.task.command[:100] if d.task else None,
                }
                for d in task.dependents
            ],
        })


@tasks_bp.route('/<task_id>/deps', endpoint='add_dependency', methods=['POST'])
@require_auth
def add_dependency(task_id: str):
    """为任务添加新的依赖."""
    return run_async(_add_dep_impl(task_id))


async def _add_dep_impl(task_id: str):
    data = request.get_json(silent=True) or {}
    dep_task_id = data.get('dep_task_id')

    if not dep_task_id:
        raise ValidationError('dep_task_id is required', field='dep_task_id')

    async with await get_db() as db:
        # 验证两个任务都存在
        for tid in (task_id, dep_task_id):
            exists = await db.execute(select(Task).where(Task.id == tid))
            if not exists.scalar_one_or_none():
                raise NotFoundError('Task', tid)

        # 检查是否已存在相同依赖
        existing = await db.execute(
            select(TaskDependency).where(
                TaskDependency.task_id == task_id,
                TaskDependency.dep_task_id == dep_task_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValidationError('Dependency already exists')

        dep = TaskDependency(
            id=str(uuid.uuid4()),
            task_id=task_id,
            dep_task_id=dep_task_id,
            auto_unlock=data.get('auto_unlock', True),
        )
        db.add(dep)

        # 如果添加了依赖且任务还在 pending 状态，改为 waiting
        task_result = await db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one_or_none()
        if task and task.status == 'pending':
            task.status = 'waiting'

        await db.commit()

        return jsonify({'dependency': dep.to_dict()}), 201


@tasks_bp.route('/stats', endpoint='task_stats', methods=['GET'])
@require_auth
def task_stats():
    """全局任务统计."""
    return run_async(_task_stats_impl())


async def _task_stats_impl():
    async with await get_db() as db:
        total_result = await db.execute(select(func.count(Task.id)))
        total = total_result.scalar() or 0

        stats_result = await db.execute(
            select(
                Task.status,
                func.count(Task.id).label('count'),
                func.avg(
                    case((Task.completed_at.isnot(None), Task.completed_at - Task.created_at), else_=None)
                ).label('avg_duration_seconds'),
            ).group_by(Task.status)
        )
        rows = stats_result.all()

        by_status = {}
        for row in rows:
            by_status[row[0]] = {
                'count': row[1],
                'avg_duration_seconds': round(row[2].total_seconds(), 1) if row[2] else None,
            }

        running_result = await db.execute(
            select(func.count(Task.id)).where(Task.status == 'running')
        )
        active = running_result.scalar() or 0

        return jsonify({
            'total': total,
            'active': active,
            'by_status': by_status,
        })
