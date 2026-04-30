"""Middleware Pipeline — 参考 DeerFlow 12 中间件链模式.

提供有序的请求/响应处理管道，每个中间件职责单一、可组合、可替换。
支持 before_request / after_request / before_tool_call / after_tool_call 生命周期。
"""

from __future__ import annotations

import logging
import time
from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MiddlewarePhase(str, Enum):
    """中间件执行阶段."""

    BEFORE_REQUEST = "before_request"
    AFTER_REQUEST = "after_request"
    BEFORE_TOOL_CALL = "before_tool_call"
    AFTER_TOOL_CALL = "after_tool_call"
    ON_ERROR = "on_error"


@dataclass
class MiddlewareContext:
    """中间件上下文 — 在中间件间传递状态."""

    request: Any = None
    response: Any = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)

    @property
    def elapsed_ms(self) -> float:
        return (time.time() - self.start_time) * 1000


@dataclass
class MiddlewareResult:
    """中间件执行结果."""

    modified: bool = False
    blocked: bool = False
    block_reason: str = ""
    skip_remaining: bool = False


class BaseMiddleware(ABC):
    """中间件抽象基类.

    子类需要实现感兴趣的生命周期方法。
    未实现的方法默认为空操作（pass-through）。
    """

    name: str = "base_middleware"
    order: int = 100
    enabled: bool = True

    async def before_request(self, ctx: MiddlewareContext) -> MiddlewareResult:
        return MiddlewareResult()

    async def after_request(self, ctx: MiddlewareContext) -> MiddlewareResult:
        return MiddlewareResult()

    async def before_tool_call(
        self, ctx: MiddlewareContext, tool_name: str, tool_input: dict
    ) -> MiddlewareResult:
        return MiddlewareResult()

    async def after_tool_call(
        self, ctx: MiddlewareContext, tool_name: str, tool_output: Any
    ) -> MiddlewareResult:
        return MiddlewareResult()

    async def on_error(self, ctx: MiddlewareContext, error: Exception) -> MiddlewareResult:
        return MiddlewareResult()


class MiddlewarePipeline:
    """有序中间件管道.

    用法:
        pipeline = MiddlewarePipeline()
        pipeline.add(AuthMiddleware())
        pipeline.add(AuditMiddleware())
        pipeline.add(ValidationMiddleware())

        # 执行请求前管道
        ctx = MiddlewareContext(request=request)
        result = await pipeline.execute_phase(MiddlewarePhase.BEFORE_REQUEST, ctx)
        if result.blocked:
            return error_response(result.block_reason)

        # ... 业务逻辑 ...

        # 执行请求后管道
        await pipeline.execute_phase(MiddlewarePhase.AFTER_REQUEST, ctx)
    """

    def __init__(self):
        self._middlewares: List[BaseMiddleware] = []

    def add(self, middleware: BaseMiddleware) -> "MiddlewarePipeline":
        if not middleware.enabled:
            logger.debug("跳过禁用的中间件: %s", middleware.name)
            return self

        self._middlewares.append(middleware)
        self._middlewares.sort(key=lambda m: m.order)
        logger.info("添加中间件: %s (order=%d)", middleware.name, middleware.order)
        return self

    def remove(self, name: str) -> bool:
        for i, m in enumerate(self._middlewares):
            if m.name == name:
                del self._middlewares[i]
                logger.info("移除中间件: %s", name)
                return True
        return False

    @property
    def middlewares(self) -> List[BaseMiddleware]:
        return list(self._middlewares)

    async def execute_phase(
        self,
        phase: MiddlewarePhase,
        ctx: MiddlewareContext,
        **kwargs,
    ) -> MiddlewareResult:
        """按顺序执行指定阶段的所有中间件."""
        phase_method_map = {
            MiddlewarePhase.BEFORE_REQUEST: "before_request",
            MiddlewarePhase.AFTER_REQUEST: "after_request",
            MiddlewarePhase.BEFORE_TOOL_CALL: "before_tool_call",
            MiddlewarePhase.AFTER_TOOL_CALL: "after_tool_call",
            MiddlewarePhase.ON_ERROR: "on_error",
        }

        method_name = phase_method_map.get(phase)
        if not method_name:
            logger.warning("未知阶段: %s", phase)
            return MiddlewareResult()

        for mw in self._middlewares:
            try:
                method = getattr(mw, method_name, None)
                if method is None:
                    continue

                if phase in (
                    MiddlewarePhase.BEFORE_TOOL_CALL,
                    MiddlewarePhase.AFTER_TOOL_CALL,
                ):
                    result = await method(ctx, **kwargs)
                elif phase == MiddlewarePhase.ON_ERROR:
                    result = await method(ctx, ctx.error)
                else:
                    result = await method(ctx)

                if result.blocked:
                    logger.info(
                        "%s 在 %s 阶段阻止了请求: %s",
                        mw.name,
                        phase.value,
                        result.block_reason,
                    )
                    return result

                if result.skip_remaining:
                    logger.debug("%s 跳过剩余中间件", mw.name)
                    break

            except Exception as e:
                logger.exception("中间件 %s 异常 (%s): %s", mw.name, phase.value, e)

                if phase != MiddlewarePhase.ON_ERROR:
                    error_result = await self._handle_error(ctx, e)
                    if error_result.blocked:
                        return error_result

        return MiddlewareResult()

    async def _handle_error(self, ctx: MiddlewareContext, error: Exception) -> MiddlewareResult:
        """错误处理：触发 ON_ERROR 阶段."""
        ctx.error = error
        return await self.execute_phase(MiddlewarePhase.ON_ERROR, ctx)

    def get_info(self) -> List[Dict[str, Any]]:
        """获取所有已注册中间件的信息."""
        return [
            {
                'name': mw.name,
                'order': mw.order,
                'enabled': mw.enabled,
                'class': type(mw).__name__,
            }
            for mw in self._middlewares
        ]


