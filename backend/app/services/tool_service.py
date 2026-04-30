"""Tool Service — manages tool registry and execution."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from openharness.tools import ToolRegistry

logger = logging.getLogger(__name__)


class ToolService:
    """工具服务 — 管理和查询 OpenHarness 的 43+ 工具."""

    def __init__(self):
        self._registry: Optional[ToolRegistry] = None

    @property
    def registry(self) -> ToolRegistry:
        """懒加载工具注册表."""
        if self._registry is None:
            try:
                from openharness.tools import get_default_tool_registry
                self._registry = get_default_tool_registry()
                logger.info("Tool registry loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load tool registry: {e}, using fallback")
                self._registry = FallbackToolRegistry()
        return self._registry

    async def list_tools(
        self,
        category: Optional[str] = None,
        include_dangerous: bool = True,
    ) -> List[Dict[str, Any]]:
        """列出所有可用工具."""
        tools = []

        for tool_name in self.registry.list_tools():
            tool_info = self.registry.get_tool_info(tool_name)
            if not tool_info:
                continue

            if category and tool_info.get('category') != category:
                continue

            if tool_info.get('dangerous') and not include_dangerous:
                continue

            tools.append({
                'name': tool_name,
                **tool_info,
            })

        return tools

    async def get_tool_detail(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具详细信息."""
        return self.registry.get_tool_info(tool_name)

    async def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具输入 Schema (JSON Schema)."""
        return self.registry.get_schema(tool_name)

    async def get_categories(self) -> List[Dict[str, Any]]:
        """获取工具分类列表."""
        categories = {}
        tools = await self.list_tools(include_dangerous=True)

        for tool in tools:
            cat = tool.get('category', 'other')
            if cat not in categories:
                categories[cat] = {'id': cat, 'name': cat.replace('_', ' ').title(), 'count': 0}
            categories[cat]['count'] += 1

        return sorted(categories.values(), key=lambda x: x['id'])

    async def execute_tool(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        session_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        执行工具.

        Returns:
            {
                'output': str,
                'is_error': bool,
                'duration_ms': int,
            }
        """
        start_time = time.time()

        try:
            # 权限检查
            permission_check = await self.check_permission(tool_name, input_data, session_context)
            if not permission_check['allowed']:
                return {
                    'output': '',
                    'is_error': True,
                    'duration_ms': int((time.time() - start_time) * 1000),
                    'permission_decision': 'denied',
                    'reason': permission_check.get('reason', 'Permission denied'),
                }

            # 执行工具
            output = await self.registry.execute(tool_name, input_data)

            return {
                'output': output,
                'is_error': False,
                'duration_ms': int((time.time() - start_time) * 1000),
                'permission_decision': permission_check.get('decision', 'allowed'),
            }

        except Exception as e:
            logger.exception(f"Tool execution error: {tool_name}")
            return {
                'output': str(e),
                'is_error': True,
                'duration_ms': int((time.time() - start_time) * 1000),
            }

    async def check_permission(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """检查工具执行权限."""
        # TODO: 实现完整的权限检查逻辑
        # 包括：路径规则、命令白名单、YOLO 分类器等

        tool_info = await self.get_tool_detail(tool_name)

        if not tool_info:
            return {'allowed': False, 'reason': f'Tool {tool_name} not found'}

        # 基础危险工具检查
        if tool_info.get('dangerous'):
            return {
                'allowed': False,
                'decision': 'ask',
                'reason': f'Tool {tool_name} requires approval',
            }

        return {'allowed': True, 'decision': 'auto'}

    async def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """搜索工具."""
        all_tools = await self.list_tools()
        query_lower = query.lower()

        results = []
        for tool in all_tools:
            name_match = query_lower in tool['name'].lower()
            desc_match = query_lower in tool.get('description', '').lower()

            if name_match or desc_match:
                score = 2 if name_match else 1
                results.append({**tool, '_relevance_score': score})

        results.sort(key=lambda x: x['_relevance_score'], reverse=True)
        return results


class FallbackToolRegistry:
    """Fallback 工具注册表 — 当 OpenHarness 无法加载时使用."""

    FALLBACK_TOOLS = {
        'Bash': {'description': 'Execute shell commands', 'category': 'file_io', 'dangerous': True},
        'Read': {'description': 'Read file contents', 'category': 'file_io', 'dangerous': False},
        'Write': {'description': 'Write to files', 'category': 'file_io', 'dangerous': False},
        'Grep': {'description': 'Search text in files', 'category': 'file_io', 'dangerous': False},
        'Glob': {'description': 'Find files by pattern', 'category': 'file_io', 'dangerous': False},
        'WebFetch': {'description': 'Fetch URL contents', 'category': 'web', 'dangerous': False},
        'WebSearch': {'description': 'Search the web', 'category': 'web', 'dangerous': False},
        'Agent': {'description': 'Spawn sub-agent', 'category': 'agent', 'dangerous': True},
        'Skill': {'description': 'Load skill from .md file', 'category': 'meta', 'dangerous': False},
        'TodoWrite': {'description': 'Manage todo list', 'category': 'meta', 'dangerous': False},
    }

    def list_tools(self) -> List[str]:
        return list(self.FALLBACK_TOOLS.keys())

    def get_tool_info(self, name: str) -> Optional[Dict]:
        return self.FALLBACK_TOOLS.get(name)

    def get_schema(self, name: str) -> Optional[Dict]:
        return None

    async def execute(self, name: str, input_data: Dict) -> str:
        return f"Fallback: Tool '{name}' not fully implemented"
