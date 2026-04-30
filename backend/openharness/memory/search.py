"""Simple heuristic memory search."""

from __future__ import annotations

import re
from pathlib import Path

from openharness.memory.scan import scan_memory_files
from openharness.memory.types import MemoryHeader
from openharness.msa.retriever import MSARetriever
from openharness.msa.types import MemorySearchResult, MemorySourceType


async def msa_find_relevant_memories(
    query: str,
    cwd: str | Path,
    *,
    max_results: int = 5,
) -> list[MemoryHeader]:
    """基于 MSA 语义检索的相关记忆

    Args:
        query: 检索查询
        cwd: 工作目录路径
        max_results: 最大返回数量

    Returns:
        相关记忆头部列表
    """
    retriever = MSARetriever.get_instance()
    if retriever is None or not retriever.is_available:
        return []

    results = await retriever.search(query, top_k=max_results)

    headers = []
    for r in results:
        header = MemoryHeader(
            file_path=r.source_id or "",
            line_number=0,
            content_preview=r.content[:200] if len(r.content) > 200 else r.content,
            relevance_score=r.score,
            category=r.category,
            tags=tuple(r.tags),
        )
        headers.append(header)

    return sorted(headers, key=lambda h: h.relevance_score, reverse=True)[:max_results]


def find_relevant_memories(
    query: str,
    cwd: str | Path,
    *,
    max_results: int = 5,
    backend: str = "keyword",
) -> list[MemoryHeader]:
    """查找相关记忆文件

    Args:
        query: 检索查询
        cwd: 工作目录
        max_results: 最大返回数
        backend: 检索后端选择 ("keyword" | "msa" | "auto")
    """
    if backend == "msa":
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
            return loop.run_until_complete(msa_find_relevant_memories(query, cwd, max_results=max_results))
        except RuntimeError:
            return []
    elif backend == "auto":
        from openharness.config.settings import Settings
        settings = Settings.load()
        if settings.msa.enabled:
            return find_relevant_memories(query, cwd, max_results=max_results, backend="msa")

    tokens = _tokenize(query)
    if not tokens:
        return []

    scored: list[tuple[float, MemoryHeader]] = []
    for header in scan_memory_files(cwd, max_files=100):
        meta = f"{header.title} {header.description}".lower()
        body = header.body_preview.lower()

        # Metadata matches are weighted 2x; body matches 1x.
        meta_hits = sum(1 for t in tokens if t in meta)
        body_hits = sum(1 for t in tokens if t in body)
        score = meta_hits * 2.0 + body_hits
        if score > 0:
            scored.append((score, header))

    scored.sort(key=lambda item: (-item[0], -item[1].modified_at))
    return [header for _, header in scored[:max_results]]


def _tokenize(text: str) -> set[str]:
    """Extract search tokens from *text*, handling ASCII and Han ideographs."""
    # ASCII word tokens (3+ chars)
    ascii_tokens = {t for t in re.findall(r"[A-Za-z0-9_]+", text.lower()) if len(t) >= 3}
    # Han ideographs (each character carries independent meaning)
    han_chars = set(re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf]", text))
    return ascii_tokens | han_chars