# ============================================================
# 内置中间件实现
# ============================================================

class AuthMiddleware(BaseMiddleware):
    """认证中间件 — 验证 JWT Token."""

    name = "auth"
    order = 10

    async def before_request(self, ctx: MiddlewareContext) -> MiddlewareResult:
        from flask import g, request as flask_request
        from app.core.security import verify_token

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


class AuditMiddleware(BaseMiddleware):
    """审计中间件 — 记录 API 调用到日志."""

    name = "audit"
    order = 90

    async def after_request(self, ctx: MiddlewareContext) -> MiddlewareResult:
        logger.info(
            "API调用: user=%s path=%s status=%d elapsed=%.1fms",
            ctx.metadata.get("user_id", "?"),
            getattr(getattr(ctx.request, 'path', None), '__str__', lambda: '?')(),
            getattr(ctx.response, 'status_code', 0) if ctx.response else 0,
            ctx.elapsed_ms,
        )
        return MiddlewareResult(modified=True)


class ValidationMiddleware(BaseMiddleware):
    """验证中间件 — 检查请求参数基本合法性."""

    name = "validation"
    order = 20

    async def before_request(self, ctx: MiddlewareContext) -> MiddlewareResult:
        from flask import request as flask_request

        content_length = flask_request.content_length or 0
        max_size = 10 * 1024 * 1024

        if content_length > max_size:
            return MiddlewareResult(
                blocked=True,
                block_reason=f"Request body too large ({content_length} > {max_size})",
            )

        return MiddlewareResult()


class RateLimitMiddleware(BaseMiddleware):
    """限流中间件 — 简单的内存限流（生产环境应使用 Redis）."""

    name = "rate_limit"
    order = 15

    def __init__(self, max_requests: int = 100, window_seconds: int = 60, max_keys: int = 10000):
        super().__init__()
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._requests: Dict[str, list] = {}

    async def before_request(self, ctx: MiddlewareContext) -> MiddlewareResult:
        from flask import request as flask_request

        key = ctx.metadata.get("user_id") or flask_request.remote_addr
        now = time.time()

        if key not in self._requests:
            self._requests[key] = []

        self._requests[key] = [t for t in self._requests[key] if now - t < self.window_seconds]

        while len(self._requests) > self.max_keys:
            oldest_key = next(iter(self._requests))
            del self._requests[oldest_key]

        if len(self._requests[key]) >= self.max_requests:
            return MiddlewareResult(
                blocked=True,
                block_reason=f"Rate limit exceeded ({self.max_requests}/{self.window_seconds}s)",
            )

        self._requests[key].append(now)
        return MiddlewareResult()


def create_default_pipeline() -> MiddlewarePipeline:
    """创建默认中间件管道（含内置中间件）."""
    pipeline = MiddlewarePipeline()
    pipeline.add(AuthMiddleware())
    pipeline.add(RateLimitMiddleware(max_requests=100, window_seconds=60))
    pipeline.add(ValidationMiddleware())
    pipeline.add(AuditMiddleware())
    return pipeline
