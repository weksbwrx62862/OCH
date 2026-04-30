"""权限拒绝追踪系统

参考实现: Claude Code src/utils/permissions/denialTracking.ts

功能:
- 记录权限拒绝历史（工具名 + 命令/输入 + 时间戳）
- 相同操作再次请求时，直接拒绝，不再询问用户
- 减少重复确认，提升 UX
- 可配置的过期时间（默认 30 分钟）

使用示例:
    >>> tracker = DenialTracker()
    >>>
    >>> # 第一次：询问用户
    >>> if not tracker.is_previously_denied("bash", "rm -rf /tmp"):
    ...     allowed = ask_user("Allow rm -rf /tmp?")
    ...     if not allowed:
    ...         tracker.record_denial("bash", "rm -rf /tmp")
    ...
    >>>
    >>> # 第二次相同命令：直接拒绝
    >>> if tracker.is_previously_denied("bash", "rm -rf /tmp"):
    ...     print("Permission denied (previously denied)")
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

# 默认过期时间（秒）
DEFAULT_DENIAL_EXPIRY_SEC = 1800.0  # 30 分钟


@dataclass
class DenialRecord:
    """拒绝记录"""

    tool_name: str
    command_hash: str  # 命令/输入的哈希值
    denied_at: float = field(default_factory=time.time)
    reason: str = ""  # 拒绝原因（可选）


@dataclass
class DenialTrackerConfig:
    """拒绝追踪器配置"""

    expiry_seconds: float = DEFAULT_DENIAL_EXPIRY_SEC
    max_records: int = 1000  # 最大记录数（防止内存泄漏）
    enabled: bool = True


class DenialTracker:
    """权限拒绝追踪器

    记录用户拒绝过的操作，后续相同操作自动拒绝，
    避免重复询问用户。

    参考 Claude Code denialTracking.ts 的实现
    """

    def __init__(self, config: DenialTrackerConfig | None = None):
        """
        初始化拒绝追踪器

        Args:
            config: 配置参数（可选）
        """
        self._config = config or DenialTrackerConfig()

        # 存储格式: {tool_name: [DenialRecord]}
        self._denials: dict[str, list[DenialRecord]] = {}
        self._lock = threading.Lock()

    def is_previously_denied(
        self,
        tool_name: str,
        tool_input: str | dict | None = None,
    ) -> bool:
        """
        检查操作是否之前被拒绝过

        Args:
            tool_name: 工具名称（如 "bash"）
            tool_input: 工具输入（命令字符串或字典）

        Returns:
            如果之前被拒绝且未过期 → True
            否则 → False
        """
        if not self._config.enabled:
            return False

        cmd_hash = self._compute_hash(tool_input)

        with self._lock:
            records = self._denials.get(tool_name, [])

            for record in records:
                if record.command_hash == cmd_hash:
                    age_sec = time.time() - record.denied_at
                    if age_sec < self._config.expiry_seconds:
                        log.debug(
                            "操作被拒绝（历史记录）: tool=%s, hash=%s, %.1f分钟前",
                            tool_name,
                            cmd_hash[:12],
                            age_sec / 60.0,
                        )
                        return True

        return False

    def record_denial(
        self,
        tool_name: str,
        tool_input: str | dict | None = None,
        reason: str = "",
    ) -> None:
        """
        记录一次拒绝

        Args:
            tool_name: 工具名称
            tool_input: 工具输入
            reason: 拒绝原因（可选）
        """
        if not self._config.enabled:
            return

        cmd_hash = self._compute_hash(tool_input)
        record = DenialRecord(
            tool_name=tool_name,
            command_hash=cmd_hash,
            reason=reason,
        )

        with self._lock:
            if tool_name not in self._denials:
                self._denials[tool_name] = []

            self._denials[tool_name].append(record)

        log.info(
            "记录权限拒绝: tool=%s, hash=%s, reason=%s",
            tool_name,
            cmd_hash[:12],
            reason or "(无)",
        )

        # 清理过期记录和限制大小
        self._cleanup(tool_name)

    def clear_denials(self, tool_name: str | None = None) -> int:
        """
        清除拒绝记录

        Args:
            tool_name: 指定工具（None = 清除所有）

        Returns:
            清除的记录数量
        """
        with self._lock:
            if tool_name:
                count = len(self._denials.get(tool_name, []))
                del self._denials[tool_name]
                log.debug("清除 %s 的 %d 条拒绝记录", tool_name, count)
                return count
            else:
                total = sum(len(v) for v in self._denials.values())
                self._denials.clear()
                log.debug("清除全部 %d 条拒绝记录", total)
                return total

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            total = sum(len(v) for v in self._denials.values())
            by_tool = {k: len(v) for k, v in self._denials.items()}

        return {
            "total_denials": total,
            "by_tool": by_tool,
            "expiry_seconds": self._config.expiry_seconds,
            "enabled": self._config.enabled,
        }

    def _compute_hash(self, tool_input: str | dict | None) -> str:
        """计算工具输入的哈希值"""
        if tool_input is None:
            return ""

        if isinstance(tool_input, dict):
            input_str = str(sorted(tool_input.items()))
        else:
            input_str = str(tool_input)

        return hashlib.sha256(input_str.encode()).hexdigest()

    def _cleanup(self, task_name: str) -> None:
        """清理过期记录并限制大小（调用方需持有 self._lock）"""
        now = time.time()
        records = self._denials.get(task_name, [])

        # 移除过期记录
        self._denials[task_name] = [
            r for r in records if (now - r.denied_at) < self._config.expiry_seconds
        ]

        # 限制最大记录数
        if len(self._denials[task_name]) > self._config.max_records:
            self._denials[task_name] = self._denials[task_name][-self._config.max_records :]


# 全局单例（线程安全）
_tracker_instance: DenialTracker | None = None
_tracker_lock = threading.Lock()


def get_denial_tracker() -> DenialTracker:
    """获取全局拒绝追踪器实例（线程安全）"""
    global _tracker_instance
    if _tracker_instance is None:
        with _tracker_lock:
            if _tracker_instance is None:
                _tracker_instance = DenialTracker()
    return _tracker_instance


def reset_denial_tracker() -> None:
    """重置全局拒绝追踪器（用于测试）"""
    global _tracker_instance
    with _tracker_lock:
        _tracker_instance = None
