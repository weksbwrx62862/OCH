"""Coordinator Service 单元测试 — 验证多智能体协调和任务分派."""

from __future__ import annotations

import pytest

from app.services.coordinator_service import CoordinatorService, BUILTIN_AGENT_DEFINITIONS


class TestCoordinatorServiceInit:
    """测试 CoordinatorService 初始化."""

    def test_builtin_agent_definitions_exist(self):
        """测试内置 Agent 定义存在."""
        assert 'code-reviewer' in BUILTIN_AGENT_DEFINITIONS
        assert 'debugger' in BUILTIN_AGENT_DEFINITIONS
        assert 'planner' in BUILTIN_AGENT_DEFINITIONS

    def test_init_references_builtin_definitions(self):
        """测试初始化时引用内置 Agent 定义."""
        service = CoordinatorService()
        assert len(service._agent_definitions) >= 3


class TestTeamManagement:
    """测试团队 CRUD 操作（数据库持久化）."""

    @pytest.fixture
    def coordinator(self, app):
        """创建 CoordinatorService 实例（依赖 app fixture 初始化数据库）."""
        return CoordinatorService()

    @pytest.mark.asyncio
    async def test_create_team_success(self, coordinator, db_session):
        """测试成功创建团队."""
        team = await coordinator.create_team(
            name='Test Team',
            description='A test team for unit testing',
        )

        assert team['name'] == 'Test Team'
        assert team['description'] == 'A test team for unit testing'
        assert team['status'] == 'active'
        assert 'id' in team
        assert 'created_at' in team

    @pytest.mark.asyncio
    async def test_create_team_with_members(self, coordinator, db_session):
        """测试创建带成员的团队."""
        members = [
            {'agent_id': 'agent-1', 'role': 'developer'},
            {'agent_id': 'agent-2', 'role': 'reviewer'},
        ]

        team = await coordinator.create_team(
            name='Dev Team',
            members=members,
        )

        assert team['name'] == 'Dev Team'

    @pytest.mark.asyncio
    async def test_list_teams_empty(self, coordinator, db_session):
        """测试空团队列表."""
        teams = await coordinator.list_teams()
        assert isinstance(teams, list)

    @pytest.mark.asyncio
    async def test_list_teams_with_data(self, coordinator, db_session):
        """测试有数据时的团队列表."""
        await coordinator.create_team(name='Team A')
        await coordinator.create_team(name='Team B')

        teams = await coordinator.list_teams()
        assert len(teams) >= 2

    @pytest.mark.asyncio
    async def test_get_team_success(self, coordinator, db_session):
        """测试获取存在的团队."""
        created = await coordinator.create_team(name='Get Team')
        team_id = created['id']

        team = await coordinator.get_team(team_id)

        assert team is not None
        assert team['name'] == 'Get Team'
        assert team['id'] == team_id

    @pytest.mark.asyncio
    async def test_get_team_not_found(self, coordinator, db_session):
        """测试获取不存在的团队."""
        team = await coordinator.get_team('nonexistent-id')
        assert team is None

    @pytest.mark.asyncio
    async def test_update_team_success(self, coordinator, db_session):
        """测试成功更新团队配置."""
        created = await coordinator.create_team(name='Old Name', description='Old desc')
        team_id = created['id']

        updated = await coordinator.update_team(
            team_id,
            name='New Name',
            description='Updated description',
        )

        assert updated is not None
        assert updated['name'] == 'New Name'
        assert updated['description'] == 'Updated description'

    @pytest.mark.asyncio
    async def test_update_team_not_found(self, coordinator, db_session):
        """测试更新不存在的团队."""
        result = await coordinator.update_team('ghost-id', name='Ghost')
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_team_success(self, coordinator, db_session):
        """测试成功解散团队（软删除）."""
        created = await coordinator.create_team(name='Delete Me')
        team_id = created['id']

        result = await coordinator.delete_team(team_id)

        assert result is True

        deleted = await coordinator.get_team(team_id)
        assert deleted is None or deleted.get('status') == 'dissolved'

    @pytest.mark.asyncio
    async def test_delete_team_not_found(self, coordinator, db_session):
        """测试删除不存在的团队."""
        result = await coordinator.delete_team('ghost-team-id')
        assert result is False


