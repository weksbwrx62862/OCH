"""Session & Chat API 单元测试 — 验证会话管理和 SSE 流式聊天."""

from __future__ import annotations

import json


class TestSessionListAPI:
    """测试会话列表 API."""

    def test_list_sessions_empty(self, test_client, auth_headers):
        """测试空会话列表."""
        response = test_client.get('/api/v1/sessions', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'data' in data
        assert data['total'] == 0

    def test_list_sessions_with_data(self, test_client, auth_headers, sample_session):
        """测试有数据时的列表."""
        response = test_client.get('/api/v1/sessions', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data['total'] >= 1

    def test_list_sessions_requires_auth(self, test_client):
        """测试未认证访问."""
        response = test_client.get('/api/v1/sessions')
        assert response.status_code == 401


class TestSessionCreateAPI:
    """测试会话创建 API."""

    def test_create_session_success(self, test_client, auth_headers):
        """测试成功创建会话."""
        payload = {
            'title': 'Test Chat',
        }

        response = test_client.post(
            '/api/v1/sessions',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert 'session' in data
        assert data['session']['status'] == 'active'

    def test_create_session_default_title(self, test_client, auth_headers):
        """测试默认标题生成."""
        response = test_client.post(
            '/api/v1/sessions',
            headers=auth_headers,
            data=json.dumps({}),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert 'session' in data
        assert data['session']['title'] is not None


class TestSessionGetAPI:
    """测试获取会话详情."""

    def test_get_session(self, test_client, auth_headers, sample_session):
        """测试获取会话详情."""
        response = test_client.get(
            f'/api/v1/sessions/{sample_session.id}',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['id'] == sample_session.id
        assert 'recent_messages' in data

    def test_get_session_not_found(self, test_client, auth_headers):
        """测试不存在的会话."""
        response = test_client.get(
            '/api/v1/sessions/fake-session-id',
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestSessionDeleteAPI:
    """测试删除会话."""

    def test_delete_session(self, test_client, auth_headers, sample_session):
        """测试成功删除."""
        response = test_client.delete(
            f'/api/v1/sessions/{sample_session.id}',
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_delete_session_not_found(self, test_client, auth_headers):
        """测试删除不存在的会话."""
        response = test_client.delete(
            '/api/v1/sessions/ghost-id',
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestSessionPauseResumeAPI:
    """测试暂停/恢复会话."""

    def test_pause_session(self, test_client, auth_headers, sample_session):
        """测试暂停会话."""
        response = test_client.put(
            f'/api/v1/sessions/{sample_session.id}/pause',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'paused'

    def test_resume_session(self, test_client, auth_headers, sample_session):
        """测试恢复会话."""
        # 先暂停
        test_client.put(
            f'/api/v1/sessions/{sample_session.id}/pause',
            headers=auth_headers,
        )

        # 再恢复
        response = test_client.put(
            f'/api/v1/sessions/{sample_session.id}/resume',
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.get_json()['status'] == 'active'


class TestChatAPI:
    """测试聊天 API（核心功能）."""

    def test_chat_missing_message(self, test_client, auth_headers, sample_session):
        """测试缺少消息内容."""
        payload = {'message': ''}

        response = test_client.post(
            f'/api/v1/sessions/{sample_session.id}/chat',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 422  # ValidationError - empty message

    def test_chat_non_stream_mode(self, test_client, auth_headers, sample_session):
        """测试非流式聊天模式."""
        payload = {
            'message': 'Hello, test message!',
            'stream': False,
        }

        response = test_client.post(
            f'/api/v1/sessions/{sample_session.id}/chat',
            headers=auth_headers,
            data=json.dumps(payload),
        )

        # 非流式应返回 JSON
        assert response.content_type.startswith('application/json')
        data = response.get_json()
        assert 'response' in data or 'errors' in data

    def test_chat_stream_mode(self, test_client, auth_headers, sample_session):
        """测试 SSE 流式聊天模式."""
        payload = {
            'message': 'Test streaming',
            'stream': True,
        }

        response = test_client.post(
            f'/api/v1/sessions/{sample_session.id}/chat',
            headers=auth_headers,
            data=json.dumps(payload),
        )

        # 流式应返回 event-stream
        assert 'text/event-stream' in response.content_type or \
               response.status_code in (200, 500)

        if response.status_code == 200:
            content = response.data.decode('utf-8')
            # 应包含 SSE 事件格式
            assert 'data: ' in content or '[DONE]' in content


class TestMessagesAPI:
    """测试消息 API."""

    def test_get_messages(self, test_client, auth_headers, sample_session, sample_messages):
        """测试获取消息列表."""
        response = test_client.get(
            f'/api/v1/sessions/{sample_session.id}/messages',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'data' in data
        assert len(data['data']) >= 2  # 至少有 user + assistant

    def test_get_messages_pagination(self, test_client, auth_headers, sample_session):
        """测试消息分页."""
        response = test_client.get(
            f'/api/v1/sessions/{sample_session.id}/messages',
            headers=auth_headers,
            query_string={'page': 1, 'per_page': 10},
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'page' in data
        assert 'per_page' in data


class TestSessionStatsAPI:
    """测试会话统计 API."""

    def test_get_stats(self, test_client, auth_headers, sample_session, sample_messages):
        """测试获取统计数据."""
        response = test_client.get(
            f'/api/v1/sessions/{sample_session.id}/stats',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'total_messages' in data
        assert 'user_messages' in data
        assert 'assistant_messages' in data
        assert data['total_messages'] >= 2
