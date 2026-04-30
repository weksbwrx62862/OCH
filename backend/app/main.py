"""OpenClaw-Harness Backend — Flask Application Entry Point."""

from __future__ import annotations

import asyncio
import atexit
import logging
from functools import wraps
from flask import Flask, jsonify, request as flask_request
from flask_cors import CORS
from flask_socketio import SocketIO
from flasgger import Swagger

from app.config import get_settings
from app.core.security import init_security
from app.middleware import create_default_pipeline, MiddlewarePipeline, MiddlewareContext, MiddlewarePhase
from app.api.websocket import (
    handle_connect,
    handle_disconnect,
    on_join_session,
    on_leave_session,
    handle_ping,
)

logger = logging.getLogger(__name__)

socketio = SocketIO(async_mode='threading', cors_allowed_origins=get_settings().CORS_ORIGINS, logger=True)

# P1-1: 全局中间件管道实例
_middleware_pipeline: MiddlewarePipeline = create_default_pipeline()


def _run_middleware_sync(ctx):
    """同步执行中间件管道（asyncio.run 不可用时的回退方案）."""
    from app.core.security import verify_token
    from flask import g, request as flask_request
    from app.middleware import MiddlewareResult

    g.user = None

    if flask_request.method == "OPTIONS":
        return MiddlewareResult()

    token = flask_request.headers.get("Authorization", "").replace("Bearer ", "")
    public_paths = frozenset(["/api/v1/auth/login", "/api/v1/health", "/health", "/apidocs/", "/flasgger_static/", "/apispec.json"])
    if flask_request.path in public_paths:
        return MiddlewareResult()
    if not flask_request.path.startswith("/api/"):
        return MiddlewareResult()
    if not token:
        return MiddlewareResult(blocked=True, block_reason="Authentication required")
    payload = verify_token(token)
    if payload is None:
        return MiddlewareResult(blocked=True, block_reason="Invalid or expired token")
    ctx.metadata["user_id"] = payload.get("sub")
    ctx.metadata["role"] = payload.get("role", "user")
    g.user = payload
    return MiddlewareResult(modified=True)


def async_handler(async_func):
    """将 async 函数包装为 Flask 同步处理（解决 Flask Blueprint 不支持 async 的问题）."""
    @wraps(async_func)
    def sync_wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
            return loop.run_until_complete(async_func(*args, **kwargs))
        except Exception as e:
            logger.exception(f"Async handler error in {async_func.__name__}: {e}")
            raise
    return sync_wrapper


def create_app() -> Flask:
    """Application factory."""
    settings = get_settings()

    app = Flask(
        __name__,
        static_folder='../frontend/public',
        template_folder='../frontend/public',
    )
    app.config.from_object(settings)

    # CORS
    CORS(
        app,
        resources={r"/api/*": {"origins": settings.CORS_ORIGINS}},
        supports_credentials=True,
    )

    # Swagger UI (API 交互式文档)
    app.config['SWAGGER'] = {
        'title': 'OpenClaw-Harness API',
        'version': '0.1.0',
        'description': (
            'OpenClaw 外挂扩展平台 — 多智能体协作框架\n\n'
            '**核心功能：**\n'
            '- 智能体（Agent）管理 — 创建、配置、部署 AI 智能体\n'
            '- 会话（Session）管理 — 多轮对话、状态跟踪、消息记录\n'
            '- 任务（Task）调度 — 后台任务执行、DAG 依赖管理\n'
            '- 权限（Permission）控制 — 细粒度工具调用权限、路径规则引擎\n'
            '- 协调器（Coordinator）— 多 Agent 团队协作与任务分派\n\n'
            '**认证方式：** Bearer Token (JWT)\n'
            '**基础 URL：** `/api/v1`'
        ),
        'uiversion': 3,
        'contact': {'developer': 'OpenClaw Team'},
        'tags': [
            {'name': 'Agents', 'description': '智能体 CRUD 和配置'},
            {'name': 'Sessions', 'description': '会话生命周期和对话管理'},
            {'name': 'Chat', 'description': '聊天消息发送和流式响应'},
            {'name': 'Tasks', 'description': '后台任务创建、调度和监控'},
            {'name': 'Skills', 'description': '技能注册、启用/禁用和扫描'},
            {'name': 'Tools', 'description': '工具发现、Schema 获取和安全检查'},
            {'name': 'Permissions', 'description': '权限规则 CRUD 和验证'},
            {'name': 'Config', 'description': '系统配置读取和更新'},
            {'name': 'Audit', 'description': '审计日志查询和导出'},
            {'name': 'Memory', 'description': '记忆事实库 CRUD 和语义检索'},
            {'name': 'MCP', 'description': 'Model Context Protocol 服务器管理'},
            {'name': 'Channels', 'description': '多平台消息渠道配置'},
            {'name': 'Sandbox', 'description': '沙箱环境管理和代码执行'},
            {'name': 'Coordinator', 'description': '多智能体协调器和团队管理'},
        ],
    }

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule": "all",
                "model": "openapi_3",
                "validation": True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
    }

    Swagger(app, config=swagger_config)

    # Register blueprints
    _register_blueprints(app)

    # Initialize security (JWT auth before_request handler)
    init_security(app)

    # Register WebSocket events (SocketIO)
    _register_socketio_events()

    # Error handlers
    _register_error_handlers(app)
    _register_custom_exception_handlers(app)

    # Health check
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'openclaw-harness', 'version': '0.1.0'}

    # P1-1: 中间件管道信息端点
    @app.route('/api/v1/middleware', methods=['GET'])
    def middleware_info():
        return jsonify({
            'pipeline': _middleware_pipeline.get_info(),
            'total_middlewares': len(_middleware_pipeline.middlewares),
        })

    # P1-1: 注册 before_request 钩子（执行中间件管道）
    @app.before_request
    def run_middleware_before_request():
        ctx = MiddlewareContext(request=flask_request)
        try:
            result = asyncio.run(
                _middleware_pipeline.execute_phase(MiddlewarePhase.BEFORE_REQUEST, ctx)
            )
        except RuntimeError:
            result = _run_middleware_sync(ctx)
        if result.blocked:
            from flask import make_response
            status_code = 404 if 'not found' in result.block_reason.lower() else 401
            return make_response(jsonify({'error': result.block_reason, 'code': status_code}), status_code)

    logger.info("中间件管道已激活 (%d 个中间件)", len(_middleware_pipeline.middlewares))

    def _shutdown_db():
        from app.core.async_utils import dispose_engine
        loop = asyncio.new_event_loop()
        loop.run_until_complete(dispose_engine())
        loop.close()

    atexit.register(_shutdown_db)

    return app