class TestAgentDefinitions:
    """测试子 Agent 定义管理."""

    @pytest.fixture
    def coordinator(self):
        """创建 CoordinatorService 实例."""
        return CoordinatorService()

    @pytest.mark.asyncio
    async def test_list_agent_definitions(self, coordinator):
        """测试列出所有可用 Agent 定义."""
        definitions = await coordinator.list_agent_definitions()

        assert len(definitions) >= 3

        ids = [d['id'] for d in definitions]
        assert 'code-reviewer' in ids
        assert 'debugger' in ids
        assert 'planner' in ids

    @pytest.mark.asyncio
    async def test_get_agent_definition_success(self, coordinator):
        """测试获取存在的 Agent 定义."""
        definition = await coordinator.get_agent_definition('code-reviewer')

        assert definition is not None
        assert definition['name'] == 'Code Reviewer'
        assert definition['id'] == 'code-reviewer'
        assert 'system_prompt' in definition
        assert 'capabilities' in definition
        assert 'tools' in definition

    @pytest.mark.asyncio
    async def test_get_agent_definition_not_found(self, coordinator):
        """测试获取不存在的 Agent 定义."""
        definition = await coordinator.get_agent_definition('nonexistent-agent')
        assert definition is None

    @pytest.mark.asyncio
    async def test_agent_definition_has_required_fields(self, coordinator):
        """测试 Agent 定义包含必要字段."""
        definition = await coordinator.get_agent_definition('debugger')

        required_fields = ['id', 'name', 'description', 'system_prompt',
                          'capabilities', 'tools']
        for field in required_fields:
            assert field in definition, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_code_reviewer_capabilities(self, coordinator):
        """测试 Code Reviewer 的能力配置."""
        definition = await coordinator.get_agent_definition('code-reviewer')

        assert 'read_code' in definition['capabilities']
        assert 'analyze_security' in definition['capabilities']
        assert 'suggest_improvements' in definition['capabilities']

        expected_tools = ['Read', 'Grep', 'Glob', 'WebSearch']
        for tool in expected_tools:
            assert tool in definition['tools']


