"""Skill Service — manage .md knowledge base skills."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 技能目录配置
SKILLS_DIRS = [
    Path.home() / '.och' / 'skills',
    Path.home() / '.openclaw' / 'skills',
]


class SkillService:
    """技能服务 — 管理 Markdown 知识库技能."""

    def __init__(self):
        self._skill_cache: Dict[str, Dict] = {}

    async def list_skills(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """列出所有已安装技能."""
        skills = []

        # 从文件系统加载
        for skills_dir in SKILLS_DIRS:
            if skills_dir.exists():
                for md_file in skills_dir.glob('*.md'):
                    skill_info = await self._parse_skill_file(md_file)
                    if skill_info:
                        skills.append(skill_info)

        # 内置技能
        builtin_skills = self._get_builtin_skills()
        skills.extend(builtin_skills)

        # 过滤
        if search:
            search_lower = search.lower()
            skills = [
                s for s in skills
                if search_lower in s['name'].lower()
                or search_lower in s.get('description', '').lower()
            ]

        if category:
            skills = [s for s in skills if s.get('category') == category]

        if enabled_only:
            skills = [s for s in skills if s.get('enabled', True)]

        # 去重（按名称）
        seen = set()
        unique_skills = []
        for s in skills:
            if s['name'] not in seen:
                seen.add(s['name'])
                unique_skills.append(s)

        return unique_skills

    async def get_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """获取技能详情（含 Markdown 内容）."""
        # 先从缓存查找
        if skill_name in self._skill_cache:
            return self._skill_cache[skill_name]

        # 从文件系统查找
        for skills_dir in SKILLS_DIRS:
            skill_file = skills_dir / f'{skill_name}.md'
            if skill_file.exists():
                skill_info = await self._parse_skill_file(skill_file)
                if skill_info:
                    self._skill_cache[skill_name] = skill_info
                    return skill_info

        # 查找内置技能
        for skill in self._get_builtin_skills():
            if skill['name'] == skill_name:
                return skill

        return None

    async def install_skill(
        self,
        source: str,
        source_type: str = 'url',
    ) -> Dict[str, Any]:
        """安装新技能."""
        import aiofiles
        import httpx

        target_dir = SKILLS_DIRS[0]
        target_dir.mkdir(parents=True, exist_ok=True)

        if source_type == 'url':
            async with httpx.AsyncClient() as client:
                response = await client.get(source)
                content = response.text

            filename = source.split('/')[-1].replace('.md', '') + '.md'
            target_path = target_dir / filename

            async with aiofiles.open(target_path, 'w') as f:
                await f.write(content)

        elif source_type == 'file':
            source_path = Path(source)
            if not source_path.exists():
                raise FileNotFoundError(f"Source file not found: {source}")

            target_path = target_dir / source_path.name
            import shutil
            shutil.copy2(source_path, target_path)

        else:
            raise ValueError(f"Unsupported source type: {source_type}")

        skill_info = await self._parse_skill_file(target_path)
        if skill_info:
            self._skill_cache[skill_info['name']] = skill_info

        return skill_info or {'name': target_path.stem, 'source': str(target_path)}

    async def uninstall_skill(self, skill_name: str) -> bool:
        """卸载技能."""
        for skills_dir in SKILLS_DIRS:
            skill_file = skills_dir / f'{skill_name}.md'
            if skill_file.exists():
                skill_file.unlink()
                if skill_name in self._skill_cache:
                    del self._skill_cache[skill_name]
                return True

        return False

    async def enable_skill(self, skill_name: str) -> bool:
        """启用技能."""
        # TODO: 实现启用逻辑（如创建软链接或修改状态）
        return True

    async def disable_skill(self, skill_name: str) -> bool:
        """禁用技能."""
        # TODO: 实现禁用逻辑
        return True

    async def _parse_skill_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """解析技能 Markdown 文件."""
        import re

        try:
            content = path.read_text(encoding='utf-8')
        except Exception as e:
            logger.warning(f"Failed to read skill file {path}: {e}")
            return None

        # 解析 frontmatter
        frontmatch = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        meta = {}

        if frontmatch:
            yaml_content = frontmatch.group(1)
            for line in yaml_content.split('\n'):
                if ':' in line:
                    key, _, value = line.partition(':')
                    meta[key.strip()] = value.strip().strip('"').strip("'")

        body = content[frontmatch.end():] if frontmatch else content

        return {
            'name': meta.get('name', path.stem),
            'description': meta.get('description', ''),
            'category': meta.get('category', 'general'),
            'version': meta.get('version', '1.0.0'),
            'enabled': meta.get('enabled', True),
            'source': 'file',
            'path': str(path),
            'triggers': meta.get('triggers', '').split(',') if meta.get('triggers') else [],
            'dependencies': meta.get('dependencies', '').split(',') if meta.get('dependencies') else [],
            'content_md': body.strip(),
            'usage_count': 0,
        }

    def _get_builtin_skills(self) -> List[Dict[str, Any]]:
        """获取内置技能定义."""
        return [
            {
                'name': 'commit',
                'description': 'Create clean git commits with proper formatting',
                'category': 'development',
                'enabled': True,
                'source': 'builtin',
                'content_md': '# Commit Skill\n\nHelp users create clean commits.',
                'triggers': ['commit this', 'git commit'],
                'dependencies': ['Bash'],
            },
            {
                'name': 'review',
                'description': 'Systematic code review for bugs and quality',
                'category': 'development',
                'enabled': True,
                'source': 'builtin',
                'content_md': '# Review Skill\n\nReview code systematically.',
                'triggers': ['review this', 'code review'],
                'dependencies': ['Read', 'Grep'],
            },
            {
                'name': 'debug',
                'description': 'Diagnose and fix bugs step-by-step',
                'category': 'development',
                'enabled': True,
                'source': 'builtin',
                'content_md': '# Debug Skill\n\nDebug issues methodically.',
                'triggers': ['debug this', 'fix bug'],
                'dependencies': ['Read', 'Grep', 'Bash'],
            },
            {
                'name': 'plan',
                'description': 'Design implementation plan before coding',
                'category': 'planning',
                'enabled': True,
                'source': 'builtin',
                'content_md': '# Plan Skill\n\nPlan before implementing.',
                'triggers': ['plan this', 'design approach'],
                'dependencies': ['Glob', 'Read'],
            },
        ]
