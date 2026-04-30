"""审计日志 API 单元测试 — 验证日志查询、时间筛选、分页和权限控制."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta


class TestAuditLogListAPI:
    """测试审计日志列表 API."""

    def test_list_logs_empty(self, test_client, auth_headers):
        """测试空列表返回."""
        response = test_client.get('/api/v1/audit', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'data' in data
        assert 'total' in data
        assert data['total'] == 0
        assert len(data['data']) == 0

    def test_list_logs_with_data(self, test_client, auth_headers, db_session):
        """测试有数据时的列表."""
        from app.models.permission import AuditLog
        import uuid

        log = AuditLog(
            id=str(uuid.uuid4()),
            user_id='test-user-001',
            action='session_create',
            resource_type='Session',
            resource_id='sess-001',
            details={'title': 'Test Session'},
        )
        db_session.add(log)
        import asyncio
        asyncio.get_event_loop().run_until_complete(db_session.commit())

        response = test_client.get('/api/v1/audit', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data['total'] >= 1

    def test_list_logs_pagination(self, test_client, auth_headers):
        """测试分页功能."""
        response = test_client.get(
            '/api/v1/audit',
            headers=auth_headers,
            query_string={'page': 1, 'per_page': 10}
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'page' in data
        assert 'per_page' in data
        assert data['page'] == 1
        assert data['per_page'] == 10

    def test_list_logs_action_filter(self, test_client, auth_headers, db_session):
        """测试操作类型筛选."""
        from app.models.permission import AuditLog
        import uuid
        import asyncio

        log = AuditLog(
            id=str(uuid.uuid4()),
            user_id='test-user-001',
            action='tool_use',
            resource_type='Tool',
            details={'tool_name': 'Bash'},
        )
        db_session.add(log)
        asyncio.get_event_loop().run_until_complete(db_session.commit())

        response = test_client.get(
            '/api/v1/audit',
            headers=auth_headers,
            query_string={'action': 'tool_use'}
        )
        assert response.status_code == 200

        data = response.get_json()
        for item in data['data']:
            assert item['action'] == 'tool_use'

    def test_list_logs_date_range_filter(self, test_client, auth_headers, db_session):
        """测试时间范围筛选."""
        from app.models.permission import AuditLog
        import uuid
        import asyncio

        now = datetime.now(timezone.utc)
        log = AuditLog(
            id=str(uuid.uuid4()),
            user_id='test-user-001',
            action='auth_fail',
            resource_type='Auth',
            details={'reason': 'invalid_token'},
            created_at=now,
        )
        db_session.add(log)
        asyncio.get_event_loop().run_until_complete(db_session.commit())

        from_date = (now - timedelta(hours=1)).isoformat()
        to_date = (now + timedelta(hours=1)).isoformat()

        response = test_client.get(
            '/api/v1/audit',
            headers=auth_headers,
            query_string={'from_date': from_date, 'to_date': to_date}
        )
        assert response.status_code == 200

    def test_list_logs_requires_auth(self, test_client):
        """测试未认证访问被拒绝."""
        response = test_client.get('/api/v1/audit')
        assert response.status_code == 401


class TestAuditLogDetailAPI:
    """测试单条日志详情 API."""

    def test_get_log_success(self, test_client, auth_headers, db_session):
        """测试获取日志详情."""
        from app.models.permission import AuditLog
        import uuid
        import asyncio

        log = AuditLog(
            id=str(uuid.uuid4()),
            user_id='test-user-001',
            action='agent_update',
            resource_type='Agent',
            details={'field': 'description'},
        )
        db_session.add(log)
        asyncio.get_event_loop().run_until_complete(db_session.commit())
        asyncio.get_event_loop().run_until_complete(db_session.refresh(log))

        response = test_client.get(
            f'/api/v1/audit/{log.id}',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['id'] == log.id
        assert data['action'] == 'agent_update'

    def test_get_log_not_found(self, test_client, auth_headers):
        """测试获取不存在的日志."""
        fake_id = 'non-existent-log-id-12345'
        response = test_client.get(f'/api/v1/audit/{fake_id}', headers=auth_headers)
        assert response.status_code == 404


class TestAuditStatsAPI:
    """测试审计统计 API."""

    def test_get_stats(self, test_client, auth_headers):
        """测试获取统计数据."""
        response = test_client.get(
            '/api/v1/audit/stats',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'total' in data
        assert 'by_action' in data
        assert 'recent' in data
        assert isinstance(data['by_action'], dict)


class TestAuditExportAPI:
    """测试审计导出 API."""

    def test_export_json_format(self, test_client, auth_headers):
        """测试 JSON 格式导出."""
        response = test_client.get(
            '/api/v1/audit/export',
            headers=auth_headers,
            query_string={'format': 'json'}
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'logs' in data
        assert 'total' in data

    def test_export_csv_format(self, test_client, auth_headers):
        """测试 CSV 格式导出."""
        response = test_client.get(
            '/api/v1/audit/export',
            headers=auth_headers,
            query_string={'format': 'csv'}
        )
        assert response.status_code == 200
        assert 'text/csv' in response.content_type


class TestAuditPurgeAPI:
    """测试日志清理 API."""

    def test_purge_requires_admin(self, test_client, user_auth_headers):
        """测试普通用户无法清理日志."""
        response = test_client.post(
            '/api/v1/audit/purge',
            headers=user_auth_headers,
        )
        assert response.status_code == 403