class TestTaskDispatch:
    """测试任务分派功能."""

    @pytest.fixture
    def coordinator(self, app):
        """创建 CoordinatorService 实例（依赖 app fixture 初始化数据库）."""
        return CoordinatorService()

    @pytest.mark.asyncio
    async def test_dispatch_task_to_available_agent(self, coordinator):
        """分派任务给可用的 Code Reviewer Agent."""
        task = await coordinator.spawn_subagent(
            agent_definition_id='code-reviewer',
            task='Review this code for bugs and security issues',
        )

        assert task is not None
        assert task['type'] == 'subagent'
        assert task['agent_definition_id'] == 'code-reviewer'
        assert task['agent_name'] == 'Code Reviewer'
        assert task['task'] == 'Review this code for bugs and security issues'
        assert task['status'] == 'spawning'
        assert 'id' in task
        assert 'created_at' in task

    @pytest.mark.asyncio
    async def test_dispatch_to_debugger(self, coordinator):
        """分派任务给 Debugger Agent."""
        task = await coordinator.spawn_subagent(
            agent_definition_id='debugger',
            task='Debug the authentication module',
        )

        assert task['agent_name'] == 'Debugger'
        assert task['status'] == 'spawning'

    @pytest.mark.asyncio
    async def test_dispatch_to_planner(self, coordinator):
        """分派任务给 Planner Agent."""
        task = await coordinator.spawn_subagent(
            agent_definition_id='planner',
            task='Design architecture for new feature',
        )

        assert task['agent_name'] == 'Planner'
        assert task['status'] == 'spawning'

    @pytest.mark.asyncio
    async def test_no_available_agent_raises_error(self, coordinator):
        """无可用 Agent 时报错."""
        with pytest.raises(ValueError, match="Agent definition 'nonexistent' not found"):
            await coordinator.spawn_subagent(
                agent_definition_id='nonexistent',
                task='Do something impossible',
            )

    @pytest.mark.asyncio
    async def test_dispatch_with_team_context(self, coordinator, db_session):
        """测试在团队上下文中分派任务."""
        team = await coordinator.create_team(name='Dev Team')
        team_id = team['id']

        task = await coordinator.spawn_subagent(
            agent_definition_id='planner',
            task='Plan implementation',
            team_id=team_id,
        )

        assert task['team_id'] == team_id

    @pytest.mark.asyncio
    async def test_dispatch_with_parent_session(self, coordinator):
        """测试关联父会话的分派."""
        parent_session = 'session-12345'

        task = await coordinator.spawn_subagent(
            agent_definition_id='code-reviewer',
            task='Review code changes',
            parent_session_id=parent_session,
        )

        assert task['parent_session_id'] == parent_session

    @pytest.mark.asyncio
    async def test_dispatch_with_custom_context(self, coordinator):
        """测试携带自定义上下文的任务分派."""
        custom_context = {
            'repo_url': 'https://github.com/test/repo',
            'branch': 'feature/new-feature',
            'priority': 'high',
        }

        task = await coordinator.spawn_subagent(
            agent_definition_id='code-reviewer',
            task='Review PR #42',
            context=custom_context,
        )

        assert task['context'] == custom_context
        assert task['context']['priority'] == 'high'


class TestAgentSelection:
    """测试 Agent 选择策略（基于专长匹配）."""

    @pytest.fixture
    def coordinator(self):
        """创建 CoordinatorService 实例."""
        return CoordinatorService()

    @pytest.mark.asyncio
    async def test_select_by_specialty_code_review(self, coordinator):
        """根据任务类型选择专长 Agent — 代码审查."""
        task = await coordinator.spawn_subagent(
            agent_definition_id='code-reviewer',
            task='Review this pull request for security vulnerabilities',
        )

        agent_def = await coordinator.get_agent_definition(task['agent_definition_id'])
        assert 'analyze_security' in agent_def['capabilities']
        assert 'read_code' in agent_def['capabilities']

    @pytest.mark.asyncio
    async def test_select_by_specialty_debugging(self, coordinator):
        """根据任务类型选择专长 Agent — 调试."""
        task = await coordinator.spawn_subagent(
            agent_definition_id='debugger',
            task='Fix null pointer exception in user service',
        )

        agent_def = await coordinator.get_agent_definition(task['agent_definition_id'])
        assert 'find_root_cause' in agent_def['capabilities']
        assert 'propose_fix' in agent_def['capabilities']

    @pytest.mark.asyncio
    async def test_select_by_specialty_planning(self, coordinator):
        """根据任务类型选择专长 Agent — 规划."""
        task = await coordinator.spawn_subagent(
            agent_definition_id='planner',
            task='Design microservice architecture for payment system',
        )

        agent_def = await coordinator.get_agent_definition(task['agent_definition_id'])
        assert 'design_architecture' in agent_def['capabilities']
        assert 'break_down_tasks' in agent_def['capabilities']


class TestTaskStatusTracking:
    """测试任务状态跟踪."""

    @pytest.fixture
    def coordinator(self):
        """创建 CoordinatorService 实例."""
        return CoordinatorService()

    @pytest.mark.asyncio
    async def test_spawned_task_has_initial_status(self, coordinator):
        """测试生成任务的初始状态."""
        task = await coordinator.spawn_subagent(
            agent_definition_id='code-reviewer',
            task='Initial status check',
        )

        assert task['status'] == 'spawning'
        assert task['result'] is None
        assert task['error'] is None

    @pytest.mark.asyncio
    async def test_get_task_dependencies_returns_dag_structure(self, coordinator):
        """测试获取任务依赖关系图返回 DAG 结构."""
        deps = await coordinator.get_task_dependencies('task-123')

        assert 'task_id' in deps
        assert 'nodes' in deps
        assert 'edges' in deps
        assert deps['task_id'] == 'task-123'
        assert isinstance(deps['nodes'], list)
        assert isinstance(deps['edges'], list)


