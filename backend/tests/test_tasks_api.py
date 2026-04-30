"""Task API 单元测试 — 验证后台任务 CRUD 操作、状态转换和 DAG 依赖管理."""

from __future__ import annotations

import json


class TestTasksListAPI:
    """测试任务列表 API."""

    def test_list_tasks_empty(self, test_client, auth_headers):
        """测试空任务列表返回."""
        response = test_client.get('/api/v1/tasks', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'data' in data
        assert 'total' in data
        assert data['total'] == 0
        assert len(data['data']) == 0

    def test_list_tasks_with_data(self, test_client, auth_headers, sample_task):
        """测试有数据时的任务列表."""
        response = test_client.get('/api/v1/tasks', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert data['total'] >= 1

        task_ids = [t['id'] for t in data['data']]
        assert sample_task.id in task_ids

    def test_list_tasks_pagination(self, test_client, auth_headers):
        """测试分页功能."""
        response = test_client.get(
            '/api/v1/tasks',
            headers=auth_headers,
            query_string={'page': 1, 'per_page': 10}
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'page' in data
        assert 'per_page' in data
        assert 'status_stats' in data

    def test_list_tasks_filter_by_status(self, test_client, auth_headers, sample_task):
        """测试按状态筛选任务."""
        response = test_client.get(
            '/api/v1/tasks',
            headers=auth_headers,
            query_string={'status': sample_task.status}
        )
        assert response.status_code == 200

        data = response.get_json()
        for task in data['data']:
            assert task['status'] == sample_task.status

    def test_list_tasks_requires_auth(self, test_client):
        """测试未认证访问被拒绝."""
        response = test_client.get('/api/v1/tasks')
        assert response.status_code == 401


class TestTaskCreateAPI:
    """测试任务创建 API."""

    def test_create_task_success(self, test_client, auth_headers):
        """测试成功创建任务."""
        payload = {
            'type': 'command',
            'command': 'echo "hello world"',
        }

        response = test_client.post(
            '/api/v1/tasks',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert 'task' in data
        assert data['task']['command'] == 'echo "hello world"'
        assert data['task']['status'] == 'pending'

    def test_create_task_missing_command(self, test_client, auth_headers):
        """测试缺少命令字段."""
        payload = {'type': 'command'}

        response = test_client.post(
            '/api/v1/tasks',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 422  # ValidationError → 422

    def test_create_task_with_session_id(self, test_client, auth_headers, sample_session):
        """测试关联会话 ID 创建任务."""
        payload = {
            'type': 'command',
            'command': 'ls -la',
            'session_id': sample_session.id,
        }

        response = test_client.post(
            '/api/v1/tasks',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert data['task']['session_id'] == sample_session.id

    def test_create_task_with_metadata(self, test_client, auth_headers):
        """测试携带元数据创建任务."""
        payload = {
            'type': 'query',
            'command': 'SELECT * FROM users',
            'metadata': {'priority': 'high', 'timeout': 30},
        }

        response = test_client.post(
            '/api/v1/tasks',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert data['task']['metadata']['priority'] == 'high'

    def test_create_task_requires_auth(self, test_client):
        """测试未认证访问被拒绝."""
        payload = {'command': 'test'}
        response = test_client.post('/api/v1/tasks', data=json.dumps(payload))
        assert response.status_code == 401


class TestTaskGetAPI:
    """测试获取任务详情 API."""

    def test_get_task_success(self, test_client, auth_headers, sample_task):
        """测试获取任务详情."""
        response = test_client.get(
            f'/api/v1/tasks/{sample_task.id}',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['id'] == sample_task.id
        assert data['command'] == sample_task.command
        assert data['status'] == sample_task.status

    def test_get_task_not_found(self, test_client, auth_headers):
        """测试获取不存在的任务."""
        fake_id = 'non-existent-task-id-12345'
        response = test_client.get(f'/api/v1/tasks/{fake_id}', headers=auth_headers)
        assert response.status_code == 404  # NotFoundError

    def test_get_task_output(self, test_client, auth_headers, sample_task):
        """测试获取任务输出."""
        response = test_client.get(
            f'/api/v1/tasks/{sample_task.id}/output',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'output' in data
        assert 'error' in data
        assert 'exit_code' in data
        assert 'status' in data


class TestTaskUpdateAPI:
    """测试任务更新 API."""

    def test_update_task_status(self, test_client, auth_headers, sample_task):
        """测试更新任务状态（先转为 running，再转为 completed）."""
        # 第一步：pending → running
        payload_running = {'status': 'running'}
        response = test_client.put(
            f'/api/v1/tasks/{sample_task.id}/update',
            headers=auth_headers,
            data=json.dumps(payload_running),
        )
        assert response.status_code == 200
        assert response.get_json()['task']['status'] == 'running'

        # 第二步：running → completed
        payload_completed = {
            'status': 'completed',
            'result': 'Task executed successfully',
            'exit_code': 0,
        }
        response = test_client.put(
            f'/api/v1/tasks/{sample_task.id}/update',
            headers=auth_headers,
            data=json.dumps(payload_completed),
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['task']['status'] == 'completed'
        assert data['task']['result'] == 'Task executed successfully'
        assert data['status_changed'] is True
        assert 'updated_fields' in data

    def test_update_task_invalid_status_transition(self, test_client, auth_headers, sample_task):
        """测试无效的状态转换."""
        # pending 状态不能直接跳到 failed
        payload = {'status': 'failed'}

        response = test_client.put(
            f'/api/v1/tasks/{sample_task.id}/update',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 422  # ValidationError - invalid transition

    def test_update_task_not_found(self, test_client, auth_headers):
        """测试更新不存在的任务."""
        payload = {'status': 'completed'}
        response = test_client.put(
            '/api/v1/tasks/nonexistent/update',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 404


class TestTaskStopAPI:
    """测试停止任务 API."""

    def test_stop_pending_task(self, test_client, auth_headers, sample_task):
        """测试停止 pending 状态任务."""
        response = test_client.put(
            f'/api/v1/tasks/{sample_task.id}/stop',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['new_status'] in ('stopped', 'cancelled')
        assert 'previous_status' in data

    def test_stop_nonexistent_task(self, test_client, auth_headers):
        """测试停止不存在的任务."""
        response = test_client.put(
            '/api/v1/tasks/ghost-task-id/stop',
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestTaskDeleteAPI:
    """测试删除任务 API."""

    def test_delete_task_success(self, test_client, auth_headers, sample_task):
        """测试成功删除任务."""
        response = test_client.delete(
            f'/api/v1/tasks/{sample_task.id}',
            headers=auth_headers,
        )
        assert response.status_code == 200

        # 验证已删除
        get_resp = test_client.get(
            f'/api/v1/tasks/{sample_task.id}',
            headers=auth_headers,
        )
        assert get_resp.status_code == 404

    def test_delete_task_not_found(self, test_client, auth_headers):
        """测试删除不存在的任务."""
        response = test_client.delete(
            '/api/v1/tasks/ghost-task-id',
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestTaskDependencyAPI:
    """测试任务依赖 (DAG) API."""

    def test_create_tasks_with_dependencies(self, test_client, auth_headers):
        """测试创建带依赖关系的任务组."""
        payload = {
            'tasks': [
                {
                    'type': 'command',
                    'command': 'npm install',
                    'deps': [],
                },
                {
                    'type': 'command',
                    'command': 'npm test',
                    'deps': [0],  # 依赖第一个任务（索引引用）
                },
            ],
        }

        response = test_client.post(
            '/api/v1/tasks/create-with-deps',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert len(data['tasks']) == 2
        assert data['dependency_count'] == 1
        assert data['tasks'][0]['status'] == 'pending'
        assert data['tasks'][1]['status'] == 'waiting'

    def test_create_empty_deps_list(self, test_client, auth_headers):
        """测试空任务列表应返回错误."""
        payload = {'tasks': []}

        response = test_client.post(
            '/api/v1/tasks/create-with-deps',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 422

    def test_add_dependency_to_task(self, test_client, auth_headers, sample_task):
        """测试为已有任务添加新依赖."""
        # 先创建一个被依赖的任务
        create_payload = {
            'type': 'command',
            'command': 'setup.sh',
        }
        create_resp = test_client.post(
            '/api/v1/tasks',
            headers=auth_headers,
            data=json.dumps(create_payload),
        )
        dep_task_id = create_resp.get_json()['task']['id']

        # 为 sample_task 添加依赖
        add_dep_payload = {
            'dep_task_id': dep_task_id,
        }
        response = test_client.post(
            f'/api/v1/tasks/{sample_task.id}/deps',
            headers=auth_headers,
            data=json.dumps(add_dep_payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert 'dependency' in data
        assert data['dependency']['dep_task_id'] == dep_task_id

    def test_get_task_dependencies(self, test_client, auth_headers, sample_task):
        """测试获取任务的依赖关系."""
        response = test_client.get(
            f'/api/v1/tasks/{sample_task.id}/deps',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'task_id' in data
        assert 'dependencies' in data
        assert 'dependents' in data


class TestTaskStatsAPI:
    """测试任务统计 API."""

    def test_get_global_stats(self, test_client, auth_headers, sample_task):
        """测试获取全局任务统计."""
        response = test_client.get(
            '/api/v1/tasks/stats',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'total' in data
        assert 'active' in data
        assert 'by_status' in data
        assert data['total'] >= 1
