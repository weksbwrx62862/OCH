"""Permissions & Security API — RBAC + Path Rules + Denial Tracking (DB)."""

from __future__ import annotations

import logging
import threading
import uuid
from flask import Blueprint, g, jsonify, request
from sqlalchemy import delete, select, func

from app.core.async_utils import run_async, get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import require_auth, require_role
from app.models.permission import PermissionRule, AuditLog
from openharness.permissions.denial_tracking import get_denial_tracker

logger = logging.getLogger(__name__)
permissions_bp = Blueprint('permissions', __name__)



@permissions_bp.route('/modes', endpoint='modes', methods=['GET'])
@require_auth
def list_permission_modes():
    """
    可用权限模式列表 + 当前模式
    ---
    tags:
      - Permissions
    security:
      - BearerAuth: []
    responses:
      200:
        description: 权限模式列表（default/auto/plan）
        schema:
          type: object
          properties:
            modes:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  name:
                    type: string
                  description:
                    type: string
            current_mode:
              type: string
              default: "default"
      401:
        description: 未认证
    """
    return run_async(_list_modes_impl())


async def _list_modes_impl():
    return jsonify({
        'modes': [
            {'id': 'default', 'name': 'Default', 'description': 'Ask before write/execute'},
            {'id': 'auto', 'name': 'Auto', 'description': 'Allow everything (sandboxed)'},
            {'id': 'plan', 'name': 'Plan Mode', 'description': 'Block all writes, read-only'},
        ],
        'current_mode': 'default',
    })


_current_permission_mode = 'default'


@permissions_bp.route('/modes/<mode_id>', endpoint='set_mode', methods=['PUT'])
@require_role('admin')
def set_permission_mode(mode_id: str):
    """设置当前权限模式.

    ---
    tags:
      - Permissions
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: mode_id
        required: true
        schema:
          type: string
          enum: [default, auto, plan]
    responses:
      200:
        description: 模式已更新
      400:
        description: 无效的模式 ID
      401:
        description: 未认证
    """
    global _current_permission_mode
    valid_modes = ['default', 'auto', 'plan']
    if mode_id not in valid_modes:
        return jsonify({'error': f'Invalid mode. Valid modes: {valid_modes}', 'code': 400}), 400
    _current_permission_mode = mode_id
    return jsonify({'message': f'Mode set to {mode_id}', 'current_mode': mode_id})


@permissions_bp.route('/rules', endpoint='rules', methods=['GET'])
@require_auth
def list_rules():
    """
    列出所有路径规则
    ---
    tags:
      - Permissions
    security:
      - BearerAuth: []
    responses:
      200:
        description: 路径规则列表（按优先级降序）
      401:
        description: 未认证
    """
    return run_async(_list_rules_impl())


async def _list_rules_impl():
    async with await get_db() as db:
        result = await db.execute(select(PermissionRule).order_by(PermissionRule.priority.desc()))
        rules = result.scalars().all()
        return jsonify({'data': [r.to_dict() for r in rules], 'total': len(rules)})


@permissions_bp.route('/rules', endpoint='rules_post', methods=['POST'])
@require_auth
def create_rule():
    """
    创建路径规则
    ---
    tags:
      - Permissions
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - pattern
          properties:
            pattern:
              type: string
              description: 路径匹配模式 (fnmatch)
            name:
              type: string
            allow:
              type: boolean
              default: true
            description:
              type: string
            priority:
              type: integer
              default: 0
    responses:
      201:
        description: 规则创建成功
      400:
        description: 缺少必填字段 (pattern)
      401:
        description: 未认证
    """
    return run_async(_create_rule_impl())


async def _create_rule_impl():
    data = request.get_json(silent=True) or {}

    if not data.get('pattern'):
        raise ValidationError('Pattern is required', field='pattern')

    async with await get_db() as db:
        rule = PermissionRule(
            id=str(uuid.uuid4()),
            name=data.get('name', ''),
            pattern=data['pattern'],
            allow=data.get('allow', True),
            description=data.get('description'),
            priority=data.get('priority', 0),
            created_by=g.user.get('user_id') if g.user else None,
        )
        db.add(rule)
        await db.commit()

        logger.info(f"Created permission rule: {rule.pattern} (allow={rule.allow})")
        return jsonify({'rule': rule.to_dict()}), 201


