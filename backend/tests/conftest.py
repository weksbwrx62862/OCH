"""Pytest 配置和共享 Fixtures — OpenClaw-Harness 测试套件."""

from __future__ import annotations

import asyncio
import os
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker,
    create_async_engine,
)



# ============================================================
# 关键: 在导入 app 模块之前设置测试环境变量
# ============================================================

os.environ.setdefault('TESTING', 'true')
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///:memory:')
os.environ.setdefault('DEBUG', 'true')


# ============================================================
# 延迟导入 (确保环境变量已设置)
# ============================================================

from app.main import create_app
from app.core.database import Base

# 确保所有模型都被导入并注册到 Base.metadata
import app.models  # noqa: F401

_test_engine = None
_test_session_factory = None
_test_loop = None
_agent_counter = 0


@pytest.fixture(scope='session')
def event_loop():
    """创建事件循环."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def app():
    """创建 Flask 应用实例 + 初始化测试数据库."""
    global _test_engine, _test_session_factory, _test_loop

    # 创建专用事件循环（避免 DeprecationWarning）
    _test_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_test_loop)

    try:
        application = create_app()
        application.config['TESTING'] = True

        # 创建专用测试引擎
        _test_engine = create_async_engine(
            'sqlite+aiosqlite:///:memory:',
            echo=False,
        )
        _test_session_factory = async_sessionmaker(
            _test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # 使用 set_test_session_factory 注入测试会话工厂
        import app.core.async_utils as _async_utils_mod
        _async_utils_mod.set_test_session_factory(_test_session_factory)

        # 同时替换 database 模块的工厂（兼容旧引用）
        import app.core.database as _db_module
        _db_module.async_session_factory = _test_session_factory

        # 同步建表（使用专用事件循环避免 DeprecationWarning）
        _test_loop.run_until_complete(_create_tables(_test_engine))

        yield application

    finally:
        # 清理（使用同一个专用事件循环）
        try:
            _test_loop.run_until_complete(_drop_tables(_test_engine))
        except Exception:
            pass
        _test_loop.run_until_complete(_test_engine.dispose())
        _test_loop.close()
        _test_engine = None
        _test_loop = None


async def _create_tables(engine):
    """同步创建所有表."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _drop_tables(engine):
    """删除所有表."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope='session')
def test_client(app):
    """测试客户端."""
    return app.test_client()


@pytest_asyncio.fixture(scope='function')
async def db_session():
    """数据库会话 (每次测试独立)."""
    if _test_session_factory is None:
        raise RuntimeError("Test DB not initialized")
    async with _test_session_factory() as session:
        yield session
        await session.rollback()


# ============================================================
# 认证 Fixtures
# ============================================================

@pytest.fixture
def auth_headers():
    """管理员认证头."""
    from app.core.security import create_jwt
    token = create_jwt({
        'user_id': 'test-user-001',
        'username': 'testuser',
        'role': 'admin',
    })
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }


@pytest.fixture
def user_auth_headers():
    """普通用户认证头."""
    from app.core.security import create_jwt
    token = create_jwt({
        'user_id': 'test-user-002',
        'username': 'normaluser',
        'role': 'user',
    })
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }


# ============================================================
# 数据 Fixtures
# ============================================================

@pytest_asyncio.fixture
async def sample_agent(db_session):
    """测试 Agent (每次使用唯一名称避免 UNIQUE 冲突)."""
    from app.models.agent import Agent
    import uuid
    global _agent_counter
    _agent_counter += 1
    agent = Agent(
        id=str(uuid.uuid4()),
        name=f'Test-Agent-{_agent_counter:03d}',
        description='测试用智能体',
        system_prompt='你是一个测试助手',
        model='claude-sonnet-4-20250514',
        max_turns=8,
        max_tokens=4096,
        is_active=True,
    )
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    return agent


@pytest_asyncio.fixture
async def sample_session(db_session, sample_agent):
    """测试 Session."""
    from app.models.session import Session
    import uuid
    s = Session(
        id=str(uuid.uuid4()),
        agent_id=sample_agent.id,
        status='active',
        title='Test Chat Session',
    )
    db_session.add(s)
    await db_session.commit()
    await db_session.refresh(s)
    return s


@pytest_asyncio.fixture
async def sample_messages(db_session, sample_session):
    """测试消息."""
    from app.models.message import Message
    import uuid
    msgs = [
        Message(id=str(uuid.uuid4()), session_id=sample_session.id, role='user',
                content='Hello test', tokens_input=10),
        Message(id=str(uuid.uuid4()), session_id=sample_session.id, role='assistant',
                content='Hi!', tokens_output=15),
    ]
    for m in msgs:
        db_session.add(m)
    await db_session.commit()
    return msgs


@pytest_asyncio.fixture
async def sample_task(db_session, sample_agent, sample_session):
    """测试用 Task 对象 — 创建后台任务用于测试任务管理功能."""
    from app.models.task import Task
    import uuid
    task = Task(
        id=str(uuid.uuid4()),
        session_id=sample_session.id if sample_session else None,
        task_type='command',
        command='echo "test"',
        status='pending',
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


@pytest_asyncio.fixture
async def sample_skill(db_session):
    """测试用 Skill 对象 — 创建知识库技能用于测试技能管理功能."""
    from app.models.skill import Skill
    import uuid
    skill = Skill(
        id=str(uuid.uuid4()),
        name=f'test-skill-{uuid.uuid4().hex[:8]}',
        description='测试用技能',
        category='test',
        version='1.0.0',
        source='builtin',
        enabled=True,
        content_md='# 测试技能\n\n这是一个测试用的 Markdown 技能文件。',
    )
    db_session.add(skill)
    await db_session.commit()
    await db_session.refresh(skill)
    return skill


@pytest_asyncio.fixture
async def sample_tool(db_session, sample_agent):
    """测试用 ToolPermission 对象 — 创建工具权限配置（关联到 sample_agent）."""
    from app.models.agent import ToolPermission
    import uuid
    tool_perm = ToolPermission(
        id=str(uuid.uuid4()),
        agent_id=sample_agent.id,
        tool_name='bash',
        permission='ask',
        path_rules=[{'pattern': '/tmp/**', 'allow': True}],
        approved_commands=['ls', 'cat'],
        denied_commands=['rm -rf /'],
    )
    db_session.add(tool_perm)
    await db_session.commit()
    await db_session.refresh(tool_perm)
    return tool_perm


@pytest_asyncio.fixture
async def sample_permission(db_session):
    """测试用 PermissionRule 对象 — 创建全局路径权限规则."""
    from app.models.permission import PermissionRule
    import uuid
    perm_rule = PermissionRule(
        id=str(uuid.uuid4()),
        name=f'test-rule-{uuid.uuid4().hex[:8]}',
        pattern='/safe/path/**',
        allow=True,
        description='测试用权限规则 — 允许访问安全路径',
        priority=10,
        created_by='test-user',
    )
    db_session.add(perm_rule)
    await db_session.commit()
    await db_session.refresh(perm_rule)
    return perm_rule


# ============================================================
# Mock & 辅助
# ============================================================

@pytest.fixture
def mock_openharness_engine():
    e = AsyncMock()
    e.submit_message = AsyncMock(return_value=iter([]))
    return e


@pytest.fixture
def mock_tool_registry():
    r = MagicMock()
    r.get_tool = MagicMock(return_value=MagicMock())
    r.list_tools = MagicMock(return_value=[])
    return r


def assert_json_response(response, expected_status: int = 200):
    assert response.status_code == expected_status, \
        f"Expected {expected_status}, got {response.status_code}: {response.data}"
    data = response.get_json()
    assert data is not None
    return data


def assert_error_response(response, expected_status: int, expected_error: str = None):
    """验证错误响应格式和内容."""
    assert response.status_code == expected_status
    data = response.get_json()
    assert 'error' in data or 'message' in data
    if expected_error:
        err = data.get('error', data.get('message', ''))
        assert expected_error.lower() in err.lower()
    return data


def assert_pagination_response(response, expected_status: int = 200):
    """验证分页响应格式 — 确保包含 items, total, page, page_size 等标准字段.

    Args:
        response: Flask 测试响应对象
        expected_status: 预期的 HTTP 状态码（默认 200）

    Returns:
        dict: 解析后的 JSON 响应数据

    Raises:
        AssertionError: 如果响应格式不符合分页规范
    """
    assert response.status_code == expected_status, \
        f"Expected {expected_status}, got {response.status_code}: {response.data}"
    data = response.get_json()
    assert data is not None, "Response JSON is None"
    assert 'items' in data, "Pagination response missing 'items' field"
    assert 'total' in data, "Pagination response missing 'total' field"
    assert 'page' in data, "Pagination response missing 'page' field"
    assert 'page_size' in data, "Pagination response missing 'page_size' field"
    assert isinstance(data['items'], list), "'items' should be a list"
    assert isinstance(data['total'], int), "'total' should be an integer"
    assert isinstance(data['page'], int), "'page' should be an integer"
    assert isinstance(data['page_size'], int), "'page_size' should be an integer"
    assert data['total'] >= 0, "'total' should be non-negative"
    assert data['page'] >= 1, "'page' should be >= 1"
    assert data['page_size'] > 0, "'page_size' should be > 0"
    return data
