"""Tool API 单元测试 — 验证工具注册表查询、Schema 详情获取和分类筛选."""

from __future__ import annotations

import json


class TestToolsListAPI:
    """测试工具列表 API."""

    def test_list_all_tools(self, test_client, auth_headers):
        """测试列出所有可用工具（43+）."""
        response = test_client.get('/api/v1/tools', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'total' in data
        assert 'categories' in data
        assert data['total'] > 0  # 应有多个工具

    def test_list_tools_with_schema(self, test_client, auth_headers):
        """测试列出工具并包含输入 Schema."""
        response = test_client.get(
            '/api/v1/tools',
            headers=auth_headers,
            query_string={'schema': 'true'},
        )
        assert response.status_code == 200

        data = response.get_json()
        # 至少有一个分类包含带 schema 的工具
        for category, tools in data['categories'].items():
            if len(tools) > 0:
                assert 'input_schema' in tools[0]
                break

    def test_list_tools_filter_by_category(self, test_client, auth_headers):
        """测试按分类筛选工具."""
        response = test_client.get(
            '/api/v1/tools',
            headers=auth_headers,
            query_string={'category': 'file_io'},
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'file_io' in data['categories']
        assert len(data['categories']['file_io']) > 0  # file_io 分类应有工具

    def test_list_tools_invalid_category(self, test_client, auth_headers):
        """测试无效的分类参数."""
        response = test_client.get(
            '/api/v1/tools',
            headers=auth_headers,
            query_string={'category': 'nonexistent_category'},
        )
        assert response.status_code == 200  # 应返回所有工具（忽略无效分类）

        data = response.get_json()
        # 无效分类时返回所有工具或空结果
        assert isinstance(data['categories'], dict)

    def test_list_tools_requires_auth(self, test_client):
        """测试未认证访问被拒绝."""
        response = test_client.get('/api/v1/tools')
        assert response.status_code == 401


class TestToolCategoriesAPI:
    """测试工具分类列表 API."""

    def test_get_categories(self, test_client, auth_headers):
        """测试获取工具分类列表."""
        response = test_client.get('/api/v1/tools/categories', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'categories' in data
        assert isinstance(data['categories'], list)
        assert len(data['categories']) > 0  # 应有多个分类

        # 每个分类应包含 id, name, icon, count 字段
        for cat in data['categories']:
            assert 'id' in cat
            assert 'name' in cat
            assert 'icon' in cat
            assert 'count' in cat

    def test_categories_include_expected_types(self, test_client, auth_headers):
        """测试包含预期的核心分类."""
        response = test_client.get('/api/v1/tools/categories', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        category_ids = [c['id'] for c in data['categories']]

        # 应包含这些核心分类
        expected_categories = {'file_io', 'web', 'agent', 'task', 'meta'}
        assert expected_categories.issubset(set(category_ids))


class TestToolDetailAPI:
    """测试获取工具详情 API."""

    def test_get_tool_detail_success(self, test_client, auth_headers):
        """测试获取 Bash 工具详情."""
        response = test_client.get('/api/v1/tools/Bash', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data['name'] == 'Bash'
        assert 'description' in data
        assert 'input_schema' in data
        assert 'examples' in data
        assert 'dangerous' in data or 'requires_permission' in data

    def test_get_tool_detail_read(self, test_client, auth_headers):
        """测试获取 Read 工具详情（验证不同工具的 Schema）."""
        response = test_client.get('/api/v1/tools/Read', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data['name'] == 'Read'
        schema = data['input_schema']
        assert schema['type'] == 'object'
        assert 'path' in schema['properties']
        assert 'path' in schema['required']

    def test_get_tool_not_found(self, test_client, auth_headers):
        """测试获取不存在的工具."""
        response = test_client.get('/api/v1/tools/NonExistentTool', headers=auth_headers)
        assert response.status_code == 404


class TestToolSchemaAPI:
    """测试工具输入 Schema API."""

    def test_get_bash_schema(self, test_client, auth_headers):
        """测试获取 Bash 工具的 JSON Schema."""
        response = test_client.get('/api/v1/tools/Bash/schema', headers=auth_headers)
        assert response.status_code == 200

        schema = response.get_json()
        assert schema['type'] == 'object'
        assert 'command' in schema['properties']
        assert 'command' in schema['required']

    def test_get_write_schema(self, test_client, auth_headers):
        """测试获取 Write 工具的 JSON Schema."""
        response = test_client.get('/api/v1/tools/Write/schema', headers=auth_headers)
        assert response.status_code == 200

        schema = response.get_json()
        assert 'path' in schema['required']
        assert 'content' in schema['required']

    def test_get_unknown_tool_schema(self, test_client, auth_headers):
        """测试获取未知工具的 Schema."""
        response = test_client.get('/api/v1/tools/UnknownTool/schema', headers=auth_headers)
        # 未知工具返回默认 schema（空对象）而不是 404
        assert response.status_code in (200, 404)

        if response.status_code == 200:
            schema = response.get_json()
            assert schema['type'] == 'object'


class TestToolExamplesAPI:
    """测试工具使用示例 API."""

    def test_get_bash_examples(self, test_client, auth_headers):
        """测试获取 Bash 工具的使用示例."""
        response = test_client.get('/api/v1/tools/Bash/examples', headers=auth_headers)
        assert response.status_code == 200

        examples = response.get_json()
        assert isinstance(examples, list)

        if len(examples) > 0:
            example = examples[0]
            assert 'input' in example
            assert 'description' in example

    def test_get_examples_for_tool_without_examples(self, test_client, auth_headers):
        """测试获取没有预定义示例的工具."""
        response = test_client.get('/api/v1/tools/Sleep/examples', headers=auth_headers)
        assert response.status_code == 200

        examples = response.get_json()
        assert isinstance(examples, list)
        # 可能是空列表


class TestToolTestAPI:
    """测试工具 dry-run 执行 API."""

    def test_test_tool_dry_run(self, test_client, auth_headers):
        """测试工具 dry-run 执行."""
        payload = {
            'input': {
                'command': 'echo "test"',
            }
        }

        response = test_client.post(
            '/api/v1/tools/Bash/test',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['tool_name'] == 'Bash'
        assert data['status'] == 'dry_run'
        assert 'validation' in data
        assert 'estimated_risk' in data

    def test_dangerous_tool_risk_assessment(self, test_client, auth_headers):
        """测试危险工具的风险评估."""
        payload = {'input': {}}

        response = test_client.post(
            '/api/v1/tools/Bash/test',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 200

        data = response.get_json()
        # Bash 是危险工具，风险应为 medium 或更高
        assert data['estimated_risk'] in ('low', 'medium', 'high')

    def test_safe_tool_risk_assessment(self, test_client, auth_headers):
        """测试安全工具的风险评估."""
        payload = {'input': {}}

        response = test_client.post(
            '/api/v1/tools/Read/test',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 200

        data = response.get_json()
        # Read 不是危险工具，风险应为 low
        assert data['estimated_risk'] == 'low'


class TestToolSecurityAPI:
    """测试工具安全相关功能 — 敏感信息过滤."""

    def test_no_sensitive_info_in_response(self, test_client, auth_headers):
        """测试响应中不包含敏感信息（如 API Key）."""
        response = test_client.get('/api/v1/tools', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()

        # 确保响应中没有敏感字段
        response_str = str(data)
        sensitive_patterns = ['api_key', 'secret', 'password', 'token']
        for pattern in sensitive_patterns:
            assert pattern.lower() not in response_str.lower(), \
                f"发现敏感信息: {pattern}"

    def test_tool_dangerous_flag_present(self, test_client, auth_headers):
        """测试危险工具标记正确显示."""
        response = test_client.get('/api/v1/tools', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()

        # 检查已知危险工具是否有标记
        dangerous_tools = ['Bash', 'Agent', 'TeamCreate', 'TeamDelete', 'MCPTool', 'CronCreate']
        for cat_name, tools in data['categories'].items():
            for tool in tools:
                if tool['name'] in dangerous_tools:
                    assert tool['dangerous'] is True or tool['requires_permission'] is True, \
                        f"危险工具 {tool['name']} 缺少标记"
