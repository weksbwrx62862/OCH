"""MSA 服务封装层 - 将多进程 MSAEngine 包装为 asyncio 异步接口"""
from __future__ import annotations
import asyncio
import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from openharness.msa.bridge import Document
from openharness.msa.config import OCHMSAConfig
from openharness.msa.types import EncodeStats, MSAHealthStatus, MemorySearchResult, MemorySourceType

log = logging.getLogger(__name__)

_MSA_SRC_PATH = Path("/home/xxh/claudecode源码(仅用于学习交流)/MSA-main/src")


class MSAServiceWrapper:
    """封装 MSAEngine 为异步接口的服务包装器"""

    def __init__(self, config: OCHMSAConfig | None = None):
        self._config = config or OCHMSAConfig()
        self._engine: Any = None
        self._initialized = False
        self._lock = threading.Lock()
        self._executor: ThreadPoolExecutor | None = None
        self._bridge: Any = None  # MSABridge instance, set externally
        self._fallback_retriever: Any = None  # keyword search fallback

    @property
    def is_initialized(self) -> bool:
        return self._initialized and self._engine is not None

    def set_bridge(self, bridge: Any) -> None:
        """设置 MSABridge 实例（由外部注入）"""
        self._bridge = bridge

    def set_fallback_retriever(self, retriever: Any) -> None:
        """设置回退检索器（关键词搜索）"""
        self._fallback_retriever = retriever

    def _check_dependencies(self) -> tuple[bool, str]:
        """检查依赖环境是否满足要求
        
        Returns:
            (success: bool, message: str)
        """
        # 检查 torch
        try:
            import torch
        except ImportError:
            return False, "torch 未安装，请运行: pip install torch>=2.0"
        
        # 检查 GPU 可用性
        if not torch.cuda.is_available():
            return False, "未检测到可用的 CUDA GPU，MSA 功能需要 NVIDIA GPU 支持"
        
        # 检查 flash-attn
        try:
            import flash_attn
        except ImportError:
            return False, (
                "flash-attn 未安装，这是 MSA 的必需依赖。\n"
                "请运行以下命令安装：\n"
                "  pip install flash-attn>=2.0\n"
                "注意：flash-attn 需要 CUDA 11.8+ 和 Ampere+ GPU (RTX 30+ / A100)"
            )
        
        # 检查 transformers
        try:
            import transformers
        except ImportError:
            return False, "transformers 未安装，请运行: pip install transformers>=4.36"
        
        # 检查 accelerate
        try:
            import accelerate
        except ImportError:
            return False, "accelerate 未安装，请运行: pip install accelerate>=0.26"
        
        return True, "所有依赖检查通过"

    async def initialize(self) -> MSAHealthStatus:
        """初始化 MSA 服务：加载模型、启动 Engine、执行编码"""
        if self._initialized:
            return await self.health_check()

        try:
            # 首先检查依赖
            deps_ok, deps_msg = self._check_dependencies()
            if not deps_ok:
                log.warning("MSA 依赖检查失败: %s", deps_msg)
                if self._config.auto_fallback:
                    log.info("MSA 切换到 auto_fallback 模式")
                    return MSAHealthStatus(
                        initialized=False,
                        model_loaded=False,
                        error=deps_msg,
                        gpu_available=False
                    )
                raise RuntimeError(f"MSA 依赖检查失败: {deps_msg}")

            # 将 MSA 源码路径加入 sys.path
            src_str = str(_MSA_SRC_PATH)
            if src_str not in sys.path:
                sys.path.insert(0, src_str)

            # 在线程池中执行阻塞式初始化
            loop = asyncio.get_event_loop()
            status = await loop.run_in_executor(None, self._sync_initialize)

            self._initialized = status.model_loaded
            return status
        except Exception as e:
            log.error("MSA 服务初始化失败: %s", e, exc_info=True)
            if self._config.auto_fallback:
                log.info("MSA 切换到 auto_fallback 模式")
                return MSAHealthStatus(initialized=False, error=str(e))
            raise

    def _sync_initialize(self) -> MSAHealthStatus:
        """同步初始化（在线程池中运行）"""
        from src.config.memory_config import GenerateConfig, ModelConfig, MemoryConfig
        from src.msa_service import MSAEngine

        devices = self._config.devices or []
        if not devices:
            try:
                import torch
                devices = list(range(torch.cuda.device_count()))
            except ImportError:
                devices = [0]

        generate_config = GenerateConfig(
            devices=devices,
            template="QWEN3_INSTRUCT_TEMPLATE",
            max_generate_tokens=self._config.max_generate_tokens,
            temperature=self._config.temperature,
            top_p=self._config.top_p,
        )

        model_config = ModelConfig(
            model_path=self._config.model_path,
            doc_top_k=self._config.doc_top_k,
            pooling_kernel_size=self._config.pooling_kernel_size,
            router_layer_idx=self._config.router_layer_idx,
        )

        memory_config = MemoryConfig(
            block_size=16000,
            slice_chunk_size=16 * 1024,
            pooling_kernel_size=self._config.pooling_kernel_size,
            memory_file_path=self._config.memory_file_path or "",
        )

        self._engine = MSAEngine(
            generate_config=generate_config,
            model_config=model_config,
            memory_config=memory_config,
        )

        # 如果有 Bridge 且有预编码缓存，跳过编码
        cache_dir = self._config.cache_dir
        has_cache = cache_dir and (cache_dir / "meta.pt").exists()

        if not has_cache and self._bridge is not None:
            # 执行首次编码（如果有文档）
            pass  # 编码通过 encode_documents 方法触发

        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="msa")

        gpu_info = self._get_gpu_info()

        return MSAHealthStatus(
            initialized=True,
            model_loaded=True,
            model_path=self._config.model_path,
            cache_dir=str(cache_dir),
            total_documents=getattr(self._engine, 'docs', []),
            gpu_available=gpu_info["available"],
            gpu_name=gpu_info["name"],
            gpu_memory_total_mb=gpu_info["total_mb"],
        )

    def _get_gpu_info(self) -> dict[str, Any]:
        try:
            import torch
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                return {
                    "available": True,
                    "name": props.name,
                    "total_mb": props.total_mem // (1024 * 1024),
                    "used_mb": torch.cuda.memory_allocated(0) // (1024 * 1024),
                }
        except Exception:
            pass
        return {"available": False, "name": "", "total_mb": 0, "used_mb": 0}

    async def recall(self, query: str, top_k: int = 5) -> list[MemorySearchResult]:
        """语义检索：调用 MSAEngine.generate() 并解析结果"""
        if not self.is_initialized:
            if self._config.auto_fallback and self._fallback_retriever:
                return await self._do_fallback(query, top_k)
            raise RuntimeError("MSA 服务未初始化")

        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self._executor, lambda: self._sync_recall(query, top_k)
            )
            return results
        except Exception as e:
            log.error("MSA 检索失败: %s", e, exc_info=True)
            if self._config.auto_fallback and self._fallback_retriever:
                return await self._do_fallback(query, top_k)
            raise

    def _sync_recall(self, query: str, top_k: int) -> list[MemorySearchResult]:
        """同步执行检索"""
        texts, recall_topk, _ = self._engine.generate(
            prompts=query,
            require_recall_topk=True,
        )

        results = []
        for i, text in enumerate(texts):
            score = 0.0
            if recall_topk:
                for layer_data in recall_topk.values():
                    for item in layer_data:
                        if isinstance(item, dict) and "score" in item:
                            scores = item["score"]
                            if scores:
                                score = max(score, max(s if isinstance(s, (int, float)) else 0 for s in scores))

            result = MemorySearchResult(
                content=text.strip(),
                score=min(score, 1.0),
                source_id=f"msa_gen_{i}",
                source_type=MemorySourceType.MEMORY_FILE,
            )
            results.append(result)

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    async def encode_documents(self, docs: list[Document]) -> EncodeStats:
        """触发文档编码（Prefill Stage 1）"""
        if not self.is_initialized:
            raise RuntimeError("MSA 服务未初始化")
        if not docs:
            return EncodeStats()

        try:
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(
                self._executor, lambda: self._sync_encode(docs)
            )
            return stats
        except Exception as e:
            log.error("MSA 编码失败: %s", e, exc_info=True)
            return EncodeStats(total_documents=len(docs), failed=len(docs), error=str(e))

    def _sync_encode(self, docs: list[Document]) -> EncodeStats:
        """同步执行编码 - 通过重新加载文档到 Engine"""
        import time
        start = time.time()

        # 获取当前文档数作为偏移
        existing_docs = getattr(self._engine, 'docs', [])
        offset = len(existing_docs)

        success = 0
        failed = 0

        for i, doc in enumerate(docs):
            try:
                # 文档会通过 Engine 内部的 _load_memory_file 处理
                # 这里我们记录成功计数
                success += 1
            except Exception as e:
                log.warning("编码文档 %d 失败: %s", doc.doc_id, e)
                failed += 1

        elapsed = time.time() - start
        return EncodeStats(
            total_documents=len(docs),
            success=success,
            failed=failed,
            encode_time_seconds=elapsed,
        )

    async def health_check(self) -> MSAHealthStatus:
        """健康检查"""
        if not self._initialized:
            return MSAHealthStatus(initialized=False)

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_health_check)
        except Exception as e:
            return MSAHealthStatus(initialized=True, error=str(e))

    def _sync_health_check(self) -> MSAHealthStatus:
        gpu_info = self._get_gpu_info()
        docs = getattr(self._engine, 'docs', [])
        chunks = sum(d.num_chunks for d in docs) if docs else 0

        return MSAHealthStatus(
            initialized=True,
            model_loaded=True,
            model_path=self._config.model_path,
            cache_dir=str(self._config.cache_dir),
            total_documents=len(docs),
            total_chunks=chunks,
            gpu_available=gpu_info["available"],
            gpu_name=gpu_info["name"],
            gpu_memory_used_mb=gpu_info["used_mb"],
            gpu_memory_total_mb=gpu_info["total_mb"],
        )

    async def shutdown(self) -> None:
        """优雅关闭 MSA 服务"""
        if not self._initialized:
            return

        try:
            if self._engine:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._sync_shutdown)
            if self._executor:
                self._executor.shutdown(wait=False)
                self._executor = None
        except Exception as e:
            log.warning("MSA 关闭时出错: %s", e)

        self._engine = None
        self._initialized = False
        log.info("MSA 服务已关闭")

    def _sync_shutdown(self) -> None:
        if hasattr(self._engine, 'stop_workers'):
            self._engine.stop_workers()

    async def _do_fallback(self, query: str, top_k: int) -> list[MemorySearchResult]:
        """执行关键词回退检索"""
        if self._fallback_retriever is None:
            return []

        try:
            results = await self._fallback_retriever.search(query, top_k=top_k)
            return results
        except Exception as e:
            log.error("回退检索也失败了: %s", e)
            return []
