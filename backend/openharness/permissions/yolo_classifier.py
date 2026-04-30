"""YOLO (You Only Live Once) 基于规则的命令安全分类器。

自动判断 Bash 命令是否安全，减少用户权限确认次数。
使用纯规则引擎实现，无需 ML 依赖，覆盖 80%+ 的常见场景。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class YoloResult:
    """YOLO 分类结果。"""

    decision: Literal["allow", "ask", "deny"]
    confidence: float = 1.0
    reason: str = ""


@dataclass
class YoloClassifierConfig:
    """YOLO 分类器配置。"""

    enabled: bool = True
    custom_safe_patterns: list[str] = field(default_factory=list)
    custom_dangerous_patterns: list[str] = field(default_factory=list)
    config_path: str | None = None


class YoloClassifier:
    """You Only Live Only — 基于规则的命令安全分类器。

    使用预定义的正则表达式规则库自动判断命令安全性，
    返回三级判定：ALLOW（安全）、ASK（不确定）、DENY（危险）。
    """

    SAFE_PATTERNS: list[re.Pattern] = [
        re.compile(r"^git\s+(status|log|diff|branch|tag|show|remote|stash)\b"),
        re.compile(r"^(ls|cat|echo|pwd|which|date|whoami|id|uname|hostname)\b"),
        re.compile(r"^python\s+-m\s+(pytest|pip|coverage)\b"),
        re.compile(r"^npm\s+(test|lint|build|run|audit)\b"),
        re.compile(r"^uv\s+(run|sync|add|remove|pip|tree|lock|tool)\b"),
        re.compile(r"^ruff\s+(check|format|lint|fix)\b"),
        re.compile(r"^grep\b"),
        re.compile(r"^find\s+.+\s+-name\b"),
        re.compile(r"^(wc|head|tail|sort|uniq|tr|cut)\b"),
        re.compile(r"^cd\b"),
        re.compile(r"^env\b"),
    ]

    DANGEROUS_PATTERNS: list[re.Pattern] = [
        re.compile(r"rm\s+-rf\s+(/|[~]$)"),
        re.compile(r"DROP\s+TABLE", re.IGNORECASE),
        re.compile(r"chmod\s+777\s+/"),
        re.compile(r">\s*/dev/sd[a-z]\d?"),
        re.compile(r"curl.*\|\s*(ba)?sh\s*$"),
        re.compile(r":\(\)\{\s*:\|:&\s*\};\:"),
        re.compile(r"dd\s+if=.*of=/dev/"),
        re.compile(r"mkfs\."),
        re.compile(r">\s*/etc/"),
        re.compile(r"shutdown\s+-[hH]"),
        re.compile(r"reboot\s*-f"),
        re.compile(r"mkswap\s+/dev/"),
        re.compile(r"swapon\s+/dev/"),
        re.compile(r">\s*/proc/"),
        re.compile(r"sysctl\s+-w\s+kernel\."),
        re.compile(r"iptables\s+-F"),
    ]

    def __init__(self, config: YoloClassifierConfig | None = None) -> None:
        self._config = config or YoloClassifierConfig()
        self._safe_patterns: list[re.Pattern] = list(self.SAFE_PATTERNS)
        self._dangerous_patterns: list[re.Pattern] = list(self.DANGEROUS_PATTERNS)

        if self._config.config_path:
            self._load_config_from_file(Path(self._config.config_path))

        for pattern_str in self._config.custom_safe_patterns:
            try:
                compiled = re.compile(pattern_str)
                self._safe_patterns.append(compiled)
            except re.error as e:
                log.warning("无效的安全模式正则 %r: %s", pattern_str, e)

        for pattern_str in self._config.custom_dangerous_patterns:
            try:
                compiled = re.compile(pattern_str)
                self._dangerous_patterns.append(compiled)
            except re.error as e:
                log.warning("无效的危险模式正则 %r: %s", pattern_str, e)

    def _load_config_from_file(self, path: Path) -> None:
        """从 YAML/JSON 文件加载自定义规则。"""
        try:
            if path.suffix in {".yml", ".yaml"}:
                import yaml

                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            elif path.suffix == ".json":
                import json

                data = json.loads(path.read_text(encoding="utf-8"))
            else:
                log.warning("不支持的配置文件格式: %s", path.suffix)
                return

            if isinstance(data, dict):
                safe_patterns = data.get("safe_patterns", [])
                dangerous_patterns = data.get("dangerous_patterns", [])
                for p in safe_patterns:
                    try:
                        self._safe_patterns.append(re.compile(p))
                    except re.error:
                        continue
                for p in dangerous_patterns:
                    try:
                        self._dangerous_patterns.append(re.compile(p))
                    except re.error:
                        continue
        except Exception as e:
            log.warning("加载 YOLO 配置失败 (%s): %s", path, e)

    def classify(self, tool_name: str, command: str) -> YoloResult:
        """返回 ALLOW / ASK / DENY 三级判定。"""
        if not self._config.enabled:
            return YoloResult(decision="ask", reason="YOLO 分类器已禁用")

        stripped = command.strip()

        if not stripped:
            return YoloResult(decision="ask", reason="空命令")

        for pattern in self._dangerous_patterns:
            if pattern.search(stripped):
                return YoloResult(
                    decision="deny",
                    confidence=0.95,
                    reason=f"匹配危险模式: {pattern.pattern}",
                )

        for pattern in self._safe_patterns:
            if pattern.match(stripped):
                # 复合命令安全检查：拆分子命令后逐个验证
                sub_commands = re.split(r'[;&|]+', stripped)
                if len(sub_commands) > 1:
                    for sub_cmd in sub_commands:
                        sub_cmd = sub_cmd.strip()
                        if not sub_cmd:
                            continue
                        for dp in self._dangerous_patterns:
                            if dp.search(sub_cmd):
                                return YoloResult(
                                    decision="deny",
                                    confidence=0.92,
                                    reason=f"复合命令包含危险子命令: {sub_cmd[:60]} (匹配: {dp.pattern})",
                                )
                return YoloResult(
                    decision="allow",
                    confidence=0.9,
                    reason=f"匹配安全模式: {pattern.pattern}",
                )

        return YoloResult(decision="ask", reason="无法确定安全性，需人工确认")

    def get_stats(self) -> dict:
        """返回分类器统计信息。"""
        return {
            "enabled": self._config.enabled,
            "safe_pattern_count": len(self._safe_patterns),
            "dangerous_pattern_count": len(self._dangerous_patterns),
            "custom_safe_count": len(self._config.custom_safe_patterns),
            "custom_dangerous_count": len(self._config.custom_dangerous_patterns),
        }
