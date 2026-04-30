"""压缩警告 Hook。

当对话接近模型的上下文窗口上限时，主动发出警告。
支持可配置的阈值和自定义警告消息。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from openharness.services.token_estimation import estimate_tokens

log = logging.getLogger(__name__)


@dataclass
class CompactWarningConfig:
    """压缩警告配置。"""

    warning_threshold: float = 0.8  # 使用率超过此值时触发警告（默认 80%）
    critical_threshold: float = 0.95  # 严重阈值（95%），强制建议压缩
    context_window_size: int = 200000  # 默认上下文窗口大小（token 数）
    enabled: bool = True
    auto_compact_suggestion: bool = True  # 是否自动建议执行压缩


@dataclass(frozen=True)
class CompactWarningResult:
    """压缩警告结果。"""

    should_warn: bool
    is_critical: bool
    usage_percent: float
    used_tokens: int
    total_tokens: int
    message: str = ""
    suggested_action: str = ""


class CompactWarningHook:
    """压缩警告检测器。

    在每次添加消息到历史记录时检查上下文使用率，
    当接近上限时发出警告。
    """

    def __init__(self, config: CompactWarningConfig | None = None) -> None:
        self._config = config or CompactWarningConfig()
        self._warning_callback: Callable[[CompactWarningResult], None] | None = None
        self._last_warning_at_usage: float = 0.0

    def set_warning_callback(self, callback: Callable[[CompactWarningResult], None]) -> None:
        """设置警告回调函数"""
        self._warning_callback = callback

    def check_context_usage(
        self,
        current_token_count: int,
        *,
        context_window_size: int | None = None,
    ) -> CompactWarningResult:
        """检查当前上下文使用率并决定是否需要警告

        Args:
            current_token_count: 当前已使用的 token 数
            context_window_size: 上下文窗口大小（覆盖配置）

        Returns:
            CompactWarningResult 包含是否需要警告和相关信息
        """
        if not self._config.enabled:
            return CompactWarningResult(
                should_warn=False,
                is_critical=False,
                usage_percent=0.0,
                used_tokens=current_token_count,
                total_tokens=context_window_size or self._config.context_window_size,
            )

        total = context_window_size or self._config.context_window_size
        usage_percent = min(current_token_count / total, 1.0)

        should_warn = False
        is_critical = False
        message = ""
        suggested_action = ""

        if usage_percent >= self._config.critical_threshold:
            is_critical = True
            should_warn = True
            remaining = total - current_token_count
            message = (
                f"⚠️ **上下文使用率严重**: {usage_percent:.1%} "
                f"(剩余 ~{remaining:,} tokens)\n"
                f"强烈建议立即执行上下文压缩以避免信息丢失。"
            )
            if self._config.auto_compact_suggestion:
                suggested_action = "microcompact_messages_time_aware()"

        elif usage_percent >= self._config.warning_threshold:
            # 避免重复警告（在阈值附近波动时不反复触发）
            if abs(usage_percent - self._last_warning_at_usage) > 0.02:
                should_warn = True
                remaining = total - current_token_count
                message = (
                    f"📊 **上下文使用率**: {usage_percent:.1%} "
                    f"(剩余 ~{remaining:,} tokens)\n"
                    f"建议考虑执行上下文压缩以保持性能。"
                )
                if self._config.auto_compact_suggestion:
                    suggested_action = "考虑调用 microcompact_messages_time_aware()"
                self._last_warning_at_usage = usage_percent

        result = CompactWarningResult(
            should_warn=should_warn,
            is_critical=is_critical,
            usage_percent=usage_percent,
            used_tokens=current_token_count,
            total_tokens=total,
            message=message,
            suggested_action=suggested_action,
        )

        if should_warn and self._warning_callback:
            try:
                self._warning_callback(result)
            except Exception as e:
                log.warning("警告回调执行失败: %s", e)

        return result

    def estimate_message_tokens(self, messages: list[dict]) -> int:
        """估算消息列表的总 token 数（复用专业 token 估算器）"""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += estimate_tokens(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        text = block.get("text", "") or block.get("input", "")
                        if isinstance(text, str):
                            total += estimate_tokens(text)
        return total

    def check_messages(
        self,
        messages: list[dict],
        *,
        context_window_size: int | None = None,
    ) -> CompactWarningResult:
        """检查消息列表的上下文使用率

        这是便捷方法，结合了 token 估算和使用率检查
        """
        estimated_tokens = self.estimate_message_tokens(messages)
        return self.check_context_usage(
            estimated_tokens, context_window_size=context_window_size
        )

    def get_config_summary(self) -> dict:
        """返回配置摘要"""
        return {
            "enabled": self._config.enabled,
            "warning_threshold": f"{self._config.warning_threshold:.0%}",
            "critical_threshold": f"{self._config.critical_threshold:.0%}",
            "context_window_size": self._config.context_window_size,
            "auto_compact_suggestion": self._config.auto_compact_suggestion,
        }
