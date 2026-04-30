"""路径白名单管理系统。

支持全局/团队/个人三级白名单，
与 PermissionChecker 深度集成。
"""

from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

log = logging.getLogger(__name__)


class WhitelistLevel(str, Enum):
    """白名单级别。"""

    GLOBAL = "global"
    TEAM = "team"
    PERSONAL = "personal"


@dataclass(frozen=True)
class PathWhitelistRule:
    """路径白名单规则。"""

    pattern: str
    allow: bool = True
    operations: tuple[str, ...] = ("read", "write", "execute")
    level: WhitelistLevel = WhitelistLevel.TEAM


@dataclass
class PathWhitelistConfig:
    """路径白名单配置。"""

    global_rules: list[PathWhitelistRule] = field(default_factory=list)
    team_rules: list[PathWhitelistRule] = field(default_factory=list)
    personal_rules: list[PathWhitelistRule] = field(default_factory=list)
    default_deny: bool = False  # 默认拒绝未匹配的路径


class PathWhitelistManager:
    """路径白名单管理器。"""

    def __init__(self, config: PathWhitelistConfig | None = None) -> None:
        self._config = config or PathWhitelistConfig()

    def add_rule(
        self,
        pattern: str,
        *,
        level: WhitelistLevel = WhitelistLevel.TEAM,
        allow: bool = True,
        operations: tuple[str, ...] = ("read", "write", "execute"),
    ) -> None:
        """添加白名单规则"""
        rule = PathWhitelistRule(
            pattern=pattern, allow=allow, operations=operations, level=level
        )
        if level == WhitelistLevel.GLOBAL:
            self._config.global_rules.append(rule)
        elif level == WhitelistLevel.TEAM:
            self._config.team_rules.append(rule)
        else:
            self._config.personal_rules.append(rule)

    def remove_rule(self, pattern: str, level: WhitelistLevel) -> bool:
        """移除规则"""
        rules_list = self._get_rules_list(level)
        original_len = len(rules_list)
        rules_list[:] = [r for r in rules_list if r.pattern != pattern]
        return len(rules_list) < original_len

    def check_path(
        self,
        target_path: str,
        operation: str = "read",
    ) -> tuple[bool, str]:
        """检查路径是否在白名单中（含路径遍历防护）

        Returns:
            (allowed, reason) 元组
        """
        # 路径规范化：检测并阻止 ../ 遍历攻击
        normalized = target_path
        if ".." in target_path:
            try:
                normalized = str(Path(target_path).resolve())
            except (OSError, ValueError):
                pass

        # 按优先级检查：GLOBAL > TEAM > PERSONAL > DEFAULT
        for rule in self._config.global_rules + self._config.team_rules + self._config.personal_rules:
            if fnmatch.fnmatch(normalized, rule.pattern):
                if operation not in rule.operations:
                    return False, f"操作 '{operation}' 不在允许列表中: {rule.pattern}"
                if not rule.allow:
                    return False, f"路径被显式拒绝: {rule.pattern}"
                return True, f"匹配白名单规则 [{rule.level.value}]: {rule.pattern}"

        # 默认行为
        if self._config.default_deny:
            return False, f"默认拒绝（路径不在白名单中）: {normalized}"
        return True, "未匹配任何白名单规则，使用默认行为"

    def get_matching_rules(self, target_path: str) -> list[PathWhitelistRule]:
        """获取所有匹配的规则"""
        normalized = target_path
        if ".." in target_path:
            try:
                normalized = str(Path(target_path).resolve())
            except (OSError, ValueError):
                pass
        all_rules = self._config.global_rules + self._config.team_rules + self._config.personal_rules
        return [r for r in all_rules if fnmatch.fnmatch(normalized, r.pattern)]

    def get_stats(self) -> dict:
        """返回统计信息"""
        return {
            "global_count": len(self._config.global_rules),
            "team_count": len(self._config.team_rules),
            "personal_count": len(self._config.personal_rules),
            "total": len(self._config.global_rules) + len(self._config.team_rules) + len(self._config.personal_rules),
            "default_deny": self._config.default_deny,
        }

    def _get_rules_list(self, level: WhitelistLevel) -> list[PathWhitelistRule]:
        """获取指定级别的规则列表"""
        if level == WhitelistLevel.GLOBAL:
            return self._config.global_rules
        elif level == WhitelistLevel.TEAM:
            return self._config.team_rules
        else:
            return self._config.personal_rules

    @classmethod
    def from_config_file(cls, path: Path) -> "PathWhitelistManager":
        """从配置文件加载（异常时返回默认空配置）"""
        import json

        config = PathWhitelistConfig()
        try:
            config_data = {}
            if path.exists():
                config_data = json.loads(path.read_text(encoding="utf-8"))

            for entry in config_data.get("global_rules", []):
                try:
                    level = WhitelistLevel(entry["level"]) if isinstance(entry["level"], str) else entry.get("level", WhitelistLevel.GLOBAL)
                    config.global_rules.append(PathWhitelistRule(
                        pattern=entry["pattern"],
                        allow=entry.get("allow", True),
                        operations=tuple(entry.get("operations", ("read", "write", "execute"))),
                        level=level,
                    ))
                except (KeyError, TypeError, ValueError):
                    log.warning("跳过无效的全局规则: %r", entry)

            for entry in config_data.get("team_rules", []):
                try:
                    level = WhitelistLevel(entry["level"]) if isinstance(entry["level"], str) else entry.get("level", WhitelistLevel.TEAM)
                    config.team_rules.append(PathWhitelistRule(
                        pattern=entry["pattern"],
                        allow=entry.get("allow", True),
                        operations=tuple(entry.get("operations", ("read", "write", "execute"))),
                        level=level,
                    ))
                except (KeyError, TypeError, ValueError):
                    log.warning("跳过无效的团队规则: %r", entry)

            for entry in config_data.get("personal_rules", []):
                try:
                    level = WhitelistLevel(entry["level"]) if isinstance(entry["level"], str) else entry.get("level", WhitelistLevel.PERSONAL)
                    config.personal_rules.append(PathWhitelistRule(
                        pattern=entry["pattern"],
                        allow=entry.get("allow", True),
                        operations=tuple(entry.get("operations", ("read", "write", "execute"))),
                        level=level,
                    ))
                except (KeyError, TypeError, ValueError):
                    log.warning("跳过无效的个人规则: %r", entry)

            if "default_deny" in config_data:
                config.default_deny = config_data["default_deny"]
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("加载路径白名单配置失败 (%s): %s", path, exc)

        return cls(config)

    def to_config_file(self, path: Path) -> None:
        """保存到配置文件"""
        import json

        data = {
            "global_rules": [
                {"pattern": r.pattern, "allow": r.allow, "operations": list(r.operations), "level": r.level.value}
                for r in self._config.global_rules
            ],
            "team_rules": [
                {"pattern": r.pattern, "allow": r.allow, "operations": list(r.operations), "level": r.level.value}
                for r in self._config.team_rules
            ],
            "personal_rules": [
                {"pattern": r.pattern, "allow": r.allow, "operations": list(r.operations), "level": r.level.value}
                for r in self._config.personal_rules
            ],
            "default_deny": self._config.default_deny,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
