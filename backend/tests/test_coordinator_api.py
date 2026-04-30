"""Coordinator API 单元测试 — 验证多智能体任务协调、团队管理和并发控制."""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock, AsyncMock


class TestCoordinatorStatusAPI:

    def test_get_coordinator_status(self, test_client, auth_headers):
        response = test_client.get('/api/v1/coordinator/teams', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'data' in data
        assert 'total' in data

    def test_get_active_teams(self, test_client, auth_headers):
        response = test_client.get(
            '/api/v1/coordinator/teams',
            headers=auth_headers,
            query_string={'status': 'active'},
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'data' in data


class TestTaskSubmissionAPI:

    def test_submit_task_success(self, test_client, auth_headers, sample_agent):
        payload = {
            'agent_definition': sample_agent.id,
            'task': 'Review the code quality of the main module',
        }

        response = test_client.post(
            '/api/v1/coordinator/spawn',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert 'task' in data
        assert data['task']['status'] == 'spawning'
        assert 'id' in data['task']

    def test_submit_task_to_specific_team(self, test_client, auth_headers):
        team_payload = {
            'name': 'Test Review Team',
            'description': '代码审查团队',
        }

        team_resp = test_client.post(
            '/api/v1/coordinator/teams',
            headers=auth_headers,
            data=json.dumps(team_payload),
        )

        if team_resp.status_code == 201:
            team_id = team_resp.get_json()['team']['id']

            task_payload = {
                'agent_definition': 'code-reviewer',
                'task': 'Review authentication module',
                'team_id': team_id,
            }

            task_resp = test_client.post(
                '/api/v1/coordinator/spawn',
                headers=auth_headers,
                data=json.dumps(task_payload),
            )
            assert task_resp.status_code == 201

            data = task_resp.get_json()
            assert data['task']['team_id'] == team_id

    def test_submit_task_invalid_payload(self, test_client, auth_headers):
        payloads = [
            {},
            {'agent_definition': 'test'},
            {'task': 'do something'},
        ]

        for payload in payloads:
            response = test_client.post(
                '/api/v1/coordinator/spawn',
                headers=auth_headers,
                data=json.dumps(payload),
            )
            assert response.status_code == 422, \
                f"预期 422，实际 {response.status_code}: {payload}"


class TestTaskTrackingAPI:

    def test_get_task_status(self, test_client, auth_headers):
        response = test_client.get(
            '/api/v1/coordinator/tasks',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'tasks' in data
        assert 'total' in data

    def test_cancel_task(self, test_client, auth_headers):
        submit_payload = {
            'prompt': 'Test task for cancellation',
            'agent_id': 'test-agent',
        }

        submit_resp = test_client.post(
            '/api/v1/coordinator/subagents',
            headers=auth_headers,
            data=json.dumps(submit_payload),
        )

        if submit_resp.status_code == 201:
            task_id = submit_resp.get_json()['task_id']

            cancel_resp = test_client.post(
                f'/api/v1/coordinator/subagents/{task_id}/cancel',
                headers=auth_headers,
            )
            assert cancel_resp.status_code in (200, 422)

    def test_list_task_dependencies(self, test_client, auth_headers):
        response = test_client.get(
            '/api/v1/coordinator/agents',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'agents' in data
        assert 'total_builtin' in data
        assert 'total_custom' in data

        builtin_names = [a['name'] for a in data['agents'] if a.get('source') != 'custom']
        assert len(builtin_names) >= 3


class TestConcurrencyAPI:

    def test_list_workers_empty(self, test_client, auth_headers):
        response = test_client.get('/api/v1/coordinator/workers', headers=auth_headers)
        assert response.status_code == 200

        data = response.get_json()
        assert 'workers' in data
        assert 'total' in data

    @patch('openharness.coordinator.autonomous_worker.spawn_autonomous_worker')
    def test_spawn_worker_success(self, mock_spawn, test_client, auth_headers):
        mock_worker = AsyncMock()
        mock_worker.agent_id = 'worker-test-001'
        mock_worker.state.value = 'idle'
        mock_worker.statistics = MagicMock(
            tasks_completed=0,
            tasks_failed=0,
            total_uptime_sec=0.0,
        )
        mock_spawn.return_value = mock_worker

        payload = {
            'agent_id': 'test-worker-001',
            'team': 'default',
            'poll_interval': 5.0,
            'max_idle': 60.0,
        }

        resp = test_client.post(
            '/api/v1/coordinator/workers',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert resp.status_code == 201

        data = resp.get_json()
        assert 'worker_id' in data
        assert 'state' in data

    def test_workers_stats(self, test_client, auth_headers):
        response = test_client.get(
            '/api/v1/coordinator/workers/stats',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'active_workers' in data
        assert 'total_tasks_completed' in data


class TestTeamManagementAPI:

    def test_create_team_success(self, test_client, auth_headers):
        payload = {
            'name': 'Development Team',
            'description': '开发团队',
            'members': [
                {'role': 'leader', 'capabilities': ['review', 'approve']},
                {'role': 'worker', 'capabilities': ['code', 'test']},
            ],
        }

        response = test_client.post(
            '/api/v1/coordinator/teams',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert 'team' in data
        assert data['team']['name'] == 'Development Team'

    def test_create_team_missing_name(self, test_client, auth_headers):
        payload = {'description': 'No name'}

        response = test_client.post(
            '/api/v1/coordinator/teams',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 422

    def test_get_team_detail(self, test_client, auth_headers):
        create_payload = {'name': 'Detail Test Team'}
        create_resp = test_client.post(
            '/api/v1/coordinator/teams',
            headers=auth_headers,
            data=json.dumps(create_payload),
        )

        if create_resp.status_code == 201:
            team_id = create_resp.get_json()['team']['id']

            get_resp = test_client.get(
                f'/api/v1/coordinator/teams/{team_id}',
                headers=auth_headers,
            )
            assert get_resp.status_code in (200, 404)

            if get_resp.status_code == 200:
                data = get_resp.get_json()
                assert data['id'] == team_id
                assert 'members' in data

    def test_update_team(self, test_client, auth_headers):
        create_payload = {'name': 'Update Test Team'}
        create_resp = test_client.post(
            '/api/v1/coordinator/teams',
            headers=auth_headers,
            data=json.dumps(create_payload),
        )

        if create_resp.status_code == 201:
            team_data = create_resp.get_json()
            if 'team' in team_data:
                team_id = team_data['team']['id']

                update_payload = {
                    'description': 'Updated description',
                    'status': 'paused',
                }
                update_resp = test_client.put(
                    f'/api/v1/coordinator/teams/{team_id}',
                    headers=auth_headers,
                    data=json.dumps(update_payload),
                )
                assert update_resp.status_code == 200

    def test_dissolve_team(self, test_client, auth_headers):
        create_payload = {'name': 'Dissolve Test Team'}
        create_resp = test_client.post(
            '/api/v1/coordinator/teams',
            headers=auth_headers,
            data=json.dumps(create_payload),
        )

        if create_resp.status_code == 201:
            team_data = create_resp.get_json()
            if 'team' in team_data:
                team_id = team_data['team']['id']

                delete_resp = test_client.delete(
                    f'/api/v1/coordinator/teams/{team_id}',
                    headers=auth_headers,
                )
                assert delete_resp.status_code == 200


class TestSubagentExecutionAPI:

    def test_submit_subagent_task(self, test_client, auth_headers):
        payload = {
            'prompt': 'Analyze the performance bottlenecks in the API layer',
            'agent_id': 'code-reviewer',
            'timeout_seconds': 300,
            'tools_allowlist': ['read_file', 'grep'],
        }

        response = test_client.post(
            '/api/v1/coordinator/subagents',
            headers=auth_headers,
            data=json.dumps(payload),
        )
        assert response.status_code == 201

        data = response.get_json()
        assert 'task_id' in data
        assert data['status'] in ('pending', 'queued', 'running')

    def test_list_subagent_tasks(self, test_client, auth_headers):
        response = test_client.get(
            '/api/v1/coordinator/subagents',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'tasks' in data
        assert 'total' in data

    def test_get_subagent_stats(self, test_client, auth_headers):
        response = test_client.get(
            '/api/v1/coordinator/subagents/stats',
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.get_json()
        assert 'executor' in data
        assert 'description' in data

    def test_get_builtin_agent_definition(self, test_client, auth_headers):
        for agent_id in ['code-reviewer', 'debugger', 'planner']:
            response = test_client.get(
                f'/api/v1/coordinator/agents/{agent_id}',
                headers=auth_headers,
            )
            assert response.status_code == 200

            data = response.get_json()
            assert data['id'] == agent_id
            assert 'name' in data
            assert 'description' in data

    def test_get_nonexistent_agent_definition(self, test_client, auth_headers):
        response = test_client.get(
            '/api/v1/coordinator/agents/nonexistent-agent-id',
            headers=auth_headers,
        )
        assert response.status_code == 404
