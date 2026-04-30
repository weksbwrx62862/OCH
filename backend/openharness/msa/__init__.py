"""MSA（Memory Sparse Attention）集成模块

提供 OpenClaw-Harness 与 EverMind-AI/MSA 服务的集成能力，
包括配置管理、类型定义、记忆桥接、服务封装和统一检索接口。
"""

from openharness.msa.config import OCHMSAConfig
from openharness.msa.types import (
    EncodeStats,
    MemorySearchResult,
    MemorySourceType,
    MSAHealthStatus,
)
from openharness.msa.bridge import MSABridge, Document
from openharness.msa.service_wrapper import MSAServiceWrapper
from openharness.msa.retriever import MSARetriever
from openharness.msa.encoder_worker import EncoderWorker, EncodeTaskStatus

__all__ = [
    # 配置
    "OCHMSAConfig",
    # 类型
    "EncodeStats",
    "MemorySearchResult",
    "MemorySourceType",
    "MSAHealthStatus",
    # 桥接层
    "MSABridge",
    "Document",
    # 服务封装
    "MSAServiceWrapper",
    # 统一检索
    "MSARetriever",
    # 编码工作器
    "EncoderWorker",
    "EncodeTaskStatus",
]
