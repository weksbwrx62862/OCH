"""Skill Service 单元测试 — 验证技能管理核心业务逻辑."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile

from app.services.skill_service import SkillService


@pytest.fixture
def skill_service():
    """创建 SkillService 实例（每次测试独立）."""
    return SkillService()


class TestListSkills:
    """测试列出技能功能."""

    @pytest.mark.asyncio
    async def test_list_skills_returns_builtin(self, skill_service):
        """列出技能应包含内置技能."""
        skills = await skill_service.list_skills()

        assert len(skills) >= 4  # 至少包含 commit, review, debug, plan
        builtin_names = {s['name'] for s in skills}
        assert 'commit' in builtin_names
        assert 'review' in builtin_names
        assert 'debug' in builtin_names
        assert 'plan' in builtin_names

    @pytest.mark.asyncio
    async def test_list_skills_unique_names(self, skill_service):
        """返回的技能列表应去重（按名称）."""
        skills = await skill_service.list_skills()
        names = [s['name'] for s in skills]

        # 验证无重复名称
        assert len(names) == len(set(names))

    @pytest.mark.asyncio
    async def test_list_skills_with_search(self, skill_service):
        """搜索过滤应正确工作."""
        # 搜索 "commit"
        results = await skill_service.list_skills(search='commit')

        assert all(
            'commit' in s['name'].lower() or 'commit' in s.get('description', '').lower()
            for s in results
        )

    @pytest.mark.asyncio
    async def test_list_skills_with_category_filter(self, skill_service):
        """分类过滤应正确工作."""
        development_skills = await skill_service.list_skills(category='development')

        assert all(s.get('category') == 'development' for s in development_skills)
        assert len(development_skills) >= 3  # commit, review, debug

    @pytest.mark.asyncio
    async def test_list_skills_enabled_only(self, skill_service):
        """仅启用过滤应返回 enabled=True 的技能."""
        enabled_skills = await skill_service.list_skills(enabled_only=True)

        assert all(s.get('enabled', True) is True for s in enabled_skills)


class TestGetSkill:
    """测试获取单个技能详情."""

    @pytest.mark.asyncio
    async def test_get_builtin_skill(self, skill_service):
        """获取内置技能应返回完整信息."""
        skill = await skill_service.get_skill('commit')

        assert skill is not None
        assert skill['name'] == 'commit'
        assert 'content_md' in skill
        assert 'triggers' in skill
        assert 'dependencies' in skill

    @pytest.mark.asyncio
    async def test_get_nonexistent_skill(self, skill_service):
        """获取不存在的技能应返回 None."""
        skill = await skill_service.get_skill('nonexistent-skill-xyz')

        assert skill is None

    @pytest.mark.asyncio
    async def test_get_skill_returns_consistent_result(self, skill_service):
        """多次获取同一技能应返回相同结果."""
        skill1 = await skill_service.get_skill('debug')
        skill2 = await skill_service.get_skill('debug')
        skill3 = await skill_service.get_skill('debug')

        assert skill1 is not None
        assert skill2 is not None
        assert skill3 is not None
        # 所有返回值应相等
        assert skill1['name'] == skill2['name'] == skill3['name']


class TestParseSkillFile:
    """测试解析 Markdown 技能文件."""

    @pytest.mark.asyncio
    async def test_parse_skill_file_with_frontmatter(self, skill_service):
        """解析带 frontmatter 的 Markdown 文件."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
name: test-skill
description: 测试技能描述
category: test
version: 2.0.0
---

# 技能内容

这是一个测试用的 Markdown 技能文件。
""")
            f.flush()
            path = Path(f.name)

        try:
            result = await skill_service._parse_skill_file(path)

            assert result is not None
            assert result['name'] == 'test-skill'
            assert result['description'] == '测试技能描述'
            assert result['category'] == 'test'
            assert result['version'] == '2.0.0'
            assert '# 技能内容' in result['content_md']
        finally:
            path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_parse_skill_file_without_frontmatter(self, skill_service):
        """解析无 frontmatter 的 Markdown 文件（使用文件名作为名称）."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write('# 简单技能\n\n无 frontmatter 的简单内容。')
            f.flush()
            path = Path(f.name)

        try:
            result = await skill_service._parse_skill_file(path)

            assert result is not None
            assert result['name'] == path.stem  # 使用文件名作为默认名称
            assert '# 简单技能' in result['content_md']
        finally:
            path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_parse_nonexistent_file(self, skill_service):
        """解析不存在的文件应返回 None."""
        result = await skill_service._parse_skill_file(Path('/nonexistent/path/skill.md'))

        assert result is None


