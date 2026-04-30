"""WebSocket Handler — Real-time communication via Socket.IO.

Provides real-time updates for:
- Session status changes
- Tool execution progress
- Agent spawning events
- System notifications

注意: 所有 socketio 事件处理器在 main.py 中注册，
这里只定义处理函数和 emit 辅助函数.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from flask_socketio import emit, join_room, leave_room
from flask import request as flask_request

logger = logging.getLogger(__name__)


# ============================================================
# Socket.IO Event Handlers (由 main.py 注册)
# ============================================================


def handle_connect():
    from app.core.security import verify_token
    token = flask_request.args.get('token') or flask_request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        logger.warning(f"WebSocket connection rejected: no token (sid={flask_request.sid})")
        return False
    payload = verify_token(token)
    if payload is None:
        logger.warning(f"WebSocket connection rejected: invalid token (sid={flask_request.sid})")
        return False
    logger.info(f"Client connected: {flask_request.sid} (user={payload.get('username')})")
    emit('connected', {
        'sid': flask_request.sid,
        'server_time': datetime.now(timezone.utc).isoformat(),
        'message': 'Connected to OpenClaw-Harness WebSocket',
    })


def handle_disconnect():
    """客户端断开连接."""
    logger.info(f"Client disconnected: {flask_request.sid}")


def on_join_session(data: Dict[str, str]):
    """
    加入会话房间 — 接收该会话的实时更新.

    Event data:
    {
      "session_id": "uuid"
    }
    """
    session_id = data.get('session_id')
    if not session_id:
        emit('error', {'message': 'session_id is required'})
        return

    room = f'session:{session_id}'
    join_room(room)
    logger.info(f"Client {flask_request.sid} joined room {room}")

    emit('joined', {
        'room': room,
        'session_id': session_id,
        'message': f'Now listening to session {session_id}',
    })


def on_leave_session(data: Dict[str, str]):
    """离开会话房间."""
    session_id = data.get('session_id')
    if session_id:
        room = f'session:{session_id}'
        leave_room(room)
        logger.info(f"Client {flask_request.sid} left room {room}")
        emit('left', {'room': room})


def handle_ping():
    """心跳检测."""
    emit('pong', {
        'server_time': datetime.now(timezone.utc).isoformat(),
        'latency': None,
    })


# ============================================================
# Server-side Emit Functions (被其他 API 调用)
# ============================================================


def emit_session_event(session_id: str, event_type: str, data: Dict[str, Any]) -> None:
    """
    向特定会话的所有监听者发送事件.

    Usage (from other modules):
        from app.api.websocket import emit_session_event
        emit_session_event(session_id, 'tool_started', {...})
    """
    from app.main import socketio

    room = f'session:{session_id}'
    socketio.emit('session_event', {
        'type': event_type,
        'session_id': session_id,
        'data': data,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }, to=room)


def emit_tool_progress(
    session_id: str,
    tool_name: str,
    status: str,
    message: str = '',
    progress: int = 0,
) -> None:
    """发送工具执行进度更新."""
    emit_session_event(session_id, 'tool_progress', {
        'tool_name': tool_name,
        'status': status,
        'message': message,
        'progress': progress,
    })


def emit_system_notification(
    level: str = 'info',
    title: str = '',
    message: str = '',
) -> None:
    """发送系统级通知（广播给所有连接的客户端）."""
    from app.main import socketio

    socketio.emit('system_notification', {
        'level': level,
        'title': title,
        'message': message,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })


def emit_agent_status(agent_id: str, status: str, details: Optional[Dict] = None) -> None:
    """发送 Agent 状态变更通知."""
    from app.main import socketio

    room = f'agent:{agent_id}'
    socketio.emit('agent_status', {
        'agent_id': agent_id,
        'status': status,
        'details': details or {},
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }, to=room)
