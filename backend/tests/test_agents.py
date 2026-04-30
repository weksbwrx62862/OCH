"""Agent API 单元测试 — 验证 CRUD 操作和权限控制."""

from __future__ import annotations

import json


class TestAgentListAPI:
    """测试 Agent 列表 API."""

    def test_list_agents_empty(self, test_client, auth_headers):
        """测试空列表返回."""
        response = test_client.get('/api/v1/agents', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'data' in data
        assert 'total' in data
        assert data['total'] == 0
        assert len(data['data']) == 0

    def test_list_agents_with_data(self, test_client, auth_headers, sample_agent):
        """测试有数据时的列表."""
        response = test_client.get('/api/v1/agents', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data['total'] >= 1

        agent_names = [a['name'] for a in data['data']]
        assert sample_agent.name in agent_names

    def test_list_agents_pagination(self, test_client, auth_headers):
        """测试分页功能."""
        response = test_client.get(
            '/api/v1/agents',
            headers=auth_headers,
            query_string={'page': 1, 'per_page': 10}
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'page' in data
        assert 'per_page' in data
        assert 'total_pages' in data

    def test_list_agents_requires_auth(self, test_client):
        """测试未认证访问被拒绝."""
        response = test_client.get('/api/v1/agents')
        assert response.status_code == 401


class TestAgentCreateAPI:
    """测试 Agent 创建 API."""

    def test_create_agent_success(self, test_client, auth_headers):
        """测试成功创建 Agent."""
        payload = {
            'name': 'New Test Agent',
            'description': '新创建的测试智能体',
            'system_prompt': '你是新助手',
            'model': 'claude-sonnet-4-20250514',
        }

        response = test_client.post(
            '/api/v1/agents',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert 'agent' in data
        assert data['agent']['name'] == 'New Test Agent'

    def test_create_agent_missing_name(self, test_client, auth_headers):
        """测试缺少名称字段."""
        payload = {'description': 'No name provided'}

        response = test_client.post(
            '/api/v1/agents',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 422  # ValidationError → 422

    def test_create_agent_duplicate_name(self, test_client, auth_headers, sample_agent):
        """测试重名检测."""
        payload = {'name': sample_agent.name}

        response = test_client.post(
            '/api/v1/agents',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 422  # ValidationError - duplicate

    def test_create_agent_requires_admin(self, test_client, user_auth_headers):
        """测试普通用户无法创建 Agent."""
        payload = {'name': 'Should Fail'}

        response = test_client.post(
            '/api/v1/agents',
            headers=user_auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 403  # Forbidden


class TestAgentGetAPI:
    """测试 Agent 获取详情 API."""

    def test_get_agent_success(self, test_client, auth_headers, sample_agent):
        """测试获取 Agent 详情."""
        response = test_client.get(
            f'/api/v1/agents/{sample_agent.id}',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['id'] == sample_agent.id
        assert data['name'] == sample_agent.name

    def test_get_agent_not_found(self, test_client, auth_headers):
        """测试获取不存在的 Agent."""
        fake_id = 'non-existent-id-12345'
        response = test_client.get(f'/api/v1/agents/{fake_id}', headers=auth_headers)
        assert response.status_code == 404  # NotFoundError


class TestAgentUpdateAPI:
    """测试 Agent 更新 API."""

    def test_update_agent_success(self, test_client, auth_headers, sample_agent):
        """测试成功更新 Agent."""
        payload = {'description': 'Updated description'}

        response = test_client.put(
            f'/api/v1/agents/{sample_agent.id}',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['agent']['description'] == 'Updated description'
        assert 'updated_fields' in data

    def test_update_agent_not_found(self, test_client, auth_headers):
        """测试更新不存在的 Agent."""
        payload = {'name': 'Ghost'}
        response = test_client.put(
            '/api/v1/agents/nonexistent',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 404


class TestAgentDeleteAPI:
    """测试 Agent 删除 API."""

    def test_delete_agent_success(self, test_client, auth_headers, sample_agent):
        """测试成功删除 Agent."""
        response = test_client.delete(
            f'/api/v1/agents/{sample_agent.id}',
            headers=auth_headers,
        )
        assert response.status_code == 200

        # 验证已删除
        get_resp = test_client.get(
            f'/api/v1/agents/{sample_agent.id}',
            headers=auth_headers,
        )
        assert get_resp.status_code == 404

    def test_delete_agent_not_found(self, test_client, auth_headers):
        """测试删除不存在的 Agent."""
        response = test_client.delete(
            '/api/v1/agents/ghost-id',
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestAgentStatsAPI:
    """测试 Agent 统计 API."""

    def test_get_stats(self, test_client, auth_headers, sample_agent):
        """测试获取统计数据."""
        response = test_client.get(
            f'/api/v1/agents/{sample_agent.id}/stats',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'agent_id' in data
        assert 'total_sessions' in data
        assert 'total_messages' in data
        assert isinstance(data['total_sessions'], int)


class TestAgentPermissionsAPI:
    """测试 Agent 权限 API."""

    def test_get_permissions(self, test_client, auth_headers, sample_agent):
        """测试获取权限配置."""
        response = test_client.get(
            f'/api/v1/agents/{sample_agent.id}/permissions',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'tool_permissions' in data
        assert 'mode' in data

    def test_update_permissions(self, test_client, auth_headers, sample_agent):
        """测试更新权限配置."""
        payload = {
            'mode': 'strict',
            'tool_permissions': [
                {
                    'tool_name': 'Bash',
                    'permission': 'deny',
                    'denied_commands': ['rm -rf', 'sudo'],
                },
            ],
        }

        response = test_client.put(
            f'/api/v1/agents/{sample_agent.id}/permissions',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 200
