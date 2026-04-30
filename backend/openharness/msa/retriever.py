"""MSA 统一检索接口 - 自动选择最优检索后端"""
from __future__ import annotations
import logging
from typing import Any

from openharness.msa.types import MemorySearchResult, MemorySourceType, MSAHealthStatus
from openharness.msa.config import OCHMSAConfig
from openharness.msa.service_wrapper import MSAServiceWrapper
from openharness.msa.bridge import MSABridge

log = logging.getLogger(__name__)


class MSARetriever:
    """统一记忆检索入口 - 屏蔽 MSA 底层复杂度"""

    _instance: MSARetriever | None = None

    def __init__(
        self,
        config: OCHMSAConfig | None = None,
        wrapper: MSAServiceWrapper | None = None,
        bridge: MSABridge | None = None,
    ):
        self._config = config or OCHMSAConfig()
        self._wrapper = wrapper or MSAServiceWrapper(self._config)
        self._bridge = bridge or MSABridge()

        if self._bridge:
            self._wrapper.set_bridge(self._bridge)

        self._keyword_search_fn: Any = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> MSARetriever | None:
        """获取全局单例"""
        return cls._instance

    @classmethod
    def set_instance(cls, instance: MSARetriever) -> None:
        """设置全局单例"""
        cls._instance = instance

    def set_keyword_search(self, search_fn: Any) -> None:
        """设置关键词搜索回退函数
        
        Args:
            search_fn: 异步函数，签名 async fn(query, top_k) -> list[MemorySearchResult]
        """
        self._keyword_search_fn = search_fn
        self._wrapper.set_fallback_retriever(self)

    @property
    def is_available(self) -> bool:
        return self._config.enabled and self._wrapper.is_initialized

    @property
    def config(self) -> OCHMSAConfig:
        return self._config

    async def initialize(self) -> MSAHealthStatus:
        """初始化检索器（如果 MSA 启用）"""
        if not self._config.enabled:
            log.info("MSA 未启用，使用关键词检索模式")
            return MSAHealthStatus(initialized=False)

        try:
            status = await self._wrapper.initialize()
            self._initialized = status.model_loaded
            return status
        except Exception as e:
            log.warning("MSA 初始化失败，将使用关键词回退模式: %s", e)
            return MSAHealthStatus(initialized=False, error=str(e))

    async def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        categories: list[str] | None = None,
        force_backend: str | None = None,
    ) -> list[MemorySearchResult]:
        """统一检索入口 - 内部选择最优后端
        
        Args:
            query: 检索查询文本
            top_k: 返回结果数量上限
            categories: 可选的分类过滤列表
            force_backend: 强制指定后端 ("msa" / "keyword")，None=自动选择
            
        Returns:
            统一格式的 MemorySearchResult 列表
        """
        backend = force_backend or self._select_backend(query)
        
        log.debug(
            "记忆检索: query='%s', backend=%s, top_k=%d",
            query[:50], backend, top_k,
        )

        if backend == "msa":
            results = await self._msa_search(query, top_k=top_k)
        else:
            results = await self._keyword_search(query, top_k=top_k)

        # 分类过滤
        if categories and results:
            results = [r for r in results if r.category in categories or not r.category]

        return results[:top_k]

    def _select_backend(self, query: str) -> str:
        """根据配置和状态选择后端"""
        if not self._config.enabled:
            return "keyword"
        
        if not self._wrapper.is_initialized:
            if self._config.auto_fallback:
                log.info("MSA 未初始化，回退到关键词检索")
                return "keyword"
            raise RuntimeError("MSA 服务未初始化且 auto_fallback=False")

        return "msa"

    async def _msa_search(self, query: str, *, top_k: int) -> list[MemorySearchResult]:
        """执行 MSA 语义检索"""
        try:
            results = await self._wrapper.recall(query, top_k=top_k * 2)
            
            # 通过 Bridge 解析 doc_id 映射回原始来源
            resolved_results = []
            for r in results:
                try:
                    source_id_int = int(r.source_id.replace("msa_gen_", "")) if r.source_id.startswith("msa_gen_") else -1
                    if source_id_int >= 0 and self._bridge:
                        resolved = self._bridge.resolve_result(source_id_int, r.content, r.score)
                        resolved_results.append(resolved)
                    else:
                        resolved_results.append(r)
                except (ValueError, KeyError):
                    resolved_results.append(r)

            return resolved_results[:top_k]
        except Exception as e:
            log.error("MSA 检索异常: %s", e, exc_info=True)
            if self._config.auto_fallback:
                return await self._keyword_search(query, top_k=top_k)
            raise

    async def _keyword_search(self, query: str, *, top_k: int) -> list[MemorySearchResult]:
        """执行关键词回退检索"""
        if self._keyword_search_fn is None:
            log.warning("未设置关键词搜索函数，返回空结果")
            return []

        try:
            results = await self._keyword_search_fn(query, top_k=top_k)
            return results
        except Exception as e:
            log.error("关键词搜索也失败了: %s", e, exc_info=True)
            return []

    async def health_check(self) -> MSAHealthStatus:
        """健康检查"""
        if not self._config.enabled:
            return MSAHealthStatus(initialized=False)
        return await self._wrapper.health_check()

    async def shutdown(self) -> None:
        """关闭检索器"""
        await self._wrapper.shutdown()
        self._initialized = False

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "msa_enabled": self._config.enabled,
            "msa_initialized": self._initialized,
            "msa_available": self.is_available,
            "auto_fallback": self._config.auto_fallback,
            "has_keyword_fallback": self._keyword_search_fn is not None,
            "bridge_stats": self._bridge.get_stats() if self._bridge else {},
        }
