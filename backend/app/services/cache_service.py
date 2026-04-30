"""Cache Service — manages CompactCache for tool output compression."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_compact_cache = None


def get_compact_cache():
    """获取全局 CompactCache 实例."""
    global _compact_cache
    if _compact_cache is None:
        try:
            from openharness.services.compact.cached_compact import CompactCache, CompactCacheConfig
            _compact_cache = CompactCache(
                config=CompactCacheConfig(
                    enabled=True,
                    keep_full_content=False,
                    max_entries=500,
                    default_expiry_seconds=3600.0,
                    summary_max_length=100,
                )
            )
            logger.info("CompactCache 初始化完成 (max=%d entries)", 500)
        except Exception as e:
            logger.warning(f"CompactCache 初始化失败: {e}")
            _compact_cache = _NullCompactCache()
    return _compact_cache


class _NullCompactCache:
    """空 CompactCache 降级实现."""

    def record_cleared(self, tool_id, tool_name, content):
        pass

    def lookup(self, tool_id):
        return None

    def get_stats(self):
        return {'total_entries': 0}

    def clear_expired(self, *a, **kw):
        return 0


def record_tool_output_for_cache(tool_id: str, tool_name: str, content: str) -> None:
    """记录工具输出到压缩缓存（在微压缩前调用）."""
    cache = get_compact_cache()
    cache.record_cleared(tool_id, tool_name, content)
