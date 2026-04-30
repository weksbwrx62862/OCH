"""Agent 内存管理系统（Agent Memory）

为每个 Agent 提供跨会话的持久化记忆存储能力。
支持记忆的记录、检索、删除、整合和导入导出。

参考实现: Claude Code src/tools/AgentTool/agentMemory.ts

设计思路:
- 子 Agent（Worker）每次启动都是「失忆」状态
- Agent Memory 提供持久化记忆，让 Worker 能利用历史经验
- 使用 JSON 文件作为存储后端（简单可靠，无需额外依赖）
- 支持分类、标签、重要程度、过期时间等元数据

存储路径:
    ~/.openharness/memory/{agent_id}.json
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from openharness.msa.retriever import MSARetriever
from openharness.msa.types import MemorySearchResult
from openharness.msa.config import OCHMSAConfig

log = logging.getLogger(__name__)

DEFAULT_MEMORY_DIR = Path.home() / ".openharness" / "memory"


@dataclass
class MemoryEntry:
    """单条记忆条目"""

    id: str
    agent_id: str
    category: str
    content: str
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    importance: int = 5
    source_task_id: str | None = None


@dataclass
class MemoryQuery:
    """记忆查询条件"""

    query: str
    categories: list[str] | None = None
    tags: list[str] | None = None
    min_importance: int = 0
    limit: int = 5
    include_expired: bool = False


@dataclass
class AgentMemoryConfig:
    """Agent 记忆配置"""

    storage_path: Path | None = None
    max_memories_per_agent: int = 200
    auto_expire_days: int = 30
    high_importance_keep_days: int = 90


class AgentMemory:
    """Agent 持久化记忆管理器"""

    def __init__(self, agent_id: str, config: AgentMemoryConfig | None = None, msa_config: OCHMSAConfig | None = None):
        self.agent_id = agent_id
        self.config = config or AgentMemoryConfig()
        self._msa_config = msa_config
        self._msa_pending_encode: list[int] = []  # 待编码的 entry id 列表
        self._entries: list[MemoryEntry] = []
        self._storage_path = self._resolve_storage_path()
        self._lock = asyncio.Lock()
        self._load()

    def _resolve_storage_path(self) -> Path:
        if self.config.storage_path:
            return self.config.storage_path / f"{self.agent_id}.json"
        return DEFAULT_MEMORY_DIR / f"{self.agent_id}.json"

    async def remember(
        self,
        content: str,
        category: str = "general",
        *,
        tags: list[str] | None = None,
        importance: int = 5,
        source_task_id: str | None = None,
        expires_in_days: int | None = None,
    ) -> MemoryEntry:
        """记录一条新记忆"""
        if len(self._entries) >= self.config.max_memories_per_agent:
            self._evict_lowest_importance()

        entry = MemoryEntry(
            id=str(uuid.uuid4())[:12],
            agent_id=self.agent_id,
            category=category,
            content=content,
            tags=tags or [],
            importance=max(1, min(10, importance)),
            source_task_id=source_task_id,
            expires_at=(
                time.time() + (expires_in_days or self.config.auto_expire_days) * 86400
                if expires_in_days is not None
                else None
            ),
        )
        self._entries.append(entry)
        await self._save()
        log.debug("记忆已记录 [%s]: %s", entry.id, content[:80])

        # MSA 增量编码标记
        if self._msa_config and self._msa_config.encode_on_write:
            self._msa_pending_encode.append(entry.id)

        return entry

    async def recall(self, query: MemoryQuery | str, *, use_msa: bool | None = None, **kwargs) -> list[MemoryEntry]:
        """回忆相关记忆

        Args:
            query: 查询文本或查询对象
            use_msa: 是否使用 MSA 语义检索
                   None → 根据全局配置决定
                   True → 强制使用 MSA
                   False → 强制使用关键词
        """
        should_use_msa = use_msa
        if should_use_msa is None:
            should_use_msa = (
                self._msa_config is not None
                and self._msa_config.enabled
            )

        if should_use_msa:
            return await self._msa_recall(query, **kwargs)

        return await self._keyword_recall(query, **kwargs)

    async def _msa_recall(self, query: MemoryQuery | str, **kwargs) -> list[MemoryEntry]:
        """MSA 语义检索路径"""
        retriever = MSARetriever.get_instance()
        if retriever is None or not retriever.is_available:
            return await self._keyword_recall(query, **kwargs)

        query_text = query.query if isinstance(query, MemoryQuery) else query
        results = await retriever.search(query_text, top_k=kwargs.get('max_results', 10))

        entries = []
        for r in results:
            if r.source_type.value == "agent_memory":
                # 尝试从本地存储中找到对应条目
                entry = self._find_entry_by_source(r.source_id)
                if entry:
                    entries.append(entry)
            else:
                entries.append(MemoryEntry(
                    id=f"msa_{hash(r.content)}",
                    agent_id=self.agent_id,
                    category=r.category or "general",
                    content=r.content,
                    tags=list(r.tags),
                    metadata={"score": r.score},
                ))

        return entries

    async def _keyword_recall(self, query: MemoryQuery | str, **kwargs) -> list[MemoryEntry]:
        """原有关键词检索逻辑"""
        if isinstance(query, str):
            query_obj = MemoryQuery(query=query, **kwargs)
        else:
            query_obj = query

        now = time.time()
        results: list[tuple[MemoryEntry, float]] = []

        for entry in self._entries:
            if not query_obj.include_expired and entry.expires_at is not None:
                if now > entry.expires_at:
                    continue

            if entry.importance < query_obj.min_importance:
                continue

            if query_obj.categories and entry.category not in query_obj.categories:
                continue

            if query_obj.tags and not any(t in entry.tags for t in query_obj.tags):
                continue

            score = self._compute_relevance(entry, query_obj.query)
            if score > 0:
                results.append((entry, score))

        results.sort(key=lambda x: (-x[1], -x[0].importance))
        return [e for e, _ in results[: query_obj.limit]]

    async def forget(self, memory_id: str) -> bool:
        """删除特定记忆"""
        for i, entry in enumerate(self._entries):
            if entry.id == memory_id:
                del self._entries[i]
                await self._save()
                return True
        return False

    async def forget_by_category(self, category: str) -> int:
        """按分类批量删除"""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.category != category]
        removed = before - len(self._entries)
        if removed > 0:
            await self._save()
        return removed

    async def consolidate(self) -> int:
        """整合重复/相似的记忆，返回合并数量"""
        merged = 0
        seen_keys: dict[str, MemoryEntry] = {}

        for entry in self._entries:
            key = f"{entry.category}:{entry.content[:50]}"
            existing = seen_keys.get(key)

            if existing is not None:
                existing.content += "\n" + entry.content
                existing.importance = max(existing.importance, entry.importance)
                if entry.tags:
                    existing.tags.extend(t for t in entry.tags if t not in existing.tags)
                merged += 1
            else:
                seen_keys[key] = entry

        self._entries = list(seen_keys.values())
        if merged > 0:
            await self._save()
        return merged

    def get_stats(self) -> dict[str, Any]:
        """返回记忆统计信息"""
        now = time.time()
        categories: dict[str, int] = {}
        total_importance = 0
        expired_count = 0

        for e in self._entries:
            categories[e.category] = categories.get(e.category, 0) + 1
            total_importance += e.importance
            if e.expires_at is not None and now > e.expires_at:
                expired_count += 1

        return {
            "agent_id": self.agent_id,
            "total_entries": len(self._entries),
            "categories": categories,
            "avg_importance": round(total_importance / max(1, len(self._entries)), 1),
            "expired_count": expired_count,
            "max_capacity": self.config.max_memories_per_agent,
            "utilization_pct": round(
                len(self._entries) / max(1, self.config.max_memories_per_agent) * 100, 1
            ),
        }

    async def export_json(self, path: str) -> None:
        """导出所有记忆到 JSON 文件"""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(e) for e in self._entries]
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("导出 %d 条记忆到 %s", len(data), path)

    @classmethod
    async def import_json(cls, agent_id: str, path: str) -> AgentMemory:
        """从 JSON 文件导入记忆"""
        memory = cls(agent_id)
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        memory._entries = [MemoryEntry(**d) for d in raw if isinstance(d, dict) and "id" in d]
        await memory._save()
        log.info("从 %s 导入 %d 条记忆", path, len(memory._entries))
        return memory

    # --- 内部方法 ---

    def _find_entry_by_source(self, source_id: str) -> MemoryEntry | None:
        """根据 source_id 查找本地条目"""
        for entry in self._entries:
            if str(entry.id) == source_id:
                return entry
        return None

    def _compute_relevance(self, entry: MemoryEntry, query: str) -> float:
        """计算记忆与查询的相关性得分"""
        q_lower = query.lower()
        c_lower = entry.content.lower()

        if q_lower in c_lower:
            return 1.0

        words = set(q_lower.split())
        matches = sum(1 for w in words if w in c_lower and len(w) > 2)
        if matches == 0:
            return 0.0

        tag_bonus = sum(1 for t in entry.tags if t.lower() in q_lower)
        return (matches / len(words)) * 0.7 + (tag_bonus * 0.1)

    def _evict_lowest_importance(self) -> None:
        """淘汰最低重要程度的条目"""
        if not self._entries:
            return
        self._entries.sort(key=lambda e: (e.importance, e.created_at))
        evicted = self._entries.pop(0)
        log.debug("淘汰低重要性记忆: %s (importance=%d)", evicted.id, evicted.importance)

    def _load(self) -> None:
        """从文件加载记忆"""
        if not self._storage_path.exists():
            return
        try:
            raw = json.loads(self._storage_path.read_text(encoding="utf-8"))
            self._entries = [MemoryEntry(**d) for d in raw if isinstance(d, dict) and "id" in d]
            log.debug("加载 %d 条记忆 from %s", len(self._entries), self._storage_path)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            log.warning("加载记忆文件失败: %s (%s)", self._storage_path, exc)
            self._entries = []

    async def _save(self) -> None:
        """保存记忆到文件（线程安全）"""
        async with self._lock:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = [asdict(e) for e in self._entries]
            self._storage_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )


def get_memory_for_agent(agent_id: str, config: AgentMemoryConfig | None = None) -> AgentMemory:
    """快速创建指定 Agent 的记忆管理器"""
    return AgentMemory(agent_id, config=config)