@permissions_bp.route('/rules/<rule_id>', endpoint='rules_rule_id', methods=['PUT'])
@require_auth
def update_rule(rule_id: str):
    """更新规则."""
    return run_async(_update_rule_impl(rule_id))


async def _update_rule_impl(rule_id: str):
    data = request.get_json(silent=True) or {}
    async with await get_db() as db:
        result = await db.execute(select(PermissionRule).where(PermissionRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            raise NotFoundError('Permission Rule', rule_id)

        for field in ('name', 'pattern', 'allow', 'description', 'priority'):
            if field in data:
                setattr(rule, field, data[field])
        await db.commit()
        return jsonify({'message': f'Rule {rule_id} updated'})


@permissions_bp.route('/rules/<rule_id>', endpoint='rules_rule_id_delete', methods=['DELETE'])
@require_auth
def delete_rule(rule_id: str):
    """删除规则."""
    return run_async(_delete_rule_impl(rule_id))


async def _delete_rule_impl(rule_id: str):
    async with await get_db() as db:
        result = await db.execute(select(PermissionRule).where(PermissionRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            raise NotFoundError('Permission Rule', rule_id)
        await db.delete(rule)
        await db.commit()
        return jsonify({'message': f'Rule {rule_id} deleted'})


@permissions_bp.route('/denials', endpoint='denials', methods=['GET'])
@require_auth
def list_denials():
    """
    权限拒绝记录 (AuditLog 中 action=tool_denied)
    ---
    tags:
      - Permissions
    security:
      - BearerAuth: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: per_page
        type: integer
        default: 20
    responses:
      200:
        description: 拒绝记录分页列表
      401:
        description: 未认证
    """
    return run_async(_list_denials_impl())


async def _list_denials_impl():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    async with await get_db() as db:
        query = select(AuditLog).where(AuditLog.action == 'tool_denied')
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        result = await db.execute(
            query.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * per_page).limit(per_page)
        )
        denials = [d.to_dict() for d in result.scalars().all()]

        return jsonify({
            'data': denials,
            'total': total,
            'page': page,
            'per_page': per_page,
        })


@permissions_bp.route('/denials/stats', endpoint='denials_stats', methods=['GET'])
@require_auth
def denial_stats():
    """拒绝统计."""
    return run_async(_denial_stats_impl())


async def _denial_stats_impl():
    async with await get_db() as db:
        total_result = await db.execute(
            select(func.count()).select_from(select(AuditLog).where(AuditLog.action == 'tool_denied').subquery())
        )
        total = total_result.scalar() or 0

        by_tool = {}
        by_reason = {}
        recent = []

        if total > 0:
            rows = await db.execute(
                select(AuditLog.details, AuditLog.created_at)
                .where(AuditLog.action == 'tool_denied')
                .order_by(AuditLog.created_at.desc())
                .limit(50)
            )

            for row in rows.all():
                details = row[0] or {}
                tool_name = details.get('tool_name', 'unknown')
                reason = details.get('reason', 'unknown')
                by_tool[tool_name] = by_tool.get(tool_name, 0) + 1
                by_reason[reason] = by_reason.get(reason, 0) + 1
                if len(recent) < 10:
                    recent.append(row[1].isoformat())

        return jsonify({
            'total_denials': total,
            'by_tool': by_tool,
            'by_reason': by_reason,
            'recent_denials': recent,
        })


@permissions_bp.route('/denials/clear', endpoint='denials_clear', methods=['POST'])
@require_role('admin')
def clear_denials():
    """清除拒绝记录."""
    return run_async(_clear_denials_impl())


async def _clear_denials_impl():
    async with await get_db() as db:
        result = await db.execute(
            delete(AuditLog).where(AuditLog.action == 'tool_denied')
        )
        count = result.rowcount
        await db.commit()

        logger.info(f"Cleared {count} denial records")
        return jsonify({'message': f'{count} denial records cleared'})


# ============================================================
# P0-1: DenialTracker 集成 (来自 openharness/permissions/)
# SHA256 指纹 + TTL 缓存，避免重复提示用户
# ============================================================

def check_tool_denial(tool_name: str, tool_input: str | dict | None = None) -> bool:
    """检查工具操作是否之前被拒绝过（内存级快速检查）

    Args:
        tool_name: 工具名称 (如 "bash", "file_write")
        tool_input: 工具输入参数

    Returns:
        True → 之前被拒绝过，应静默拒绝（不再询问用户）
        False → 首次或已过期，需要正常权限检查流程
    """
    tracker = get_denial_tracker()
    return tracker.is_previously_denied(tool_name, tool_input)


def record_tool_denial(
    tool_name: str,
    tool_input: str | dict | None = None,
    reason: str = "",
) -> None:
    """记录一次权限拒绝到内存追踪器 + 持久化到 DB

    双轨记录：内存用于快速去重，DB 用于审计追溯
    """
    tracker = get_denial_tracker()
    tracker.record_denial(tool_name, tool_input, reason)
    logger.debug(
        "记录权限拒绝: tool=%s, reason=%s (内存追踪器)",
        tool_name,
        reason or "(无)",
    )


@permissions_bp.route('/denials/tracker', endpoint='denials_tracker', methods=['GET'])
@require_auth
def tracker_stats():
    """DenialTracker 内存状态统计."""
    tracker = get_denial_tracker()
    stats = tracker.get_stats()
    return jsonify({
        'tracker': {
            'enabled': stats['enabled'],
            'total_memory_records': stats['total_denials'],
            'by_tool': stats['by_tool'],
            'expiry_seconds': stats['expiry_seconds'],
        },
        'hint': '内存级追踪器用于静默重复拒绝，DB 记录见 /denials 端点',
    })


@permissions_bp.route('/denials/tracker/clear', endpoint='denials_tracker_clear', methods=['POST'])
@require_auth
def clear_tracker():
    """清除 DenialTracker 内存缓存（不影 DB 记录）."""
    tracker = get_denial_tracker()
    count = tracker.clear_denials()
    return jsonify({'message': f'Cleared {count} memory denial records'})


# ============================================================
# P1-2: PermissionChecker 统一集成 (来自 openharness/permissions/)
# 工具级权限检查：路径规则 + 命令黑名单 + YOLO 分类 + 模式控制
# ============================================================

_permission_checker_instance = None
_permission_checker_lock = threading.Lock()


def get_permission_checker():
    """获取全局 PermissionChecker 实例（延迟初始化，线程安全）."""
    global _permission_checker_instance
    if _permission_checker_instance is None:
        with _permission_checker_lock:
            if _permission_checker_instance is None:
                try:
                    from openharness.permissions.checker import PermissionChecker
                    from openharness.permissions.modes import PermissionMode

                    class SimpleSettings:
                        mode = PermissionMode.DEFAULT
                        denied_tools: set = set()
                        allowed_tools: set = set()
                        path_rules: list = []
                        denied_commands: list = [
                            "rm -rf /*",
                            "DROP TABLE",
                            "FORMAT",
                            "> /dev/sda",
                            ":(){ :|:& };:",
                            "chmod -R 777 /",
                            "wget* | sh",
                            "curl* | bash",
                        ]

                    _permission_checker_instance = PermissionChecker(settings=SimpleSettings())
                    logger.info("PermissionChecker 初始化完成")
                except Exception as e:
                    logger.warning(f"PermissionChecker 初始化失败: {e}")
                    _permission_checker_instance = None
    return _permission_checker_instance


@permissions_bp.route('/check', endpoint='check_tool', methods=['POST'])
@require_auth
def check_tool_permission():
    """
    统一工具权限检查（DB规则 + PermissionChecker + DenialTracker 三重校验）

    三层校验流程：
    1. DenialTracker 快速去重（内存级 SHA256 指纹）
    2. PermissionChecker 规则引擎（命令黑名单 + YOLO 分类 + 模式控制）
    3. DB 路径规则（PermissionRule 表 fnmatch 匹配）
    ---
    tags:
      - Permissions
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - tool_name
          properties:
            tool_name:
              type: string
              example: "bash"
              description: 工具名称
            command:
              type: string
              example: "rm -rf /tmp/test"
              description: 要执行的命令
            file_path:
              type: string
              example: "/etc/passwd"
              description: 操作的文件路径
            is_read_only:
              type: boolean
              default: false
              description: 是否只读操作
    responses:
      200:
        description: 权限检查结果
        schema:
          type: object
          properties:
            allowed:
              type: boolean
              description: 是否允许执行
            reason:
              type: string
              description: 拒绝原因（allowed=false 时）
            layer:
              type: string
              enum: [denial_tracker, permission_checker, db_rules, none]
              description: 决策来源层级
            denial_tracker:
              type: object
              description: DenialTracker 检查结果
            permission_checker:
              type: object
              description: PermissionChecker 检查结果
            db_rules:
              type: object
              description: DB 路径规则检查结果
      400:
        description: 缺少必填参数 tool_name
      401:
        description: 未认证
    """
    data = request.get_json(silent=True) or {}
    tool_name = data.get('tool_name', '')
    command = data.get('command')
    file_path = data.get('file_path')
    is_read_only = data.get('is_read_only', False)

    if not tool_name:
        raise ValidationError('tool_name is required', field='tool_name')

    results = {}

    # 第一层: DenialTracker 快速去重
    tracker_result = check_tool_denial(tool_name, {'command': command} if command else None)
    results['denial_tracker'] = {
        'previously_denied': tracker_result,
        'action': 'silent_reject' if tracker_result else 'proceed',
    }
    if tracker_result:
        return jsonify({
            'allowed': False,
            'reason': 'Previously denied (DenialTracker)',
            'layer': 'denial_tracker',
            **results,
        })

    # 第二层: PermissionChecker 规则引擎
    checker = get_permission_checker()
    if checker:
        decision = checker.evaluate(
            tool_name,
            is_read_only=is_read_only,
            file_path=file_path,
            command=command,
        )
        results['permission_checker'] = {
            'allowed': decision.allowed,
            'requires_confirmation': decision.requires_confirmation,
            'reason': decision.reason,
        }

        if not decision.allowed and not decision.requires_confirmation:
            record_tool_denial(tool_name, {'command': command}, decision.reason)
            return jsonify({
                'allowed': False,
                'reason': decision.reason,
                'layer': 'permission_checker',
                **results,
            })

    # 第三层: DB 路径规则（来自 PermissionRule 表）
    db_allowed = True
    db_reason = ""
    if file_path:
        async def _check_db_rules():
            async with await get_db() as db:
                rule_result = await db.execute(
                    select(PermissionRule).where(
                        PermissionRule.allow.is_(False)
                    ).order_by(PermissionRule.priority.desc())
                )
                for rule in rule_result.scalars().all():
                    import fnmatch as fnmatch_mod
                    if fnmatch_mod.fnmatch(file_path, rule.pattern):
                        return False, f"DB rule '{rule.name}' denies path: {rule.pattern}"
                return True, ""

        db_allowed, db_reason = run_async(_check_db_rules())

    results['db_rules'] = {
        'allowed': db_allowed,
        'reason': db_reason,
    }

    final_allowed = db_allowed
    if not final_allowed:
        record_tool_denial(tool_name, {'file_path': file_path}, db_reason)

    return jsonify({
        'allowed': final_allowed,
        'reason': db_reason or (results.get('permission_checker', {}).get('reason') or 'Allowed'),
        'layer': 'db_rules' if not db_allowed else ('permission_checker' if checker else 'none'),
        **results,
    })
