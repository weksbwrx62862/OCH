"""统一异步工具 — 消除各 API 模块中 _run_async / _get_db 的重复定义.

核心修复：Flask 同步视图函数调用 async 代码时，asyncpg 连接池
绑定在模块级事件循环上，而 run_async 在新线程中创建新事件循环，
导致 "Future attached to a different loop" 错误。

解决方案：复用 database.py 的模块级单例引擎和会话工厂，
避免每次调用创建新引擎导致连接池泄漏。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_test_session_factory = None


def set_test_session_factory(factory):
    global _test_session_factory
    _test_session_factory = factory


def run_async(coro: Any) -> Any:
    return asyncio.run(coro)


async def get_db() -> AsyncSession:
    if _test_session_factory is not None:
        session = _test_session_factory()
        return session
    from app.core.database import async_session_factory
    session = async_session_factory()
    return session


async def dispose_engine():
    from app.core.database import engine
    await engine.dispose()
