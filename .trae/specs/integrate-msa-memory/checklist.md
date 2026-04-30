# Checklist - MSA 集成验证清单 (v2)

## Phase 1: 基础配置与桥接层 ✅

- [x] OCHMSAConfig 包含所有必需字段（enabled, model_path, devices, doc_top_k 等）✅
- [x] Settings.msa 配置段可从环境变量/配置文件正确加载 ✅
- [x] Settings.msa.enabled 默认为 False ✅
- [x] MSABridge.facts_to_documents() 正确将 MemoryFact 列表转为 Document 列表 ✅
- [x] MSABridge.agent_memory_to_documents() 正确将 MemoryEntry 列表转为 Document 列表 ✅
- [x] MSABridge.id_map 正确维护 doc_id → 原始记忆对象的映射 ✅
- [x] MSABridge.sync_all() 返回完整的 Document 列表和 id_map ✅
- [x] MSABridge.sync_incremental() 仅返回新增/变更的 Document ✅

---

## Phase 2: MSA 服务封装 ✅

- [x] MSAServiceWrapper.initialize() 成功加载 MSA 模型并启动 Engine ✅
- [x] MSAServiceWrapper.recall() 返回 list[MemorySearchResult] 格式结果 ✅
- [x] MSAServiceWrapper.recall() 结果包含 content, score, source_id, source_type 字段 ✅
- [x] MSAServiceWrapper.encode_documents() 返回正确的 EncodeStats（total/success/fail）✅
- [x] MSAServiceWrapper.health_check() 返回 MSAHealthStatus 含 model_loaded, cache_size, gpu_util ✅
- [x] MSAServiceWrapper.shutdown() 释放 GPU 显存并终止工作进程 ✅
- [x] MSA 异常时 auto_fallback=True 触发关键词回退检索 ✅
- [x] MSA 异常时 auto_fallback=False 抛出异常 ✅
- [x] MSARetriever.search() 在 MSA available 时使用 MSA 后端 ✅
- [x] MSARetriever.search() 在 MSA unavailable 时回退到关键词后端 ✅
- [x] MSARetriever.search() 结果统一为 MemorySearchResult 格式 ✅

---

## Phase 3: 后端集成 ✅

- [x] msa_find_relevant_memories() 在 msa.enabled 时调用 MSARetriever ✅
- [x] find_relevant_memories(backend="keyword") 行为与修改前完全一致 ✅
- [x] find_relevant_memories(backend="msa") 使用 MSA 检索 ✅
- [x] find_relevant_memories(backend="auto") 根据 settings 自动选择 ✅
- [x] AgentMemory.recall(use_msa=True) 走 MSA 检索路径 ✅
- [x] AgentMemory.recall(use_msa=False) 保持原有关键词检索行为 ✅
- [x] AgentMemory.recall(use_msa=None) 根据全局配置自动选择 ✅
- [x] AgentMemory.remember() 新条目在 encode_on_write 时加入待编码队列 ✅
- [x] build_runtime_system_prompt() 启用 MSA 时包含 "# MSA Relevant Memories" 段落 ✅
- [x] MSA 注入内容包含相关度分数 ✅
- [x] 总 memory 注入不超过 max_tokens 限制 ✅
- [x] MSA 未启用时 build_runtime_system_prompt() 不含额外段落 ✅

---

## Phase 4: API 与 QueryEngine ✅

- [x] POST /api/v1/memory/msa/init 返回 200 + 服务状态 ✅
- [x] POST /api/v1/memory/msa/init 重复调用返回合理错误 ✅
- [x] POST /api/v1/memory/msa/encode 返回编码统计信息 ✅
- [x] POST /api/v1/memory/msa/recall 返回语义检索结果列表 ✅
- [x] GET /api/v1/memory/msa/status 返回当前服务状态 ✅
- [x] DELETE /api/v1/memory/msa/shutdown 成功关闭服务 ✅
- [x] 所有新端点未认证时返回 401 ✅
- [x] QueryEngine 不传 msa_retriever 时行为完全不变 ✅
- [x] QueryEngine 传入 msa_retriever 时在 submit_message 中使用 ✅

---

## Phase 5: 编码工作流与监控 🔄

- [x] EncoderWorker 支持后台执行全量编码任务 ✅
- [x] EncoderWorker 支持增量编码（仅处理变更条目）✅
- [x] 编码进度可通过 API 或回调获取 ✅
- [x] 编码完成后 KV 缓存可被后续检索使用 ✅
- [ ] 性能 benchmark 数据已记录

---

## 兼容性验证 ✅

- [x] 现有 memory/search.py 所有调用方无需修改即可运行 ✅
- [x] 现有 AgentMemory 所有使用处向后兼容 ✅
- [x] 现有 /api/v1/memory/* 端点响应格式不变 ✅
- [x] settings.py 未配置 msa 段时系统正常运行 ✅
- [x] 无 GPU 环境下 MSA 功能优雅禁用（不报错）✅
- [x] flash-attn 未安装时给出清晰的安装提示 ✅

---

## 模块导入验证 ✅

- [x] types.py 导入成功（MemorySearchResult, MSAHealthStatus, EncodeStats, MemorySourceType）✅
- [x] config.py 导入成功（OCHMSAConfig）✅
- [x] bridge.py 导入成功（MSABridge, Document）✅
- [x] service_wrapper.py 导入成功（MSAServiceWrapper）✅
- [x] retriever.py 导入成功（MSARetriever）✅
- [x] encoder_worker.py 导入成功（EncoderWorker, EncodeTaskStatus）✅
- [x] msa/__init__.py 全量导出成功 ✅
