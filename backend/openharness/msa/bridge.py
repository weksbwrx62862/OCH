"""OCH 记忆 ↔ MSA Document 格式转换桥接"""
from __future__ import annotations
import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from openharness.msa.types import MemorySearchResult, MemorySourceType, EncodeStats

log = logging.getLogger(__name__)


@dataclass
class Document:
    doc: str = ""
    doc_id: int = 0
    num_chunks: int = 0


@dataclass
class SyncSnapshot:
    """同步快照，用于增量判断"""
    fact_count: int = 0
    fact_hash: str = ""
    memory_file_count: int = 0
    memory_file_hash: str = ""
    timestamp: float = 0.0


class MSABridge:
    """OCH 记忆系统 → MSA Document 格式的双向转换桥接"""

    def __init__(self, cache_dir: Path | None = None):
        self._cache_dir = cache_dir or (Path.home() / ".openharness" / "msa_cache")
        self._id_map: dict[int, dict[str, Any]] = {}
        self._next_doc_id: int = 1
        self._snapshot: SyncSnapshot | None = None
        self._pending_encode: list[Document] = []

    @property
    def id_map(self) -> dict[int, dict[str, Any]]:
        return dict(self._id_map)

    def facts_to_documents(
        self,
        facts: list[dict],
        *,
        group_by_category: bool = True,
    ) -> list[Document]:
        """将 MemoryFact 列表转换为 MSA Document 列表

        Args:
            facts: MemoryFact 字典列表，每项包含 id, content, category, tags 等
            group_by_category: 是否按 category 分组为单个 Document

        Returns:
            MSA Document 列表
        """
        documents = []

        if group_by_category:
            from collections import defaultdict
            grouped = defaultdict(list)
            for f in facts:
                cat = f.get("category", "general")
                grouped[cat].append(f)

            for category, items in grouped.items():
                parts = []
                for item in items:
                    tags_str = ", ".join(item.get("tags", []))
                    content = item.get("content", "")
                    entry_text = f"[{category}] {content}"
                    if tags_str:
                        entry_text += f"  (tags: {tags_str})"
                    parts.append(entry_text)

                doc_text = "\n\n".join(parts)
                doc_id = self._allocate_doc_id()

                doc = Document(doc=doc_text, doc_id=doc_id)
                documents.append(doc)

                self._id_map[doc_id] = {
                    "source_type": MemorySourceType.MEMORY_FACT,
                    "source_ids": [f.get("id", "") for f in items],
                    "category": category,
                    "count": len(items),
                }
        else:
            for f in facts:
                doc_id = self._allocate_doc_id()
                doc = Document(
                    doc=f.get("content", ""),
                    doc_id=doc_id,
                )
                documents.append(doc)
                self._id_map[doc_id] = {
                    "source_type": MemorySourceType.MEMORY_FACT,
                    "source_id": f.get("id", ""),
                    "category": f.get("category", "general"),
                }

        return documents

    def agent_memory_to_documents(
        self,
        entries: list[dict],
        *,
        group_by_category: bool = True,
    ) -> list[Document]:
        """将 AgentMemory MemoryEntry 列表转换为 MSA Document 列表

        Args:
            entries: MemoryEntry 字典列表，包含 id, agent_id, category, content, tags 等
            group_by_category: 是否按 category 分组

        Returns:
            MSA Document 列表
        """
        documents = []

        if group_by_category:
            from collections import defaultdict
            grouped = defaultdict(list)
            for e in entries:
                cat = e.get("category", "general")
                grouped[cat].append(e)

            for category, items in grouped.items():
                parts = []
                for item in items:
                    content = item.get("content", "")
                    tags_str = ", ".join(item.get("tags", []))
                    agent_id = item.get("agent_id", "unknown")
                    entry_text = f"[Agent:{agent_id}][{category}] {content}"
                    if tags_str:
                        entry_text += f"  (tags: {tags_str})"
                    parts.append(entry_text)

                doc_text = "\n\n".join(parts)
                doc_id = self._allocate_doc_id()

                doc = Document(doc=doc_text, doc_id=doc_id)
                documents.append(doc)

                self._id_map[doc_id] = {
                    "source_type": MemorySourceType.AGENT_MEMORY,
                    "source_ids": [e.get("id", "") for e in items],
                    "agent_ids": list(set(e.get("agent_id", "") for e in items)),
                    "category": category,
                    "count": len(items),
                }
        else:
            for e in entries:
                doc_id = self._allocate_doc_id()
                doc = Document(
                    doc=e.get("content", ""),
                    doc_id=doc_id,
                )
                documents.append(doc)
                self._id_map[doc_id] = {
                    "source_type": MemorySourceType.AGENT_MEMORY,
                    "source_id": e.get("id", ""),
                    "agent_id": e.get("agent_id", ""),
                    "category": e.get("category", "general"),
                }

        return documents

    def resolve_result(self, doc_id: int, text_content: str, score: float = 0.0) -> MemorySearchResult:
        """将 MSA 返回的 doc_id 映射回 MemorySearchResult"""
        meta = self._id_map.get(doc_id, {})
        return MemorySearchResult(
            content=text_content,
            score=score,
            source_id=str(meta.get("source_id", "")),
            source_type=meta.get("source_type", MemorySourceType.MEMORY_FACT),
            category=meta.get("category", ""),
            tags=meta.get("tags", []),
        )

    def save_snapshot(self, facts: list[dict], memory_entries: list[dict]) -> SyncSnapshot:
        """保存当前数据快照用于增量判断"""
        fact_json = json.dumps(facts, sort_keys=True, default=str)
        mem_json = json.dumps(memory_entries, sort_keys=True, default=str)

        self._snapshot = SyncSnapshot(
            fact_count=len(facts),
            fact_hash=hashlib.md5(fact_json.encode()).hexdigest(),
            memory_file_count=len(memory_entries),
            memory_file_hash=hashlib.md5(mem_json.encode()).hexdigest(),
        )
        return self._snapshot

    def needs_sync(self, facts: list[dict], memory_entries: list[dict]) -> bool:
        """判断是否需要重新同步"""
        if self._snapshot is None:
            return True

        fact_json = json.dumps(facts, sort_keys=True, default=str)
        mem_json = json.dumps(memory_entries, sort_keys=True, default=str)

        current_fact_hash = hashlib.md5(fact_json.encode()).hexdigest()
        current_mem_hash = hashlib.md5(mem_json.encode()).hexdigest()

        return (
            self._snapshot.fact_hash != current_fact_hash
            or self._snapshot.memory_file_hash != current_mem_hash
        )

    def sync_all(self, facts: list[dict], memory_entries: list[dict]) -> tuple[list[Document], SyncSnapshot]:
        """全量同步：转换所有记忆为 Documents"""
        self._id_map.clear()
        self._next_doc_id = 1

        docs = []
        docs.extend(self.facts_to_documents(facts))
        docs.extend(self.agent_memory_to_documents(memory_entries))

        snapshot = self.save_snapshot(facts, memory_entries)
        return docs, snapshot

    def sync_incremental(
        self,
        facts: list[dict],
        memory_entries: list[dict],
        known_fact_ids: set[str] | None = None,
        known_memory_ids: set[str] | None = None,
    ) -> tuple[list[Document], SyncSnapshot]:
        """增量同步：仅转换新增/变更的条目"""
        if self.needs_sync(facts, memory_entries):
            return self.sync_all(facts, memory_entries)

        new_facts = []
        new_memories = []

        if known_fact_ids is not None:
            for f in facts:
                if f.get("id", "") not in known_fact_ids:
                    new_facts.append(f)

        if known_memory_ids is not None:
            for e in memory_entries:
                if e.get("id", "") not in known_memory_ids:
                    new_memories.append(e)

        if not new_facts and not new_memories:
            snapshot = self.save_snapshot(facts, memory_entries)
            return [], snapshot

        new_docs = []
        if new_facts:
            new_docs.extend(self.facts_to_documents(new_facts))
        if new_memories:
            new_docs.extend(self.agent_memory_to_documents(new_memories))

        snapshot = self.save_snapshot(facts, memory_entries)
        return new_docs, snapshot

    def _allocate_doc_id(self) -> int:
        doc_id = self._next_doc_id
        self._next_doc_id += 1
        return doc_id

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_documents": len(self._id_map),
            "next_doc_id": self._next_doc_id,
            "has_snapshot": self._snapshot is not None,
            "sources": {
                "memory_fact": sum(1 for m in self._id_map.values() if m.get("source_type") == "memory_fact"),
                "agent_memory": sum(1 for m in self._id_map.values() if m.get("source_type") == "agent_memory"),
            },
        }
