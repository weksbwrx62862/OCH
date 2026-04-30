"""Session Service 单元测试 — 验证会话管理核心业务逻辑.

改造说明：原使用 sys.modules mock 导致 pytest-cov 无法追踪模块覆盖率。
现改为 @patch 方式按需 mock 外部依赖，保持模块路径可见。
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

# 正常导入被测模块 — pytest-cov 可追踪此路径
from app.services.session_service import SessionService
from app.services.hook_service import trigger_hook
from app.core.exceptions import NotFoundError


class TestCreateSession:
    """测试创建会话功能."""

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_create_session_success(self, mock_executor, app, db_session, sample_agent):
        """成功创建会话."""
        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)
        session = await service.create_session(agent_id=sample_agent.id)

        assert session.id is not None
        assert session.agent_id == sample_agent.id
        assert session.status == 'active'
        assert session.title is not None
        assert session.total_messages == 0

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_create_session_with_custom_title(self, mock_executor, app, db_session, sample_agent):
        """创建带自定义标题的会话."""
        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)
        session = await service.create_session(
            agent_id=sample_agent.id,
            title='我的自定义会话'
        )

        assert session.title == '我的自定义会话'

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_create_session_with_metadata(self, mock_executor, app, db_session, sample_agent):
        """创建带元数据的会话."""
        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)
        metadata = {'source': 'test', 'version': '1.0'}
        session = await service.create_session(
            agent_id=sample_agent.id,
            metadata_=metadata
        )

        assert session.metadata_ == metadata

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_create_session_nonexistent_agent(self, mock_executor, app, db_session):
        """使用不存在的 Agent ID 创建会话应抛出 NotFoundError."""
        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)

        with pytest.raises(NotFoundError) as exc_info:
            await service.create_session(agent_id='nonexistent-agent-id')

        assert 'Agent' in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_create_session_generates_unique_ids(self, mock_executor, app, db_session, sample_agent):
        """多次创建会话应生成不同的 UUID."""
        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)

        session1 = await service.create_session(agent_id=sample_agent.id)
        session2 = await service.create_session(agent_id=sample_agent.id)

        assert session1.id != session2.id


class TestGetSession:
    """测试获取会话详情功能."""

    @pytest.mark.asyncio
    async def test_get_session_exists(self, app, db_session, sample_session):
        """获取存在的会话."""
        service = SessionService(db_session)
        session = await service.get_session(sample_session.id)

        assert session.id == sample_session.id
        assert session.status == sample_session.status

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, app, db_session):
        """获取不存在的会话应抛出 NotFoundError."""
        service = SessionService(db_session)

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_session('nonexistent-session-id')

        assert 'Session' in str(exc_info.value)


class TestUpdateSession:
    """测试更新会话功能."""

    @pytest.mark.asyncio
    async def test_update_session_title(self, app, db_session, sample_session):
        """更新会话标题."""
        service = SessionService(db_session)
        updated = await service.update_session(
            sample_session.id,
            title='更新后的标题'
        )

        assert updated.title == '更新后的标题'

    @pytest.mark.asyncio
    async def test_update_session_status(self, app, db_session, sample_session):
        """更新会话状态."""
        service = SessionService(db_session)
        updated = await service.update_session(
            sample_session.id,
            status='paused'
        )

        assert updated.status == 'paused'

    @pytest.mark.asyncio
    async def test_update_nonexistent_session(self, app, db_session):
        """更新不存在的会话应抛出 NotFoundError."""
        service = SessionService(db_session)

        with pytest.raises(NotFoundError):
            await service.update_session(
                'nonexistent-id',
                title='test'
            )


class TestDeleteSession:
    """测试删除会话功能."""

    @pytest.mark.asyncio
    async def test_delete_session_success(self, app, db_session, sample_session):
        """成功删除会话."""
        service = SessionService(db_session)
        session_id = sample_session.id

        await service.delete_session(session_id)

        with pytest.raises(NotFoundError):
            await service.get_session(session_id)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, app, db_session):
        """删除不存在的会话应抛出 NotFoundError."""
        service = SessionService(db_session)

        with pytest.raises(NotFoundError):
            await service.delete_session('nonexistent-id')


class TestListSessions:
    """测试列表查询功能（支持分页、筛选）."""

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_list_sessions_returns_list(self, mock_executor, app, db_session):
        """列表查询应返回列表和总数."""
        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)
        sessions, total = await service.list_sessions()

        assert isinstance(sessions, list)
        assert isinstance(total, int)
        assert total >= 0

    @pytest.mark.asyncio
    async def test_list_sessions_with_data(self, app, db_session, sample_session):
        """有数据时返回列表."""
        service = SessionService(db_session)
        sessions, total = await service.list_sessions()

        assert len(sessions) >= 1
        assert total >= 1
        assert any(s.id == sample_session.id for s in sessions)

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_list_sessions_pagination(self, mock_executor, app, db_session, sample_agent):
        """分页参数正确工作."""
        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)

        for i in range(5):
            await service.create_session(agent_id=sample_agent.id)

        page1, total = await service.list_sessions(page=1, per_page=2)
        assert len(page1) <= 2
        assert total >= 5

        page2, _ = await service.list_sessions(page=2, per_page=2)
        assert len(page2) <= 2

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_list_sessions_filter_by_status(self, mock_executor, app, db_session, sample_agent):
        """按状态筛选会话."""
        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)

        await service.create_session(agent_id=sample_agent.id)
        paused_session = await service.create_session(agent_id=sample_agent.id)
        await service.update_session(paused_session.id, status='paused')

        active_sessions, _ = await service.list_sessions(status='active')
        assert all(s.status == 'active' for s in active_sessions)

        paused_sessions, _ = await service.list_sessions(status='paused')
        assert all(s.status == 'paused' for s in paused_sessions)

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_list_sessions_filter_by_agent(self, mock_executor, app, db_session, sample_agent):
        """按 Agent ID 筛选会话."""
        from app.models.agent import Agent

        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)

        await service.create_session(agent_id=sample_agent.id)

        other_agent = Agent(
            id=str(uuid.uuid4()),
            name=f'Other-Agent-{uuid.uuid4().hex[:8]}',
            description='其他智能体',
        )
        db_session.add(other_agent)
        await db_session.commit()
        await service.create_session(agent_id=other_agent.id)

        filtered, total = await service.list_sessions(agent_id=sample_agent.id)
        assert all(s.agent_id == sample_agent.id for s in filtered)


class TestAddMessage:
    """测试添加消息功能."""

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_add_user_message(self, mock_executor, app, db_session, sample_session):
        """添加用户消息."""
        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)
        message = await service.add_message(
            session_id=sample_session.id,
            role='user',
            content='你好，这是一个测试消息'
        )

        assert message.id is not None
        assert message.role == 'user'
        assert message.content == '你好，这是一个测试消息'
        assert message.session_id == sample_session.id

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_add_assistant_message(self, mock_executor, app, db_session, sample_session):
        """添加助手回复消息."""
        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)
        message = await service.add_message(
            session_id=sample_session.id,
            role='assistant',
            content='你好！我是 AI 助手。'
        )

        assert message.role == 'assistant'
        assert message.content == '你好！我是 AI 助手。'

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_add_message_updates_session_stats(self, mock_executor, app, db_session, sample_session):
        """添加消息后应更新会话的消息计数."""
        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)

        initial_count = sample_session.total_messages

        await service.add_message(
            session_id=sample_session.id,
            role='user',
            content='测试统计更新'
        )

        updated_session = await service.get_session(sample_session.id)
        assert updated_session.total_messages == initial_count + 1

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_add_message_with_tokens(self, mock_executor, app, db_session, sample_session):
        """添加带 token 统计的消息."""
        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)
        message = await service.add_message(
            session_id=sample_session.id,
            role='user',
            content='测试 token',
            tokens_input=10,
            tokens_output=5
        )

        assert message.tokens_input == 10
        assert message.tokens_output == 5


class TestGetMessages:
    """测试获取消息列表功能."""

    @pytest.mark.asyncio
    async def test_get_messages_empty(self, app, db_session, sample_session):
        """无消息的会话返回空列表."""
        service = SessionService(db_session)
        messages, total = await service.get_messages(sample_session.id)

        assert messages == []
        assert total == 0

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_get_messages_with_data(self, mock_executor, app, db_session, sample_session):
        """有消息时返回消息列表."""
        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)

        await service.add_message(session_id=sample_session.id, role='user', content='消息1')
        await service.add_message(session_id=sample_session.id, role='assistant', content='回复1')
        await service.add_message(session_id=sample_session.id, role='user', content='消息2')

        messages, total = await service.get_messages(sample_session.id)

        assert len(messages) == 3
        assert total == 3
        assert messages[0].created_at <= messages[1].created_at

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_get_messages_pagination(self, mock_executor, app, db_session, sample_session):
        """分页参数正确工作."""
        mock_executor.return_value = AsyncMock()
        service = SessionService(db_session)

        for i in range(10):
            await service.add_message(
                session_id=sample_session.id,
                role='user',
                content=f'消息 {i}'
            )

        page1, total = await service.get_messages(
            session_id=sample_session.id,
            page=1,
            per_page=3
        )
        assert len(page1) == 3
        assert total == 10

        page2, _ = await service.get_messages(
            session_id=sample_session.id,
            page=2,
            per_page=3
        )
        assert len(page2) == 3

    @pytest.mark.asyncio
    async def test_get_messages_nonexistent_session(self, app, db_session):
        """获取不存在会话的消息应抛出 NotFoundError."""
        service = SessionService(db_session)

        with pytest.raises(NotFoundError):
            await service.get_messages('nonexistent-id')


class TestPauseResumeCompleteSession:
    """测试会话状态转换功能."""

    @pytest.mark.asyncio
    async def test_pause_session(self, app, db_session, sample_session):
        """暂停会话."""
        service = SessionService(db_session)
        paused = await service.pause_session(sample_session.id)

        assert paused.status == 'paused'

    @pytest.mark.asyncio
    async def test_resume_session(self, app, db_session, sample_session):
        """恢复会话."""
        service = SessionService(db_session)

        await service.pause_session(sample_session.id)

        resumed = await service.resume_session(sample_session.id)

        assert resumed.status == 'active'

    @pytest.mark.asyncio
    async def test_complete_session(self, app, db_session, sample_session):
        """完成会话."""
        service = SessionService(db_session)
        completed = await service.complete_session(sample_session.id)

        assert completed.status == 'completed'
        assert completed.completed_at is not None


class TestTriggerHook:
    """测试 Hook 触发机制."""

    @pytest.mark.asyncio
    @patch('app.services.hook_service.get_hook_executor')
    async def test_trigger_hook_returns_result_structure(self, mock_executor):
        """触发 hook 应返回标准结果结构."""
        mock_hook_result = MagicMock()
        mock_hook_result.results = []
        mock_executor.return_value.execute = AsyncMock(return_value=mock_hook_result)

        result = await trigger_hook('test_event', {'key': 'value'})

        assert 'blocked' in result
        assert 'results_count' in result
        assert 'results' in result
        assert 'blocked_reason' in result
        assert result['blocked'] is False