class TestProtocolStatusAndShutdown:
    """测试协议状态和关闭流程."""

    @pytest.fixture
    def coordinator(self, app):
        """创建 CoordinatorService 实例（依赖 app fixture 初始化数据库）."""
        return CoordinatorService()

    @pytest.mark.asyncio
    async def test_get_protocol_status_idle(self, coordinator, db_session):
        """测试空闲状态下的协议状态."""
        status = await coordinator.get_protocol_status()

        assert status['status'] == 'idle'
        assert isinstance(status['active_teams'], int)
        assert status['total_agents_spawned'] == 0
        assert status['shutdown_initiated'] is False

    @pytest.mark.asyncio
    async def test_get_protocol_status_with_active_teams(self, coordinator, db_session):
        """测试有活跃团队时的协议状态."""
        await coordinator.create_team(name='Active Team')
        await coordinator.create_team(name='Another Active Team')

        status = await coordinator.get_protocol_status()

        assert status['active_teams'] >= 2

    @pytest.mark.asyncio
    async def test_initiate_shutdown(self, coordinator):
        """测试发起关闭握手."""
        shutdown_info = await coordinator.initiate_shutdown()

        assert shutdown_info['status'] == 'shutdown_requested'
        assert 'message' in shutdown_info
        assert 'pending_tasks' in shutdown_info

    @pytest.mark.asyncio
    async def test_multiple_teams_creation_and_deletion(self, coordinator, db_session):
        """测试团队的批量创建和删除."""
        team_ids = []
        for i in range(5):
            team = await coordinator.create_team(name=f'Team {i}')
            team_ids.append(team['id'])

        teams = await coordinator.list_teams()
        assert len(teams) >= 5

        for team_id in team_ids:
            result = await coordinator.delete_team(team_id)
            assert result is True


class TestLoadBalancingSimulation:
    """模拟负载均衡分配场景."""

    @pytest.fixture
    def coordinator(self):
        """创建 CoordinatorService 实例."""
        return CoordinatorService()

    @pytest.mark.asyncio
    async def test_distribute_tasks_across_agents(self, coordinator):
        """将多个任务分发到不同的 Agent."""
        tasks = []

        tasks.append(await coordinator.spawn_subagent(
            agent_definition_id='code-reviewer',
            task='Review code A',
        ))
        tasks.append(await coordinator.spawn_subagent(
            agent_definition_id='debugger',
            task='Fix bug B',
        ))
        tasks.append(await coordinator.spawn_subagent(
            agent_definition_id='planner',
            task='Plan feature C',
        ))

        assert len(tasks) == 3

        task_ids = [t['id'] for t in tasks]
        assert len(set(task_ids)) == 3

        agent_types = [t['agent_name'] for t in tasks]
        assert 'Code Reviewer' in agent_types
        assert 'Debugger' in agent_types
        assert 'Planner' in agent_types

    @pytest.mark.asyncio
    async def test_same_agent_multiple_tasks(self, coordinator):
        """同一 Agent 处理多个任务."""
        task1 = await coordinator.spawn_subagent(
            agent_definition_id='code-reviewer',
            task='Review file 1',
        )
        task2 = await coordinator.spawn_subagent(
            agent_definition_id='code-reviewer',
            task='Review file 2',
        )
        task3 = await coordinator.spawn_subagent(
            agent_definition_id='code-reviewer',
            task='Review file 3',
        )

        assert task1['id'] != task2['id']
        assert task2['id'] != task3['id']
        assert task1['agent_definition_id'] == 'code-reviewer'
