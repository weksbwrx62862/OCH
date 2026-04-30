# Tasks - MSA 集成实现任务列表 (v2)

## Phase 1: 基础配置与桥接层 ✅

- [x] Task 1: 创建 MSA 配置模块 ✅
  - [x] 创建 `backend/openharness/msa/__init__.py` ✅
  - [x] 创建 `backend/openharness/msa/config.py`，实现 OCHMSAConfig 数据类 ✅
  - [x] 创建 `backend/openharness/msa/types.py`，定义 MemorySearchResult, MSAHealthStatus, EncodeStats 等共享类型 ✅
  - [x] 在 `backend/openharness/config/settings.py` 添加 msa 配置段（默认 disabled）✅
  - [x] 验证：配置可通过 Settings 对象访问，默认值正确 ✅

- [x] Task 2: 实现记忆格式转换桥接 (MSABridge) ✅
  - [x] 创建 `backend/openharness/msa/bridge.py` ✅
  - [x] 实现 MemoryFact → Document 转换（content→doc, id→doc_id, category 分组策略）✅
  - [x] 实现 AgentMemory (JSON) → Document 转换（MemoryEntry 合并为 Document）✅
  - [x] 实现 doc_id → 原始记忆对象的反向映射表（id_map）✅
  - [x] 实现增量同步逻辑（版本号追踪 / 哈希比对）✅
  - [x] 实现 `sync_all()` 全量同步方法 ✅
  - [x] 实现 `sync_incremental()` 增量同步方法 ✅
  - [x] 验证：给定测试数据能正确双向转换 ✅

---

## Phase 2: MSA 服务封装 ✅

- [x] Task 3: 实现 MSA 服务包装器 (MSAServiceWrapper) ✅
  - [x] 创建 `backend/openharness/msa/service_wrapper.py` ✅
  - [x] 引用 MSA 源码（作为 submodule 或 sys.path 引入 `/home/xxh/claudecode源码(仅用于学习交流)/MSA-main/src`）✅
  - [x] 实现 `async initialize(config)` — 加载模型、启动 Engine、执行编码 ✅
  - [x] 实现 `async recall(query, top_k)` — 构造输入 → 调用 generate() → 解析结果 ✅
  - [x] 实现 `async encode_documents(docs)` — 触发 Prefill Stage 1 ✅
  - [x] 实现 `async health_check()` — 返回状态信息 ✅
  - [x] 实现 `async shutdown()` — 优雅关闭 ✅
  - [x] 实现 auto_fallback 逻辑（异常捕获 + 回退调用）✅
  - [x] 验证：单卡环境下可完成初始化→检索→关闭全流程 ✅

- [x] Task 4: 实现统一检索接口 (MSARetriever) ✅
  - [x] 创建 `backend/openharness/msa/retriever.py` ✅
  - [x] 实现 MSARetriever 类（单例/懒初始化模式）✅
  - [x] 实现 `async search(query, top_k, categories)` 统一入口 ✅
  - [x] 实现后端自动选择逻辑（MSA available? → MSA : keyword fallback）✅
  - [x] 实现结果标准化（两种后端返回相同格式）✅
  - [x] 验证：MSA 启用时走 MSA 路径；未启动时回退到关键词 ✅

---

## Phase 3: 后端集成 ✅

- [x] Task 5: 改造 memory/search.py ✅
  - [x] 新增 `msa_find_relevant_memories(query, cwd, max_results)` 函数 ✅
  - [x] 内部调用 MSARetriever.search() 并转换为 list[MemoryHeader] ✅
  - [x] 修改 `find_relevant_memories()` 增加 `backend` 参数（keyword/msa/auto）✅
  - [x] 默认值 `backend="keyword"` 保持向后兼容 ✅
  - **BREAKING**: 无（默认行为不变）✅
  - [x] 验证：原有测试全部通过；msa 模式返回语义相关结果 ✅

- [x] Task 6: 改造 AgentMemory 集成 MSA ✅
  - [x] AgentMemory.__init__() 接收可选 msa_config 参数 ✅
  - [x] recall() 增加 use_msa 参数和自动选择逻辑 ✅
  - [x] remember() 在 encode_on_write=True 时标记待编码 ✅
  - [x] 新增 `_msa_pending_encode` 队列管理待编码条目 ✅
  - [x] 验证：AgentMemory 单元测试通过；MSA 路径返回正确结果 ✅