class TestInstallSkill:
    """测试安装技能功能."""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_install_from_url(self, mock_client_class, skill_service):
        """从 URL 安装技能."""
        # 配置 mock HTTP 客户端
        mock_response = MagicMock()
        mock_response.text = """---
name: url-skill
description: 从 URL 安装的技能
---

# URL 技能内容
"""
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client_instance

        # mock aiofiles 模块（避免 ModuleNotFoundError）
        with patch.dict('sys.modules', {'aiofiles': MagicMock()}), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'mkdir'), \
             patch('builtins.open', MagicMock()):
            result = await skill_service.install_skill(
                source='https://example.com/skill.md',
                source_type='url'
            )

            # 验证安装成功（result 可能是 dict 或 None，取决于实现细节）
            assert result is not None

    @pytest.mark.asyncio
    async def test_install_unsupported_source_type(self, skill_service):
        """不支持的安装类型应抛出 ValueError."""
        # mock aiofiles 以避免导入错误
        with patch.dict('sys.modules', {'aiofiles': MagicMock()}):
            with pytest.raises(ValueError, match='Unsupported source type'):
                await skill_service.install_skill(
                    source='some-source',
                    source_type='invalid_type'
                )


class TestUninstallSkill:
    """测试卸载技能功能."""

    @pytest.mark.asyncio
    async def test_uninstall_existing_skill(self, skill_service):
        """卸载存在的技能应返回 True."""
        # 创建临时技能文件
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_path = Path(tmpdir) / 'test-uninstall.md'
            skill_path.write_text('---\nname: test-uninstall\n---\n# 内容')

            # 临时替换 SKILLS_DIRS（模块级变量）
            from app.services.skill_service import SKILLS_DIRS
            original_dirs = SKILLS_DIRS.copy()
            SKILLS_DIRS.clear()
            SKILLS_DIRS.append(Path(tmpdir))

            try:
                result = await skill_service.uninstall_skill('test-uninstall')

                assert result is True
                assert skill_path.exists() is False
            finally:
                # 恢复原始值
                SKILLS_DIRS.clear()
                SKILLS_DIRS.extend(original_dirs)

    @pytest.mark.asyncio
    async def test_uninstall_nonexistent_skill(self, skill_service):
        """卸载不存在的技能应返回 False."""
        result = await skill_service.uninstall_skill('nonexistent-skill-xyz')

        assert result is False


class TestEnableDisableSkill:
    """测试启用/禁用技能功能."""

    @pytest.mark.asyncio
    async def test_enable_skill_returns_true(self, skill_service):
        """启用技能应返回 True（TODO 实现）."""
        result = await skill_service.enable_skill('some-skill')

        assert result is True

    @pytest.mark.asyncio
    async def test_disable_skill_returns_true(self, skill_service):
        """禁用技能应返回 True（TODO 实现）."""
        result = await skill_service.disable_skill('some-skill')

        assert result is True


class TestBuiltinSkills:
    """测试内置技能定义."""

    @pytest.mark.asyncio
    async def test_builtin_skills_structure(self, skill_service):
        """验证内置技能的数据结构完整性."""
        builtin_skills = skill_service._get_builtin_skills()

        assert isinstance(builtin_skills, list)
        assert len(builtin_skills) >= 4

        required_fields = ['name', 'description', 'category', 'enabled', 'source', 'content_md', 'triggers', 'dependencies']

        for skill in builtin_skills:
            for field in required_fields:
                assert field in skill, f"缺少必需字段: {field}"

    @pytest.mark.asyncio
    async def test_builtin_skills_categories(self, skill_service):
        """验证内置技能的分类分布."""
        builtin_skills = skill_service._get_builtin_skills()
        categories = {s['category'] for s in builtin_skills}

        assert 'development' in categories
        assert 'planning' in categories

    @pytest.mark.asyncio
    async def test_builtin_skills_all_enabled(self, skill_service):
        """所有内置技能默认启用."""
        builtin_skills = skill_service._get_builtin_skills()

        assert all(s.get('enabled') is True for s in builtin_skills)


class TestEdgeCases:
    """边界条件测试."""

    @pytest.mark.asyncio
    async def test_empty_search_string(self, skill_service):
        """空搜索字符串应返回全部技能."""
        all_skills = await skill_service.list_skills()
        empty_search_skills = await skill_service.list_skills(search='')

        assert len(all_skills) == len(empty_search_skills)

    @pytest.mark.asyncio
    async def test_case_insensitive_search(self, skill_service):
        """搜索应大小写不敏感."""
        upper_results = await skill_service.list_skills(search='COMMIT')
        lower_results = await skill_service.list_skills(search='commit')

        assert len(upper_results) == len(lower_results)

    @pytest.mark.asyncio
    async def test_get_multiple_times_same_skill(self, skill_service):
        """多次获取同一技能应返回相同结果."""
        skill1 = await skill_service.get_skill('debug')
        skill2 = await skill_service.get_skill('debug')
        skill3 = await skill_service.get_skill('debug')

        assert skill1 == skill2 == skill3