def _register_blueprints(app: Flask) -> None:
    """Register all API blueprints."""
    from app.api import auth_bp
    from app.api import agents_bp, sessions_bp, tools_bp, skills_bp
    from app.api import coordinator_bp, permissions_bp, tasks_bp
    from app.api import config_bp, plugins_bp, mcp_bp, audit_bp, memory_bp, channels_bp, sandbox_bp

    api_prefix = '/api/v1'

    app.register_blueprint(auth_bp)

    blueprints = [
        (agents_bp, '/agents'),
        (sessions_bp, '/sessions'),
        (tools_bp, '/tools'),
        (skills_bp, '/skills'),
        (coordinator_bp, '/coordinator'),
        (permissions_bp, '/permissions'),
        (tasks_bp, '/tasks'),
        (config_bp, '/config'),
        (plugins_bp, '/plugins'),
        (mcp_bp, '/mcp'),
        (audit_bp, '/audit'),
        (memory_bp, '/memory'),
        (channels_bp, '/channels'),
        (sandbox_bp, '/sandbox'),
    ]

    for bp, url_prefix in blueprints:
        app.register_blueprint(bp, url_prefix=f'{api_prefix}{url_prefix}')
        logger.debug(f"Registered blueprint: {bp.name} → {api_prefix}{url_prefix}")


def _register_socketio_events() -> None:
    """注册所有 Socket.IO 事件处理器."""
    socketio.on_event('connect', handle_connect)
    socketio.on_event('disconnect', handle_disconnect)
    socketio.on_event('join_session', on_join_session)
    socketio.on_event('leave_session', on_leave_session)
    socketio.on_event('ping', handle_ping)
    logger.debug("Registered Socket.IO event handlers")


def _register_error_handlers(app: Flask) -> None:
    """Register global error handlers."""

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'code': 404}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.exception("Internal server error")
        return jsonify({'error': 'Internal server error', 'code': 500}), 500

    @app.errorhandler(400)
    def bad_request(error):
        if get_settings().APP_ENV != "development":
            return jsonify({'error': 'Bad request', 'code': 400}), 400
        return jsonify({'error': str(error.description or 'Bad request'), 'code': 400}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized', 'code': 401}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'code': 403}), 403


def _register_custom_exception_handlers(app: Flask) -> None:
    """注册自定义异常处理器."""

    from app.core.exceptions import OCHError

    @app.errorhandler(OCHError)
    def handle_och_error(error: OCHError):
        logger.warning(f"OCHError: {error.message} (code={error.code})")
        return jsonify({
            'error': error.message,
            'code': error.code,
            'details': error.details,
        }), error.code

    @app.errorhandler(Exception)
    def handle_generic_error(error: Exception):
        logger.exception("Unhandled exception")
        if get_settings().APP_ENV != "development":
            return jsonify({'error': 'Internal server error', 'code': 500}), 500
        return jsonify({
            'error': str(error),
            'code': 500,
            'type': type(error).__name__,
        }), 500


if __name__ == '__main__':

    app = create_app()
    socketio.init_app(app)

    logger.info("🚀 Starting OpenClaw-Harness Backend on http://0.0.0.0:8008")

    socketio.run(
        app,
        host='0.0.0.0',
        port=8008,
        debug=True,
        allow_unsafe_werkzeug=True,
    )