- [x] Task 7: 改造 prompts/context.py 注入 MSA 上下文 ✅
  - [x] build_runtime_system_prompt() 中增加 MSA 检索调用 ✅
  - [x] 格式化为 "# MSA Relevant Memories" 段落（含相关度分数）✅
  - [x] 总 memory 注入受 max_tokens 限制 ✅
  - [x] MSA 未启用时不注入额外内容 ✅
  - [x] 验证：启用 MSA 时 prompt 包含语义检索结果 ✅

---

## Phase 4: API 与 QueryEngine ✅

- [x] Task 8: 扩展 REST API ✅
  - [x] POST `/api/v1/memory/msa/init` — 初始化 MSA 服务 ✅
  - [x] POST `/api/v1/memory/msa/encode` — 触发编码，返回 EncodeStats ✅
  - [x] POST `/api/v1/memory/msa/recall` — 语义检索 API ✅
  - [x] GET `/api/v1/memory/msa/status` — 服务状态查询 ✅
  - [x] DELETE `/api/v1/memory/msa/shutdown` — 关闭服务 ✅
  - [x] 所有端点需要 @require_auth 认证 ✅
  - [x] 编写 API 测试 ✅

- [x] Task 9: QueryEngine 可选集成 ✅
  - [x] QueryEngine.__init__() 接收可选 msa_retriever 参数 ✅
  - [x] submit_message() 中可选调用 MSA 检索并注入上下文 ✅
  - [x] 不传 msa_retriever 时行为完全不变 ✅
  - [x] 验证：集成测试通过 ✅

---

## Phase 5: 编码工作流与监控 🔄

- [x] Task 10: 实现离线编码管理 (EncoderWorker) ✅
  - [x] 创建 `backend/openharness/msa/encoder_worker.py` ✅
  - [x] 实现后台编码任务队列 ✅
  - [x] 实现编码进度回调/状态持久化 ✅
  - [x] 支持手动触发全量编码和自动增量编码 ✅
  - [x] 验证：编码完成后 KV 缓存可被检索使用 ✅

- [ ] Task 11: 测试与基准测试 🔄
  - [x] MSABridge 双向转换测试 ✅
  - [x] MSAServiceWrapper 生命周期测试（init → recall → shutdown）✅
  - [x] MSARetriever 回退机制测试 ✅
  - [x] memory/search.py 集成测试 ✅
  - [x] AgentMemory MSA 路径测试 ✅
  - [x] API 端点测试 ✅
  - [ ] 性能 benchmark（编码吞吐、检索延迟、显存占用）

---

## 遗留任务（补充完善）

- [x] Task 12: 无 GPU 环境优雅禁用 ✅
  - [x] 在 OCHMSAConfig 中增强 GPU 检测 ✅
  - [x] 在 MSAServiceWrapper.initialize() 中添加无 GPU 时的优雅降级 ✅
  - [x] 验证：无 GPU 环境下 MSA 功能自动禁用不报错 ✅

- [x] Task 13: flash-attn 依赖检测与提示 ✅
  - [x] 在初始化前检测 flash-attn 是否安装 ✅
  - [x] 未安装时给出清晰的安装提示和替代方案 ✅
  - [x] 验证：未安装 flash-attn 时不会导致系统崩溃 ✅

---

# Task Dependencies

```
Task 1 (配置) ──┬──> Task 2 (Bridge) ──┬──> Task 3 (ServiceWrapper) ──> Task 4 (Retriever)
                │                       │
                │                       └──> Task 10 (EncoderWorker)
                │
                └──> Task 5 (search.py)  ←──┐
                                          │
Task 6 (AgentMemory) ←── Task 4 ─────────┤
                        │                  │
Task 7 (context.py) ←──┘                  │
                                           │
Task 8 (API) ←── Task 4 ──────────────────┤
                    │                      │
Task 9 (QueryEngine) ←────────────────────┘
                          │
Task 11 (Tests) ────────依赖 Task 5,6,7,8,9
                          │
Task 12,13 (补充) ──────依赖 Task 3
```

**可并行执行的组**：
- Group A: Task 1 （无依赖）
- Group B: Task 2 （依赖 Task 1）
- Group C: Task 3 （依赖 Task 1）
- Group D: Task 5, Task 6 （依赖 Task 4，可并行）
- Group E: Task 7, Task 8, Task 9 （依赖 Task 4+D，可并行）
- Group F: Task 10 （依赖 Task 3，可与 D/E 并行）
- Group G: Task 12, 13 （依赖 Task 3，可并行）
