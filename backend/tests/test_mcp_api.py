"""MCP 服务器管理 API 单元测试 — 验证服务器 CRUD、工具发现和连接状态."""

from __future__ import annotations

import json


class TestMCPServerListAPI:
    """测试 MCP 服务器列表 API."""

    def test_list_servers_empty(self, test_client, auth_headers):
        """测试空列表返回."""
        response = test_client.get('/api/v1/mcp/servers', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'data' in data
        assert 'total' in data
        assert data['total'] == 0
        assert len(data['data']) == 0

    def test_list_servers_with_data(self, test_client, auth_headers, db_session):
        """测试有数据时的列表."""
        from app.models.mcp_server import MCPServer
        import uuid
        import asyncio

        server = MCPServer(
            id=str(uuid.uuid4()),
            name='test-mcp-server',
            server_type='stdio',
            command='node',
            args=['server.js'],
            enabled=True,
        )
        db_session.add(server)
        asyncio.get_event_loop().run_until_complete(db_session.commit())

        response = test_client.get('/api/v1/mcp/servers', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data['total'] >= 1

        server_names = [s['name'] for s in data['data']]
        assert 'test-mcp-server' in server_names

    def test_list_servers_requires_auth(self, test_client):
        """测试未认证访问被拒绝."""
        response = test_client.get('/api/v1/mcp/servers')
        assert response.status_code == 401


class TestMCPServerCreateAPI:
    """测试 MCP 服务器创建 API."""

    def test_create_server_success(self, test_client, auth_headers):
        """测试成功创建服务器."""
        payload = {
            'name': 'New Test Server',
            'type': 'stdio',
            'command': 'python',
            'args': ['mcp_server.py'],
            'env': {'DEBUG': 'true'},
            'enabled': True,
            'auto_start': False,
        }

        response = test_client.post(
            '/api/v1/mcp/servers',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert 'server' in data
        assert data['server']['name'] == 'New Test Server'
        assert data['server']['type'] == 'stdio'

    def test_create_server_missing_name(self, test_client, auth_headers):
        """测试缺少名称字段."""
        payload = {'type': 'stdio'}

        response = test_client.post(
            '/api/v1/mcp/servers',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 422

    def test_create_server_requires_admin(self, test_client, user_auth_headers):
        """测试普通用户无法创建服务器."""
        payload = {'name': 'Should Fail'}

        response = test_client.post(
            '/api/v1/mcp/servers',
            headers=user_auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 403


class TestMCPServerGetAndUpdateAPI:
    """测试服务器获取和更新 API."""

    def test_update_server_success(self, test_client, auth_headers, db_session):
        """测试成功更新服务器配置."""
        from app.models.mcp_server import MCPServer
        import uuid
        import asyncio

        server = MCPServer(
            id=str(uuid.uuid4()),
            name='updatable-server',
            server_type='stdio',
            command='node',
        )
        db_session.add(server)
        asyncio.get_event_loop().run_until_complete(db_session.commit())
        asyncio.get_event_loop().run_until_complete(db_session.refresh(server))

        payload = {'command': 'python3', 'enabled': False}
        response = test_client.put(
            f'/api/v1/mcp/servers/{server.id}',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 200

    def test_update_server_not_found(self, test_client, auth_headers):
        """测试更新不存在的服务器."""
        payload = {'name': 'Ghost'}
        response = test_client.put(
            '/api/v1/mcp/servers/nonexistent-id',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 404

    def test_update_server_requires_admin(self, test_client, user_auth_headers, db_session):
        """测试普通用户无法更新服务器."""
        from app.models.mcp_server import MCPServer
        import uuid
        import asyncio

        server = MCPServer(
            id=str(uuid.uuid4()),
            name='protected-server',
            server_type='stdio',
        )
        db_session.add(server)
        asyncio.get_event_loop().run_until_complete(db_session.commit())
        asyncio.get_event_loop().run_until_complete(db_session.refresh(server))

        payload = {'enabled': False}
        response = test_client.put(
            f'/api/v1/mcp/servers/{server.id}',
            headers=user_auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 403


class TestMCPServerDeleteAPI:
    """测试服务器删除 API."""

    def test_delete_server_success(self, test_client, auth_headers, db_session):
        """测试成功删除服务器."""
        from app.models.mcp_server import MCPServer
        import uuid
        import asyncio

        server = MCPServer(
            id=str(uuid.uuid4()),
            name='deletable-server',
            server_type='stdio',
        )
        db_session.add(server)
        asyncio.get_event_loop().run_until_complete(db_session.commit())
        asyncio.get_event_loop().run_until_complete(db_session.refresh(server))

        response = test_client.delete(
            f'/api/v1/mcp/servers/{server.id}',
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_delete_server_not_found(self, test_client, auth_headers):
        """测试删除不存在的服务器."""
        response = test_client.delete(
            '/api/v1/mcp/servers/ghost-server-id',
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_server_requires_admin(self, test_client, user_auth_headers):
        """测试普通用户无法删除服务器."""
        response = test_client.delete(
            '/api/v1/mcp/servers/some-server-id',
            headers=user_auth_headers,
        )
        assert response.status_code == 403


class TestMCPToolsAndResourcesAPI:
    """测试工具发现和资源列表 API."""

    def test_list_tools_mock(self, test_client, auth_headers, db_session):
        """测试获取服务器工具列表（Mock 数据）."""
        from app.models.mcp_server import MCPServer
        import uuid
        import asyncio

        server = MCPServer(
            id=str(uuid.uuid4()),
            name='tools-server',
            server_type='stdio',
            discovered_tools=['read_file', 'write_file', 'execute_command'],
        )
        db_session.add(server)
        asyncio.get_event_loop().run_until_complete(db_session.commit())
        asyncio.get_event_loop().run_until_complete(db_session.refresh(server))

        response = test_client.get(
            f'/api/v1/mcp/servers/{server.id}/tools',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'tools' in data
        assert 'server_id' in data
        assert data['server_id'] == server.id
        assert len(data['tools']) == 3

    def test_list_resources_mock(self, test_client, auth_headers, db_session):
        """测试获取服务器资源列表（Mock 数据）."""
        from app.models.mcp_server import MCPServer
        import uuid
        import asyncio

        server = MCPServer(
            id=str(uuid.uuid4()),
            name='resources-server',
            server_type='stdio',
            discovered_resources=['config://app', 'logs://system'],
        )
        db_session.add(server)
        asyncio.get_event_loop().run_until_complete(db_session.commit())
        asyncio.get_event_loop().run_until_complete(db_session.refresh(server))

        response = test_client.get(
            f'/api/v1/mcp/servers/{server.id}/resources',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'resources' in data
        assert len(data['resources']) == 2

    def test_tools_server_not_found(self, test_client, auth_headers):
        """测试获取不存在服务器的工具列表."""
        response = test_client.get(
            '/api/v1/mcp/servers/fake-id/tools',
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestMCPConnectionTestAPI:
    """测试连接状态查询 API."""

    def test_connection_test_success(self, test_client, auth_headers, db_session):
        """测试成功连接测试."""
        from app.models.mcp_server import MCPServer
        import uuid
        import asyncio

        server = MCPServer(
            id=str(uuid.uuid4()),
            name='testable-server',
            server_type='stdio',
            enabled=True,
        )
        db_session.add(server)
        asyncio.get_event_loop().run_until_complete(db_session.commit())
        asyncio.get_event_loop().run_until_complete(db_session.refresh(server))

        response = test_client.post(
            f'/api/v1/mcp/servers/{server.id}/test',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'status' in data
        assert 'latency_ms' in data
        assert data['status'] in ['ok', 'disabled']

    def test_connection_test_disabled_server(self, test_client, auth_headers, db_session):
        """测试禁用服务器的连接测试."""
        from app.models.mcp_server import MCPServer
        import uuid
        import asyncio

        server = MCPServer(
            id=str(uuid.uuid4()),
            name='disabled-server',
            server_type='stdio',
            enabled=False,
        )
        db_session.add(server)
        asyncio.get_event_loop().run_until_complete(db_session.commit())
        asyncio.get_event_loop().run_until_complete(db_session.refresh(server))

        response = test_client.post(
            f'/api/v1/mcp/servers/{server.id}/test',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'disabled'

    def test_connection_test_server_not_found(self, test_client, auth_headers):
        """测试连接不存在的服务器."""
        response = test_client.post(
            '/api/v1/mcp/servers/ghost-id/test',
            headers=auth_headers,
        )
        assert response.status_code == 404
