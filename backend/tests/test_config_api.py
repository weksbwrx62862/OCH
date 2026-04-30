"""配置管理 API 单元测试 — 验证配置读取、更新权限和敏感信息脱敏."""

from __future__ import annotations

import json


class TestConfigGetAPI:
    """测试配置读取 API."""

    def test_get_config_public(self, test_client, auth_headers):
        """测试获取公开配置."""
        response = test_client.get('/api/v1/config', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'app' in data
        assert 'database' in data
        assert 'openharness' in data
        assert 'security' in data

        # 验证基本字段存在
        assert 'name' in data['app']
        assert 'env' in data['app']
        assert 'debug' in data['app']

    def test_get_config_no_secrets_exposed(self, test_client, auth_headers):
        """测试敏感信息不被暴露."""
        response = test_client.get('/api/v1/config', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        response_str = json.dumps(data)

        # 验证敏感信息不在响应中
        assert 'SECRET_KEY' not in response_str or 'change-me' in response_str
        assert 'JWT_SECRET' not in response_str

    def test_get_config_database_masked(self, test_client, auth_headers):
        """测试数据库 URL 脱敏处理."""
        response = test_client.get('/api/v1/config', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        db_url = data.get('database', {}).get('url', '')

        # 数据库 URL 应该被部分隐藏
        if '@' in db_url:
            assert db_url.startswith('***@') or '...' in db_url

    def test_get_config_requires_auth(self, test_client):
        """测试未认证访问被拒绝."""
        response = test_client.get('/api/v1/config')
        assert response.status_code == 401


class TestConfigUpdateAPI:
    """测试配置更新 API."""

    def test_update_config_success(self, test_client, auth_headers):
        """测试成功更新配置."""
        payload = {
            'OPENHARNESS_DEFAULT_MODEL': 'claude-sonnet-4-20250514',
            'DEBUG': True,
            'LOG_LEVEL': 'DEBUG',
        }

        response = test_client.put(
            '/api/v1/config',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'message' in data
        assert 'updated' in data['message'].lower() or 'configuration' in data['message'].lower()

    def test_update_config_empty_body(self, test_client, auth_headers):
        """测试空更新请求."""
        payload = {}

        response = test_client.put(
            '/api/v1/config',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 200

    def test_update_config_requires_admin(self, test_client, user_auth_headers):
        """测试普通用户无法更新配置."""
        payload = {'DEBUG': True}

        response = test_client.put(
            '/api/v1/config',
            headers=user_auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 403


class TestConfigResetAPI:
    """测试配置重置 API."""

    def test_reset_config_success(self, test_client, auth_headers):
        """测试成功重置配置."""
        response = test_client.post(
            '/api/v1/config/reset',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'message' in data
        assert 'reset' in data['message'].lower()

    def test_reset_config_requires_admin(self, test_client, user_auth_headers):
        """测试普通用户无法重置配置."""
        response = test_client.post(
            '/api/v1/config/reset',
            headers=user_auth_headers,
        )
        assert response.status_code == 403


class TestConfigSchemaAPI:
    """测试配置 Schema API."""

    def test_get_config_schema(self, test_client, auth_headers):
        """测试获取配置 Schema（用于前端表单验证）."""
        response = test_client.get('/api/v1/config/schema', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'type' in data
        assert 'properties' in data

        # 验证 Schema 包含预期字段
        props = data['properties']
        assert 'OPENHARNESS_DEFAULT_MODEL' in props
        assert 'OPENHARNESS_MAX_TURNS' in props
        assert 'DEBUG' in props
        assert 'LOG_LEVEL' in props


class TestConfigProvidersAPI:
    """测试 LLM Provider 管理 API."""

    def test_list_providers(self, test_client, auth_headers):
        """测试获取 Provider 列表."""
        response = test_client.get('/api/v1/config/providers', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'providers' in data
        assert 'total' in data
        assert isinstance(data['providers'], list)

    def test_add_provider_requires_admin(self, test_client, user_auth_headers):
        """测试普通用户无法添加 Provider."""
        payload = {
            'type': 'custom',
            'base_url': 'https://api.example.com',
        }

        response = test_client.post(
            '/api/v1/config/providers',
            headers=user_auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 403

    def test_test_provider_connection(self, test_client, auth_headers):
        """测试 Provider 连接测试."""
        response = test_client.post(
            '/api/v1/config/providers/test-provider-id/test',
            headers=auth_headers,
            data=json.dumps({}),
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'status' in data
        assert 'latency_ms' in data
        assert data['status'] == 'ok'


class TestConfigValidationAPI:
    """测试配置验证 API."""

    def test_validate_config(self, test_client, auth_headers):
        """测试配置有效性验证."""
        response = test_client.get('/api/v1/config/validation', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'valid' in data
        assert 'errors' in data
        assert 'warnings' in data
        assert isinstance(data['errors'], list)
        assert isinstance(data['warnings'], list)
