"""缓存微压缩（Cached Microcompact）

在执行微压缩时，将被清除的工具输出记录到缓存中。
支持摘要保留和完整内容恢复两种模式。

参考实现: Claude Code src/services/compact/cachedMicrocompact.ts

设计思路:
- 传统微压缩删除旧工具输出 → 信息永久丢失
- 缓存微压缩删除时同时记录 → 可用于调试、上下文重建、API cache editing
- 双模式:
  1. 摘要模式 (keep_full_content=False): 只保留前 N 字符 + 哈希 + token 估算
  2. 完整模式 (keep_full_content=True): 保留全部内容，支持恢复
"""

from __future__ import annotations

import collections
import hashlib
import logging
import time
from dataclasses import dataclass, field

from openharness.services.token_estimation import estimate_tokens

log = logging.getLogger(__name__)


@dataclass
class CompactCacheConfig:
    """微压缩缓存配置"""

    enabled: bool = True
    keep_full_content: bool = False
    max_entries: int = 500
    default_expiry_seconds: float = 3600.0
    summary_max_length: int = 100


@dataclass
class CachedToolResult:
    """被缓存的工具输出条目"""

    tool_id: str
    tool_name: str
    content_hash: str
    summary: str
    original_length: int
    estimated_tokens: int
    cleared_at: float
    content: str | None = None


@dataclass
class CompactCache:
    """微压缩缓存管理器

    管理 microcompact 过程中被清除的工具输出条目，
    支持按 tool_id 查找、过期清理、批量恢复等功能。
    """

    config: CompactCacheConfig = field(default_factory=CompactCacheConfig)
    _entries: collections.OrderedDict = field(default_factory=collections.OrderedDict)

    def record_cleared(
        self,
        tool_id: str,
        tool_name: str,
        content: str,
    ) -> None:
        """记录一条被清除的工具输出"""
        if not self.config.enabled:
            return

        if len(self._entries) >= self.config.max_entries:
            oldest_key, _ = self._entries.popitem(last=False)
            log.debug("缓存已满，移除最旧条目: %s", oldest_key)

        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        summary = content[: self.config.summary_max_length].replace("\n", " ")
        estimated_tokens = estimate_tokens(content)

        entry = CachedToolResult(
            tool_id=tool_id,
            tool_name=tool_name,
            content_hash=content_hash,
            summary=summary,
            original_length=len(content),
            estimated_tokens=estimated_tokens,
            cleared_at=time.time(),
            content=content if self.config.keep_full_content else None,
        )

        self._entries[tool_id] = entry
        log.debug(
            "记录清除条目: %s (%s), %d 字符, ~%d tokens",
            tool_id,
            tool_name,
            len(content),
            estimated_tokens,
        )

    def lookup(self, tool_id: str) -> CachedToolResult | None:
        """查找缓存条目（命中时更新 LRU 顺序）"""
        entry = self._entries.get(tool_id)
        if entry is not None:
            self._entries.move_to_end(tool_id)
        return entry

    def get_stats(self) -> dict:
        """返回缓存统计信息"""
        total_entries = len(self._entries)
        total_original_chars = sum(e.original_length for e in self._entries.values())
        total_estimated_tokens = sum(e.estimated_tokens for e in self._entries.values())
        has_full_content = sum(1 for e in self._entries.values() if e.content is not None)
        tools_count: dict[str, int] = {}
        for e in self._entries.values():
            tools_count[e.tool_name] = tools_count.get(e.tool_name, 0) + 1

        return {
            "total_entries": total_entries,
            "total_original_characters": total_original_chars,
            "total_estimated_tokens": total_estimated_tokens,
            "entries_with_full_content": has_full_content,
            "tools_breakdown": tools_count,
            "max_entries": self.config.max_entries,
            "utilization_pct": round(total_entries / max(1, self.config.max_entries) * 100, 1),
        }

    def clear_expired(self, max_age_seconds: float | None = None) -> int:
        """清理过期条目

        Args:
            max_age_seconds: 最大存活秒数。None 则使用 config.default_expiry_seconds

        Returns:
            清理的条目数量
        """
        if max_age_seconds is None:
            max_age_seconds = self.config.default_expiry_seconds

        now = time.time()
        expired_keys = [
            tid for tid, entry in self._entries.items() if now - entry.cleared_at > max_age_seconds
        ]

        for key in expired_keys:
            del self._entries[key]

        if expired_keys:
            log.info("清理 %d 条过期缓存条目", len(expired_keys))

        return len(expired_keys)

    def restore_for_tool_ids(self, tool_ids: list[str]) -> dict[str, str]:
        """批量恢复指定 tool_id 的完整内容

        Returns:
            {tool_id: content} 映射，仅包含有完整内容的条目
        """
        result: dict[str, str] = {}
        for tid in tool_ids:
            entry = self._entries.get(tid)
            if entry is not None and entry.content is not None:
                result[tid] = entry.content
        return result

    def clear_all(self) -> None:
        """清空所有缓存条目"""
        count = len(self._entries)
        self._entries.clear()
        log.debug("清空缓存 (%d 条)", count)
