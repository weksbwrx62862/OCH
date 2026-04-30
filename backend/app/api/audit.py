"""Audit Log API — DB-persistent audit trail with export."""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request, Response
from sqlalchemy import delete, select, func

from app.core.async_utils import run_async, get_db
from app.core.exceptions import NotFoundError
from app.core.security import require_auth, require_role
from app.models.permission import AuditLog

logger = logging.getLogger(__name__)
audit_bp = Blueprint('audit', __name__)



@audit_bp.route('', methods=['GET'])
@require_auth
def list_audit_logs():
    """
    审计日志列表（分页 + 多维度筛选 + 导出支持）
    ---
    tags:
      - Audit
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
        maximum: 100
      - in: query
        name: action
        type: string
        enum: [tool_use, tool_denied, session_create, auth_fail, config_change]
        description: 按操作类型筛选
      - in: query
        name: user_id
        type: string
        description: 按用户 ID 筛选
      - in: query
        name: from_date
        type: string
        format: date-time
        description: 起始时间 (ISO 8601)
      - in: query
        name: to_date
        type: string
        format: date-time
        description: 结束时间 (ISO 8601)
    responses:
      200:
        description: 审计日志分页列表（data/total/page/per_page）
      401:
        description: 未认证
    """
    return run_async(_list_logs_impl())


async def _list_logs_impl():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    action_filter = request.args.get('action')
    user_id = request.args.get('user_id')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    async with await get_db() as db:
        query = select(AuditLog)

        if action_filter:
            query = query.where(AuditLog.action == action_filter)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if from_date:
            try:
                dt = datetime.fromisoformat(from_date)
                query = query.where(AuditLog.created_at >= dt)
            except ValueError:
                pass
        if to_date:
            try:
                dt = datetime.fromisoformat(to_date)
                query = query.where(AuditLog.created_at <= dt)
            except ValueError:
                pass

        # 总数
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        result = await db.execute(
            query.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * per_page).limit(per_page)
        )
        logs = [log_entry.to_dict() for log_entry in result.scalars().all()]

        return jsonify({
            'data': logs,
            'total': total,
            'page': page,
            'per_page': per_page,
        })


@audit_bp.route('/<log_id>', endpoint='log_id', methods=['GET'])
@require_auth
def get_audit_log(log_id: str):
    """单条日志详情."""
    return run_async(_get_log_impl(log_id))


async def _get_log_impl(log_id: str):
    async with await get_db() as db:
        result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
        log = result.scalar_one_or_none()
        if not log:
            raise NotFoundError('Audit Log', log_id)
        return jsonify(log.to_dict())


@audit_bp.route('/stats', endpoint='stats', methods=['GET'])
@require_auth
def audit_stats():
    """审计统计."""
    return run_async(_stats_impl())


async def _stats_impl():
    async with await get_db() as db:
        total_result = await db.execute(
            select(func.count()).select_from(
                select(AuditLog.id).subquery()
            )
        )
        total = total_result.scalar() or 0

        by_action = {}
        action_rows = await db.execute(
            select(
                AuditLog.action,
                func.count(AuditLog.id),
            ).group_by(AuditLog.action)
        )
        for row in action_rows.all():
            by_action[row[0]] = row[1]

        recent_rows = await db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(5)
        )
        recent = [log_entry.to_dict() for log_entry in recent_rows.scalars().all()]

        return jsonify({
            'total': total,
            'by_action': by_action,
            'recent': recent,
        })


@audit_bp.route('/export', endpoint='export', methods=['GET'])
@require_role('admin')
def export_audit_logs():
    """导出审计报告."""
    fmt = request.args.get('format', 'json')
    limit = min(request.args.get('limit', 10000, type=int), 50000)

    return run_async(_export_impl(fmt, limit))


async def _export_impl(fmt: str, limit: int):
    async with await get_db() as db:
        result = await db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        logs = result.scalars().all()

        if fmt == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['id', 'timestamp', 'action', 'user_id', 'resource_type',
                            'resource_id', 'ip_address', 'details'])
            for log_entry in logs:
                writer.writerow([
                    log_entry.id, log_entry.created_at.isoformat(), log_entry.action, log_entry.user_id or '',
                    log_entry.resource_type or '', log_entry.resource_id or '',
                    log_entry.ip_address or '', str(log_entry.details) if log_entry.details else '',
                ])
            return Response(output.getvalue(), mimetype='text/csv',
                           headers={'Content-Disposition': f'attachment; filename=audit-{datetime.now(timezone.utc):%Y%m%d}.csv'})

        data = [log_entry.to_dict() for log_entry in logs]
        return jsonify({'total': len(data), 'logs': data})


@audit_bp.route('/purge', endpoint='purge', methods=['POST'])
@require_role('admin')
def purge_old_logs():
    """清理过期日志."""
    days = request.args.get('older_than_days', 90, type=int)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    return run_async(_purge_impl(cutoff))


async def _purge_impl(cutoff: datetime):
    async with await get_db() as db:
        result = await db.execute(
            delete(AuditLog).where(AuditLog.created_at < cutoff)
        )
        count = result.rowcount
        await db.commit()

        logger.info(f"Purged {count} audit logs older than {cutoff.isoformat()}")
        return jsonify({'message': f'Purged {count} old audit logs'})
