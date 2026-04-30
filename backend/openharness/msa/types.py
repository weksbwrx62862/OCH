from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class MemorySourceType(str, Enum):
    """记忆来源类型"""

    MEMORY_FACT = "memory_fact"
    AGENT_MEMORY = "agent_memory"
    MEMORY_FILE = "memory_file"


@dataclass
class MemorySearchResult:
    """统一记忆检索结果"""

    content: str
    score: float = 0.0
    source_id: str = ""
    source_type: MemorySourceType = MemorySourceType.MEMORY_FACT
    category: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class MSAHealthStatus:
    """MSA 服务健康状态"""

    initialized: bool = False
    model_loaded: bool = False
    model_path: str = ""
    cache_dir: str = ""
    cache_size_bytes: int = 0
    total_documents: int = 0
    total_chunks: int = 0
    gpu_available: bool = False
    gpu_name: str = ""
    gpu_memory_used_mb: int = 0
    gpu_memory_total_mb: int = 0
    error: str = ""


@dataclass
class EncodeStats:
    """编码统计信息"""

    total_documents: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0
    total_chunks: int = 0
    encode_time_seconds: float = 0.0
    cache_size_bytes: int = 0
