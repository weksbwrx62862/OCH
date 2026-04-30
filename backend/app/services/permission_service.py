"""Permission Service — RBAC and path-based access control."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 权限模式定义
PERMISSION_MODES = {
    'default': {
        'description': 'Ask before write/execute operations',
        'auto_allow_patterns': ['*.md', '*.txt', '*.json'],
        'always_ask_tools': ['Bash', 'Write', 'Edit'],
    },
    'auto': {
        'description': 'Allow all operations (sandboxed)',
        'auto_allow_all': True,
    },
    'plan': {
        'description': 'Block all writes, read-only mode',
        'block_write_operations': True,
        'allowed_read_tools': ['Read', 'Grep', 'Glob', 'WebFetch', 'WebSearch'],
    },
}


class PermissionService:
    """权限管理服务 — 多级权限控制."""

    def __init__(self):
        self._path_rules: List[Dict[str, Any]] = []
        self._denial_log: List[Dict[str, Any]] = []
        self._current_mode = 'default'

    async def get_modes(self) -> List[Dict[str, Any]]:
        """获取可用权限模式."""
        return [
            {'id': k, **v} for k, v in PERMISSION_MODES.items()
        ]

    async def get_current_mode(self) -> str:
        """获取当前权限模式."""
        return self._current_mode

    async def set_mode(self, mode: str) -> bool:
        """设置权限模式."""
        if mode not in PERMISSION_MODES:
            raise ValueError(f"Invalid permission mode: {mode}")
        self._current_mode = mode
        return True

    async def add_path_rule(
        self,
        pattern: str,
        allow: bool = True,
        description: str = '',
        priority: int = 0,
    ) -> Dict[str, Any]:
        """添加路径规则."""
        rule = {
            'id': f"rule_{len(self._path_rules)}",
            'pattern': pattern,
            'allow': allow,
            'description': description,
            'priority': priority,
            'compiled_pattern': re.compile(pattern),
        }
        self._path_rules.append(rule)
        # 按优先级排序
        self._path_rules.sort(key=lambda x: x['priority'], reverse=True)
        return rule

    async def remove_path_rule(self, rule_id: str) -> bool:
        """移除路径规则."""
        original_len = len(self._path_rules)
        self._path_rules = [r for r in self._path_rules if r['id'] != rule_id]
        return len(self._path_rules) < original_len

    async def list_rules(self) -> List[Dict[str, Any]]:
        """列出所有路径规则."""
        return [
            {k: v for k, v in r.items() if k != 'compiled_pattern'}
            for r in self._path_rules
        ]

    async def check_permission(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        agent_config: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        检查工具执行权限.

        Returns:
            {
                'allowed': bool,
                'decision': str (auto/allow/deny/ask),
                'reason': str,
            }
        """
        mode_config = PERMISSION_MODES.get(self._current_mode, {})

        # Plan Mode: 阻止所有写操作
        if self._current_mode == 'plan':
            allowed_read = mode_config.get('allowed_read_tools', [])
            if tool_name not in allowed_read:
                await self._log_denial(tool_name, 'Plan mode - write blocked')
                return {
                    'allowed': False,
                    'decision': 'deny',
                    'reason': 'Plan mode is active. Write operations are disabled.',
                }

        # Auto Mode: 允许所有操作
        if self._current_mode == 'auto':
            return {'allowed': True, 'decision': 'auto', 'reason': 'Auto-approve mode'}

        # Default Mode: 标准检查
        always_ask = mode_config.get('always_ask_tools', [])

        if tool_name in always_ask:
            # 检查是否匹配自动允许模式
            auto_allow_patterns = mode_config.get('auto_allow_patterns', [])
            file_path = input_data.get('path') or input_data.get('file')

            if file_path and any(
                self._match_glob(pattern, file_path)
                for pattern in auto_allow_patterns
            ):
                return {'allowed': True, 'decision': 'auto', 'reason': 'Matches auto-allow pattern'}

            await self._log_denial(tool_name, 'Requires user approval')
            return {
                'allowed': False,
                'decision': 'ask',
                'reason': f'Tool "{tool_name}" requires user approval.',
            }

        # 检查自定义路径规则
        for rule in self._path_rules:
            file_path = input_data.get('path') or input_data.get('cwd') or ''
            if rule['compiled_pattern'].search(file_path):
                decision = 'allow' if rule['allow'] else 'deny'
                if not rule['allow']:
                    await self._log_denial(tool_name, f'Path rule: {rule["pattern"]}')
                return {
                    'allowed': rule['allow'],
                    'decision': decision,
                    'reason': f'Path rule matched: {rule["pattern"]}',
                }

        # 默认允许
        return {'allowed': True, 'decision': 'auto', 'reason': 'No restrictions apply'}

    async def get_denial_stats(self) -> Dict[str, Any]:
        """获取拒绝统计."""
        by_tool: Dict[str, int] = {}
        by_reason: Dict[str, int] = {}

        for denial in self._denial_log:
            tool = denial.get('tool_name', 'unknown')
            reason = denial.get('reason', 'unknown')
            by_tool[tool] = by_tool.get(tool, 0) + 1
            by_reason[reason] = by_reason.get(reason, 0) + 1

        return {
            'total_denials': len(self._denial_log),
            'by_tool': dict(sorted(by_tool.items(), key=lambda x: x[1], reverse=True)),
            'by_reason': dict(sorted(by_reason.items(), key=lambda x: x[1], reverse=True)),
            'recent_denials': self._denial_log[-10:] if self._denial_log else [],
        }

    async def clear_denials(self) -> None:
        """清除拒绝记录."""
        self._denial_log.clear()

    async def _log_denial(self, tool_name: str, reason: str) -> None:
        """记录拒绝事件."""
        self._denial_log.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'tool_name': tool_name,
            'reason': reason,
        })

        # 保持日志大小限制
        if len(self._denial_log) > 10000:
            self._denial_log = self._denial_log[-5000:]

    @staticmethod
    def _match_glob(pattern: str, path: str) -> bool:
        """简单的 glob 匹配."""
        regex = pattern.replace('.', '\\.').replace('*', '.*').replace('?', '.')
        return bool(re.search(regex, path))
