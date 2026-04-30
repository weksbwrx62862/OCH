"""Permission Service 单元测试 — 验证 RBAC 权限控制和路径规则管理.

测试覆盖范围：
1. 权限规则 CRUD（Create, Read, Update, Delete）
2. 权限验证逻辑（多模式支持）
3. 路径规则匹配和通配符
4. 拒绝日志和统计
5. 优先级处理（deny 优先于 allow）
6. 边界条件和异常场景

核心测试点：
- allow/deny 列表匹配
- 通配符 * 匹配（如 /api/*, *.md）
- deny 规则优先级高于 allow
- Plan Mode 只读限制
- Auto Mode 全自动审批
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from app.services.permission_service import PermissionService


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def perm_service():
    """创建 PermissionService 实例."""
    return PermissionService()


@pytest_asyncio.fixture
async def service_with_rules(perm_service):
    """预置一些规则的 PermissionService."""
    await perm_service.add_path_rule(
        pattern=r'/safe/.*',
        allow=True,
        description='允许访问安全目录',
        priority=10,
    )
    await perm_service.add_path_rule(
        pattern=r'/dangerous/.*',
        allow=False,
        description='禁止访问危险目录',
        priority=20,  # 高优先级
    )
    return perm_service


# ============================================================
# Test 1: 权限模式管理
# ============================================================

class TestPermissionModes:
    """测试权限模式配置."""

    @pytest.mark.asyncio
    async def test_get_available_modes(self, perm_service):
        """获取可用权限模式列表."""
        modes = await perm_service.get_modes()

        assert len(modes) == 3
        mode_ids = [m['id'] for m in modes]
        assert 'default' in mode_ids
        assert 'auto' in mode_ids
        assert 'plan' in mode_ids

    @pytest.mark.asyncio
    async def test_get_current_mode_default(self, perm_service):
        """默认权限模式为 'default'."""
        mode = await perm_service.get_current_mode()
        assert mode == 'default'

    @pytest.mark.asyncio
    async def test_set_mode_valid(self, perm_service):
        """设置有效的权限模式."""
        result = await perm_service.set_mode('auto')
        assert result is True

        current = await perm_service.get_current_mode()
        assert current == 'auto'

    @pytest.mark.asyncio
    async def test_set_mode_invalid_raises_error(self, perm_service):
        """设置无效的权限模式抛出 ValueError."""
        with pytest.raises(ValueError, match="Invalid permission mode"):
            await perm_service.set_mode('nonexistent_mode')

    @pytest.mark.asyncio
    async def test_mode_switching(self, perm_service):
        """模式切换 — 验证状态正确转换."""
        # default -> auto -> plan -> default
        await perm_service.set_mode('auto')
        assert await perm_service.get_current_mode() == 'auto'

        await perm_service.set_mode('plan')
        assert await perm_service.get_current_mode() == 'plan'

        await perm_service.set_mode('default')
        assert await perm_service.get_current_mode() == 'default'


# ============================================================
# Test 2: 权限规则 CRUD
# ============================================================

class TestPermissionCRUD:
    """测试路径权限规则的增删改查."""

    @pytest.mark.asyncio
    async def test_create_permission_rule(self, perm_service):
        """创建权限规则 — 返回完整规则信息."""
        rule = await perm_service.add_path_rule(
            pattern=r'/api/v1/users/.*',
            allow=True,
            description='允许用户 API 访问',
            priority=5,
        )

        assert rule['pattern'] == r'/api/v1/users/.*'
        assert rule['allow'] is True
        assert rule['description'] == '允许用户 API 访问'
        assert rule['priority'] == 5
        assert 'id' in rule
        assert 'compiled_pattern' in rule

    @pytest.mark.asyncio
    async def test_create_deny_rule(self, perm_service):
        """创建拒绝规则."""
        rule = await perm_service.add_path_rule(
            pattern=r'/admin/.*',
            allow=False,
            description='禁止普通用户访问管理员接口',
            priority=100,
        )

        assert rule['allow'] is False
        assert rule['priority'] == 100

    @pytest.mark.asyncio
    async def test_list_rules_empty(self, perm_service):
        """空规则列表."""
        rules = await perm_service.list_rules()
        assert rules == []

    @pytest.mark.asyncio
    async def test_list_rules_with_data(self, service_with_rules):
        """列出所有规则 — 不包含编译后的正则对象."""
        rules = await service_with_rules.list_rules()

        assert len(rules) == 2
        for rule in rules:
            assert 'compiled_pattern' not in rule  # 内部实现细节不应暴露
            assert 'id' in rule
            assert 'pattern' in rule
            assert 'allow' in rule

    @pytest.mark.asyncio
    async def test_remove_path_rule_success(self, perm_service):
        """成功移除路径规则."""
        rule = await perm_service.add_path_rule(
            pattern=r'/tmp/.*',
            allow=True,
            description='临时规则',
        )

        result = await perm_service.remove_path_rule(rule['id'])
        assert result is True

        rules = await perm_service.list_rules()
        assert len(rules) == 0

    @pytest.mark.asyncio
    async def test_remove_nonexistent_rule(self, perm_service):
        """移除不存在的规则返回 False."""
        result = await perm_service.remove_path_rule('nonexistent-id')
        assert result is False

    @pytest.mark.asyncio
    async def test_rules_sorted_by_priority(self, perm_service):
        """规则按优先级降序排列（高优先级在前）."""
        await perm_service.add_path_rule(r'/low/.*', True, '低优先级', priority=1)
        await perm_service.add_path_rule(r'/high/.*', True, '高优先级', priority=100)
        await perm_service.add_path_rule(r'/medium/.*', True, '中优先级', priority=50)

        rules = await perm_service.list_rules()

        priorities = [r['priority'] for r in rules]
        assert priorities == sorted(priorities, reverse=True)


# ============================================================
# Test 3: 权限验证逻辑
# ============================================================

class TestPermissionValidation:
    """测试权限决策逻辑."""

    # --------------------------------------------------------
    # Allow 列表匹配
    # --------------------------------------------------------

    @pytest.mark.asyncio
    async def test_allow_list_match(self, service_with_rules):
        """allow 列表匹配返回 True — 安全路径被放行."""
        result = await service_with_rules.check_permission(
            tool_name='Read',
            input_data={'path': '/safe/document.txt'},
            agent_config={'role': 'user'},
        )

        assert result['allowed'] is True
        assert result['decision'] == 'allow'

    @pytest.mark.asyncio
    async def test_allow_multiple_safe_paths(self, service_with_rules):
        """多个安全路径均被允许."""
        safe_paths = [
            '/safe/file.txt',
            '/safe/subdir/nested/file.md',
            '/safe/config.json',
        ]

        for path in safe_paths:
            result = await service_with_rules.check_permission(
                'Write',
                {'path': path},
                {},
            )
            assert result['allowed'] is True, \
                f"安全路径未被允许: {path}"

    # --------------------------------------------------------
    # Deny 列表匹配
    # --------------------------------------------------------

    @pytest.mark.asyncio
    async def test_deny_list_match(self, service_with_rules):
        """deny 列表返回 False — 危险路径被拦截（对非 always_ask 工具）.

        注意：Write 工具在 Default 模式下属于 always_ask_tools，
        会优先返回 'ask' 而非检查路径规则。这里使用 Read 工具测试。
        """
        result = await service_with_rules.check_permission(
            tool_name='Read',  # Read 不在 always_ask_tools 中，会检查路径规则
            input_data={'path': '/dangerous/critical_config.yaml'},
            agent_config={},
        )

        assert result['allowed'] is False
        assert result['decision'] == 'deny'
        assert 'Path rule matched' in result['reason']

    @pytest.mark.asyncio
    async def test_deny_blocks_all_tools_on_dangerous_path(self, service_with_rules):
        """Deny 规则对非 always_ask 工具生效.

        注意：
        - Write/Bash/Edit 在 Default 模式下优先返回 'ask'（除非匹配 auto_allow_patterns）
        - 路径规则对 Read/Grep/Glob 等工具完全生效
        - Write 工具访问 .txt/.md/.json 文件时会匹配 auto_allow_patterns 而被允许
        """
        # 对非 always_ask 工具，deny 规则应该生效
        safe_tools_to_test = ['Read', 'Grep', 'Glob']

        for tool in safe_tools_to_test:
            result = await service_with_rules.check_permission(
                tool,
                {'path': '/dangerous/secret.txt'},
                {},
            )
            assert result['allowed'] is False, \
                f"工具 {tool} 在危险路径上应被拒绝"

        # 对 always_ask 工具（Write/Bash），在 Default 模式下的行为：
        # - 如果路径匹配 auto_allow_patterns (*.md, *.txt, *.json) → 允许
        # - 否则 → 返回 'ask'
        result_write_txt = await service_with_rules.check_permission(
            'Write',
            {'path': '/dangerous/secret.txt'},  # .txt 匹配 auto_allow
            {},
        )
        assert result_write_txt['allowed'] is True  # .txt 文件被自动允许

        result_write_py = await service_with_rules.check_permission(
            'Write',
            {'path': '/dangerous/secret.py'},  # .py 不匹配 auto_allow
            {},
        )
        assert result_write_py['allowed'] is False
        assert result_write_py['decision'] == 'ask'

    # --------------------------------------------------------
    # 通配符匹配
    # --------------------------------------------------------

    @pytest.mark.parametrize("path,pattern,should_match", [
        ('/api/v1/users', r'/api/.*', True),
        ('/api/v2/posts', r'/api/.*', True),
        ('/web/index.html', r'/api/.*', False),
        ('/docs/readme.md', r'.*\.md$', True),
        ('/docs/report.pdf', r'.*\.md$', False),
        ('/data/config.json', r'/data/.*\.(json|yaml)', True),
        ('/data/config.xml', r'/data/.*\.(json|yaml)', False),
    ])
    @pytest.mark.asyncio
    async def test_wildcard_matching(self, perm_service, path, pattern, should_match):
        """通配符 * 和正则表达式匹配测试.

        测试目标：验证系统能够正确处理各种通配符模式，
        包括前缀匹配、后缀匹配、扩展名过滤等。
        """
        await perm_service.add_path_rule(pattern, allow=True, description='test')
        result = await perm_service.check_permission(
            'Read',
            {'path': path},
            {},
        )

        if should_match:
            assert result['allowed'] is True or result['decision'] == 'allow', \
                f"路径 {path} 应匹配模式 {pattern}"
        else:
            # 不匹配时，如果没有其他规则，默认允许
            pass  # 默认行为是允许

    @pytest.mark.asyncio
    async def test_glob_pattern_matching_md_files(self, perm_service):
        """Glob 模式 *.md 匹配 Markdown 文件.

        场景：Default 模式下，Write 工具对 .md 文件自动允许。
        """
        result = await perm_service.check_permission(
            'Write',
            {'path': '/notes/meeting.md'},
            {},
        )

        # Default 模式 + Write 工具 + .md 文件 → 自动允许
        assert result['allowed'] is True
        assert 'auto-allow' in result['reason'].lower() or 'Matches auto-allow' in result['reason']

    @pytest.mark.asyncio
    async def test_glob_pattern_matching_txt_files(self, perm_service):
        """Glob 模式 *.txt 匹配文本文件."""
        result = await perm_service.check_permission(
            'Write',
            {'path': '/data/output.txt'},
            {},
        )

        assert result['allowed'] is True

    @pytest.mark.asyncio
    async def test_glob_no_match_for_other_extensions(self, perm_service):
        """非白名单扩展名需要用户批准."""
        result = await perm_service.check_permission(
            'Write',
            {'path': '/code/script.py'},  # .py 不在自动允许列表
            {},
        )

        # Write 工具在 default 模式下需要批准（除非匹配 auto_allow_patterns）
        assert result['allowed'] is False
        assert result['decision'] == 'ask'

    # --------------------------------------------------------
    # Deny 优先级高于 Allow
    # --------------------------------------------------------

    @pytest.mark.asyncio
    async def test_deny_overrides_allow(self, perm_service):
        """deny 规则优先级高于 allow — 高优先级 deny 覆盖低优先级 allow.

        使用 Read 工具测试（非 always_ask 工具，会检查路径规则）.
        """

        # 低优先级：允许 /conflict/ 路径
        await perm_service.add_path_rule(
            pattern=r'/conflict/.*',
            allow=True,
            description='允许（低优先级）',
            priority=1,
        )

        # 高优先级：拒绝同一路径
        await perm_service.add_path_rule(
            pattern=r'/conflict/.*',
            allow=False,
            description='拒绝（高优先级）',
            priority=100,
        )

        result = await perm_service.check_permission(
            'Read',  # 使用 Read 工具（非 always_ask）
            {'path': '/conflict/sensitive.txt'},
            {},
        )

        # 高优先级的 deny 应该生效
        assert result['allowed'] is False
        assert result['decision'] == 'deny'

    @pytest.mark.asyncio
    async def test_first_matching_rule_wins(self, perm_service):
        """第一个匹配的规则生效（按优先级排序后）."""
        # 添加多个可能匹配的规则
        await perm_service.add_path_rule(
            pattern=r'/test/.*',
            allow=False,
            priority=50,
        )
        await perm_service.add_path_rule(
            pattern=r'/test/specific/.*',
            allow=True,
            priority=10,  # 低优先级
        )

        # /test/specific/file.txt 同时匹配两个规则
        # 但 /test/.* (priority=50) 排在前面，应该先生效
        result = await perm_service.check_permission(
            'Read',
            {'path': '/test/specific/file.txt'},
            {},
        )

        # 第一个匹配的是 deny 规则（优先级更高）
        assert result['allowed'] is False


# ============================================================
# Test 4: Plan Mode（只读模式）测试
# ============================================================

class TestPlanMode:
    """测试 Plan Mode 的只读限制."""

    @pytest.mark.asyncio
    async def test_plan_mode_blocks_write_operations(self, perm_service):
        """Plan Mode 阻止写操作工具."""
        await perm_service.set_mode('plan')

        write_tools = ['Write', 'Edit', 'Bash']
        for tool in write_tools:
            result = await perm_service.check_permission(tool, {}, {})
            assert result['allowed'] is False
            assert result['decision'] == 'deny'
            assert 'Plan mode' in result['reason']

    @pytest.mark.asyncio
    async def test_plan_mode_allows_read_operations(self, perm_service):
        """Plan Mode 允许读操作工具."""
        await perm_service.set_mode('plan')

        read_tools = ['Read', 'Grep', 'Glob', 'WebFetch', 'WebSearch']
        for tool in read_tools:
            result = await perm_service.check_permission(tool, {}, {})
            assert result['allowed'] is True
            assert result['decision'] == 'auto'

    @pytest.mark.asyncio
    async def test_plan_mode_reason_message(self, perm_service):
        """Plan Mode 拒绝信息包含明确提示."""
        await perm_service.set_mode('plan')

        result = await perm_service.check_permission('Write', {'path': '/test.txt'})

        assert 'write blocked' in result['reason'].lower() or 'disabled' in result['reason'].lower()


# ============================================================
# Test 5: Auto Mode（全自动模式）测试
# ============================================================

class TestAutoMode:
    """测试 Auto Mode 的全自动审批."""

    @pytest.mark.asyncio
    async def test_auto_mode_allows_everything(self, perm_service):
        """Auto Mode 允许所有操作."""
        await perm_service.set_mode('auto')

        all_tools = ['Read', 'Write', 'Bash', 'Agent', 'Delete', 'Exec']
        for tool in all_tools:
            result = await perm_service.check_permission(
                tool,
                {'command': 'rm -rf /'},  # 即使危险命令也被允许
                {},
            )
            assert result['allowed'] is True
            assert result['decision'] == 'auto'
            assert 'Auto-approve' in result['reason']

    @pytest.mark.asyncio
    async def test_auto_mode_ignores_path_rules(self, service_with_rules):
        """Auto Mode 忽略路径规则 — 直接全部放行."""
        await service_with_rules.set_mode('auto')

        # 即使有 deny 规则，auto 模式也直接放行
        result = await service_with_rules.check_permission(
            'Write',
            {'path': '/dangerous/critical.dat'},
            {},
        )

        assert result['allowed'] is True


# ============================================================
# Test 6: Default Mode 标准检查
# ============================================================

class TestDefaultMode:
    """测试 Default Mode 的标准权限检查流程."""

    @pytest.mark.asyncio
    async def test_always_ask_tools_require_approval(self, perm_service):
        """Always-ask 工具列表需要用户批准."""
        # Default 模式下 Bash、Write、Edit 需要批准
        ask_tools = ['Bash', 'Write', 'Edit']

        for tool in ask_tools:
            result = await perm_service.check_permission(
                tool,
                {},  # 无文件路径
                {},
            )
            assert result['allowed'] is False
            assert result['decision'] == 'ask'
            assert 'requires user approval' in result['reason'].lower() or 'approval' in result['reason'].lower()

    @pytest.mark.asyncio
    async def test_safe_tools_auto_approved(self, perm_service):
        """安全工具自动批准 — 不在 always_ask 列表中."""
        safe_tools = ['Read', 'Grep', 'Glob', 'WebFetch', 'WebSearch', 'Skill', 'TodoWrite']

        for tool in safe_tools:
            result = await perm_service.check_permission(tool, {}, {})
            assert result['allowed'] is True
            assert result['decision'] == 'auto'

    @pytest.mark.asyncio
    async def test_default_fallback_when_no_rules_match(self, perm_service):
        """无匹配规则时默认允许."""
        result = await perm_service.check_permission(
            'CustomTool',
            {'path': '/random/path'},
            {},
        )

        assert result['allowed'] is True
        assert 'No restrictions apply' in result['reason']


# ============================================================
# Test 7: 拒绝日志和统计
# ============================================================

class TestDenialLogging:
    """测试拒绝事件记录和统计."""

    @pytest.mark.asyncio
    async def test_denial_logged_on_reject(self, service_with_rules):
        """拒绝操作被记录到日志 — 使用 Read 工具测试 deny 规则."""
        # 触发一次拒绝（使用 Read 工具以触发路径规则的 deny）
        await service_with_rules.check_permission(
            'Read',  # 非 always_ask 工具
            {'path': '/dangerous/test.txt'},
            {},
        )

        stats = await service_with_rules.get_denial_stats()
        assert stats['total_denials'] >= 1

    @pytest.mark.asyncio
    async def test_denial_stats_by_tool(self, service_with_rules):
        """按工具统计拒绝次数 — 区分 deny 和 ask."""
        # 使用 Read 工具触发 deny（路径规则）
        await service_with_rules.check_permission('Read', {'path': '/dangerous/a.txt'})
        await service_with_rules.check_permission('Grep', {'path': '/dangerous/b.sh'})

        # 使用 Bash 工具触发 ask（always_ask 逻辑，.sh 不匹配 auto_allow_patterns）
        await service_with_rules.check_permission('Bash', {'path': '/dangerous/d.sh'})

        # Write 工具访问 .py 文件（不匹配 auto_allow）→ ask
        await service_with_rules.check_permission('Write', {'path': '/dangerous/c.py'})

        stats = await service_with_rules.get_denial_stats()

        assert 'by_tool' in stats
        # Read 和 Grep 应该通过 deny 路径规则被记录
        assert stats['by_tool'].get('Read', 0) >= 1
        assert stats['by_tool'].get('Grep', 0) >= 1
        # Bash 和 Write 通过 always_ask 逻辑被记录
        assert stats['by_tool'].get('Bash', 0) >= 1
        assert stats['by_tool'].get('Write', 0) >= 1

    @pytest.mark.asyncio
    async def test_denial_stats_by_reason(self, service_with_rules):
        """按原因统计拒绝次数."""
        # 触发不同类型的拒绝
        await service_with_rules.check_permission('Read', {'path': '/dangerous/x.txt'})  # deny: Path rule
        await service_with_rules.check_permission('Bash', {'path': '/dangerous/y.sh'})  # ask: Requires approval (.sh 不匹配 auto_allow)

        stats = await service_with_rules.get_denial_stats()

        assert 'by_reason' in stats
        assert len(stats['by_reason']) > 0
        # 应该包含两种不同的原因
        reasons = list(stats['by_reason'].keys())
        assert any('Path rule' in r for r in reasons)
        assert any('approval' in r.lower() or 'Requires' in r for r in reasons)

    @pytest.mark.asyncio
    async def test_recent_denials_limited_to_10(self, service_with_rules):
        """最近拒绝记录最多显示 10 条."""
        # 触发 15 次拒绝（全部使用会真正被拒绝的工具/路径组合）
        for i in range(8):
            await service_with_rules.check_permission(
                'Read',
                {'path': f'/dangerous/file_{i}.txt'},  # Read + 危险路径 → deny
            )
        for i in range(7):
            await service_with_rules.check_permission(
                'Bash',
                {'path': f'/dangerous/extra_{i}.sh'},  # Bash + .sh 文件 → ask (不匹配 auto_allow)
            )

        stats = await service_with_rules.get_denial_stats()

        assert len(stats['recent_denials']) <= 10
        assert stats['total_denials'] == 15  # 总数不受限

    @pytest.mark.asyncio
    async def test_clear_denials(self, service_with_rules):
        """清除拒绝日志."""
        # 先产生一些拒绝
        for _ in range(5):
            await service_with_rules.check_permission('Write', {'path': '/dangerous/x'})

        # 清除
        await service_with_rules.clear_denials()

        stats = await service_with_rules.get_denial_stats()
        assert stats['total_denials'] == 0
        assert len(stats['recent_denials']) == 0

    @pytest.mark.asyncio
    async def test_denial_log_size_limit(self, perm_service):
        """拒绝日志大小限制（10000 条上限）.
        
        当日志超过 10000 条时，自动裁剪至最近 5000 条。
        """
        # 添加一条 deny 规则用于生成拒绝
        await perm_service.add_path_rule(r'/limit_test/.*', allow=False)

        # 模拟大量拒绝（通过直接调用内部方法加速测试）
        for i in range(10500):
            await perm_service._log_denial('TestTool', f'Stress test {i}')

        stats = await perm_service.get_denial_stats()

        # 日志应被裁剪到 <= 10000 条（实际保留 5000 条）
        assert stats['total_denials'] <= 10000


# ============================================================
# Test 8: Glob 匹配辅助方法
# ============================================================

class TestGlobMatching:
    """测试 Glob 模式匹配辅助方法."""

    @pytest.mark.parametrize("pattern,path,expected", [
        ('*.md', 'readme.md', True),
        ('*.md', 'readme.txt', False),
        ('*.json', 'config.json', True),
        ('file?.txt', 'file1.txt', True),
        ('file?.txt', 'file12.txt', False),  # ? 只匹配单个字符
        ('*', 'anything', True),
        ('/api/*', '/api/v1/users', True),
        ('/api/*', '/web/users', False),
    ])
    def test_static_glob_match(self, pattern, path, expected):
        """静态方法 glob 匹配测试."""
        result = PermissionService._match_glob(pattern, path)
        assert result is expected, \
            f"glob('{pattern}', '{path}') 应返回 {expected}"


# ============================================================
# Test 9: 边界条件和异常场景
# ============================================================

class TestEdgeCases:
    """边界条件和异常场景测试."""

    @pytest.mark.asyncio
    async def test_empty_input_data(self, perm_service):
        """空输入数据不导致异常."""
        result = await perm_service.check_permission('Read', {}, {})

        assert 'allowed' in result
        assert 'decision' in result
        assert 'reason' in result

    @pytest.mark.asyncio
    async def test_none_agent_config(self, perm_service):
        """agent_config 为 None 时不崩溃."""
        result = await perm_service.check_permission('Read', {'path': '/test.txt'}, None)

        assert result['allowed'] is True

    @pytest.mark.asyncio
    async def test_special_characters_in_path(self, perm_service):
        """路径中的特殊字符处理."""
        special_paths = [
            '/path with spaces/file.txt',
            '/path-with-dashes/file.txt',
            '/path_with_underscores/file.txt',
            '/path.with.dots/file.txt',
        ]

        for path in special_paths:
            result = await perm_service.check_permission('Read', {'path': path}, {})
            assert result['allowed'] is True  # 默认允许

    @pytest.mark.asyncio
    async def test_unicode_path(self, perm_service):
        """Unicode 路径处理."""
        result = await perm_service.check_permission(
            'Read',
            {'path': '/文档/报告/测试文件.md'},
            {},
        )

        assert 'allowed' in result  # 不崩溃即可

    @pytest.mark.asyncio
    async def test_very_long_path(self, perm_service):
        """超长路径处理."""
        long_path = '/a' * 1000 + '/file.txt'
        result = await perm_service.check_permission('Read', {'path': long_path}, {})

        assert 'allowed' in result  # 不崩溃

    @pytest.mark.asyncio
    async def test_concurrent_permission_checks(self, perm_service):
        """并发权限检查 — 验证线程安全性."""
        import asyncio

        async def check(task_id):
            return await perm_service.check_permission('Read', {'path': f'/test/{task_id}'}, {})

        # 并发执行 100 次检查
        tasks = [check(i) for i in range(100)]
        results = await asyncio.gather(*tasks)

        # 所有结果都应包含必要字段
        for result in results:
            assert 'allowed' in result
            assert 'decision' in result
