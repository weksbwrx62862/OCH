# MSA (Memory Sparse Attention) 集成方案 Spec v2

## Why

当前 OpenClaw-Harness 的 Agent 记忆系统存在以下瓶颈：

1. **`memory/search.py`** 使用简单关键词匹配（token 集合交集），无语义理解
2. **`AgentMemory._compute_relevance()`** 仅支持子串包含匹配
3. **对话历史受 LLM 上下文窗口限制**（128K-1M），无法利用长期经验
4. 多 Agent 协作时无法跨 Agent 共享大规模记忆

MSA（基于 [EverMind-AI/MSA](https://github.com/EverMind-AI/MSA)）提供：
- 基于 Qwen3-4B 的**端到端可训练稀疏注意力**，支持 **1 亿 token 上下文**
- **三阶段流水线**：离线编码 → 在线路由(Top-k) → 稀疏生成
- **KV 缓存压缩 + 分层存储**（K 路由键驻留 GPU，V 内容存 CPU）
- **文档级 RoPE**：每个文档位置从 0 重置，支持外推
- **多 GPU 并行推理**（NCCL All-to-All 分布式打分）

### MSA 源码核心组件分析

```
MSA-main/src/
├── msa/
│   ├── __init__.py              # 导出: MSAGenerationMixin, MemorySparseAttention, MSAConfig
│   ├── memory_sparse_attention.py  # ★ 核心: MemorySparseAttention(Qwen3Attention)
│   │   ├── forward_with_kvcache_for_batch_parrallel()  # 推理时的三阶段处理
│   │   ├── _calculate_routing_scores_adaptive()         # 自适应路由打分
│   │   └── sequence_pooling_kv()                       # 分块均值池化
│   ├── configuration_msa.py     # MSAConfig(Qwen3Config) + DotDict
│   ├── model.py                 # MSAForCausalLM
│   └── generate.py              # MSAGenerationMixin
├── msa_service.py               # ★ 服务层: Memory, MSAService, MSAEngine
│   ├── Memory (GpuWorker)       # 单 GPU 记忆工作进程
│   │   ├── generate_blocks()    # Prefill Stage 1: 文档 → 压缩 KV 缓存
│   │   ├── prefill_stage2()     # Stage 2: 查询 → Top-K 路由 + KV 提取
│   │   ├── serialize()/deserialize()  # KV 缓存持久化
│   │   └── _generate_slice()    # 分片加速检索
│   ├── MSAService(Memory, MemoryClientBase)  # NCCL 多卡协调
│   │   └── doc_query()          # 分布式 All-Gather + All-to-All 检索
│   └── MSAEngine                # 多进程引擎管理器
├── config/memory_config.py      # GenerateConfig, ModelConfig, MemoryConfig
├── prefill.py                   # PrefillStage1Worker (子进程)
└── utils/cache.py               # CustomDynamicCache
```

## What Changes

### 新增模块
- **`backend/openharness/msa/`** — MSA 集成适配层（非直接复制 MSA 源码）
  - `__init__.py` — 模块导出
  - `config.py` — OCH 侧 MSA 配置（OCHMSAConfig），桥接 MSA 原始配置
  - `bridge.py` — **核心桥接层**: 将 OCH 记忆系统转换为 MSA Document 格式
  - `service_wrapper.py` — 封装 MSAEngine/MSAService 为异步接口
  - `retriever.py` — OCH 统一检索接口，屏蔽 MSA 底层复杂度
  - `encoder_worker.py` — 离线编码任务管理（后台执行）

### 修改模块
- **`backend/openharness/memory/search.py`**
  - 新增 `msa_semantic_search()` 作为 MSA 语义检索入口
  - 保留原有 `find_relevant_memories()` 作为 fallback
  - 根据 Settings 自动选择后端

- **`backend/openharness/coordinator/agent_memory.py`**
  - `AgentMemory` 新增 `_msa_bridge` 可选属性
  - `recall()` 增加 MSA 语义检索路径
  - `remember()` 触发增量编码标记

- **`backend/openharness/prompts/context.py`**
  - `build_runtime_system_prompt()` 增加 MSA 上下文注入

- **`backend/openharness/engine/query_engine.py`**
  - 可选注入 `MSARetriever`

- **`backend/app/api/memory.py`**
  - 新增 MSA 相关 API 端点

- **`backend/openharness/config/settings.py`**
  - 新增 `msa` 配置段

### 架构关系图

```
OpenClaw-Harness                    MSA (EverMind-AI)
=================                    ================

AgentMemory (JSON)  ──┐
                      ├──→ MSABridge ──→ List[Document] ──→ MSAEngine
MemoryFact (DB)     ──┘                     │
                                              ▼
                                   ┌─────────────────────┐
                                   │  Prefill Stage 1     │
                                   │  文档 → K̄/V̄/K̄ᵟ     │
                                   │  (离线/增量)          │
                                   └──────────┬──────────┘
                                              │
                                   ┌──────────▼──────────┐
                                   │  Prefill Stage 2     │
                                   │  Query → Top-K 路由   │
                                   │  + KV 提取            │
                                   └──────────┬──────────┘
                                              │
                                   ┌──────────▼──────────┐
                                   │  Generate            │
                                   │  稀疏上下文生成       │
                                   └──────────┬──────────┘
                                              │
                              MSARetriever ←──┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
           memory/search.py   agent_memory.py   context.py
           (语义检索)         (recall增强)      (prompt注入)
```

---

## ADDED Requirements

### Requirement: MSA 桥接配置 (OCHMSAConfig)

系统 SHALL 提供 OCHMSAConfig 数据类：

```python
@dataclass
class OCHMSAConfig:
    """OpenClaw-Harness 侧 MSA 集成配置"""
    enabled: bool = False
    model_path: str = "EverMind-AI/MSA-4B"        # MSA 模型路径
    devices: list[int] = field(default_factory=lambda: [])  # GPU 设备列表, 空=自动检测
    doc_top_k: int = 16                            # Top-K 检索文档数
    pooling_kernel_size: int = 64                  # 分块池化大小
    router_layer_idx: str = "all"                  # 路由层配置
    max_generate_tokens: int = 256                 # 最大生成长度
    cache_dir: Path | None = None                  # KV 缓存目录 (~/.openharness/msa_cache/)
    encode_on_write: bool = True                   # 写入时自动触发增量编码
    auto_fallback: bool = True                     # MSA 不可用时自动回退
    temperature: float = 0.0
    top_p: float = 0.9
```

#### Scenario: 默认禁用
- **WHEN** 未配置或 `enabled=False`
- **THEN** 所有现有行为不变，MSA 不参与任何流程

#### Scenario: 启用 MSA
- **WHEN** 设置 `och.msa.enabled = True`
- **THEN** 系统初始化 MSAEngine 并加载模型到指定 GPU
- **AND** 扫描现有记忆并触发首次编码

### Requirement: 记忆格式转换桥接 (MSABridge)

系统 SHALL 提供 MSABridge 类，负责 OCH 记忆格式 ↔ MSA Document 格式的双向转换：

#### MSA Document 格式（来自源码）:
```python
@dataclass
class Document:
    doc: str = ""          # 原始文本内容
    doc_id: int = 0        # 全局唯一文档 ID
    num_chunks: int = 0    # 分块数量（自动计算）
```

#### 功能要求：
1. **MemoryFact → Document**: 将 DB 中的结构化事实转为 MSA 文档
   - content 字段作为 doc 文本
   - id 作为 doc_id
   - 按 category 分组或合并为单个文档

2. **AgentMemory → Document**: 将 JSON 记忆文件转为 MSA 文档
   - 每个 MemoryEntry 可合并为一个 Document
   - 按 category/time_range 分组

3. **Document → 检索结果映射**: MSA 返回的 doc_id 映射回原始记忆对象

4. **增量同步**: 追踪已编码版本号，仅转换新增/变更条目

#### Scenario: 全量转换
- **WHEN** 首次启用 MSA 或调用全量同步 API
- **THEN** Bridge 扫描所有活跃 MemoryFact 和 AgentMemory
- **AND** 转换为 List[Document] 并返回
- **AND** 记录快照哈希用于后续增量判断

#### Scenario: 增量转换
- **WHEN** 有新记忆写入且 `encode_on_write=True`
- **THEN** Bridge 仅转换变更的条目
- **AND** 返回增量 Document 列表

### Requirement: MSA 服务封装 (MSAServiceWrapper)

系统 SHALL 提供 MSAServiceWrapper 类，封装 MSAEngine 为异步 Python 接口：

#### 功能要求：
1. **异步初始化**: `async def initialize(config: OCHMSAConfig)`
   - 加载 MSA 模型到指定 GPU
   - 启动 MSAEngine 工作进程
   - 加载或执行文档编码

2. **异步语义检索**: `async def recall(query: str, top_k: int) -> list[MemorySearchResult]`
   - 内部调用 MSAEngine.generate()
   - 解析返回结果并映射回 OCH 记忆格式
   - 包含相关性得分

3. **异步编码**: `async def encode_documents(docs: list[Document]) -> EncodeStats`
   - 触发 Prefill Stage 1
   - 返回编码统计信息

4. **优雅关闭**: `async def shutdown()`
   - 停止所有工作进程
   - 释放 GPU 显存

5. **健康检查**: `async def health_check() -> MSAHealthStatus`
   - 返回模型状态、缓存大小、GPU 利用率等

#### Scenario: 检索请求
- **WHEN** 调用 `wrapper.recall("如何处理权限错误", top_k=5)`
- **THEN** 内部构造 MSA 输入格式并调用 generate()
- **AND** 返回 `list[MemorySearchResult]` 包含 {content, score, source_id, source_type}
- **AND** 若 MSA 异常且 `auto_fallback=True`，回退到关键词检索

### Requirement: 统一检索接口 (MSARetriever)

系统 SHALL 提供 MSARetriever 作为 OCH 侧统一入口：

```python
class MSARetriever:
    async def search(self, query: str, *, top_k: int = 5,
                     categories: list[str] | None = None) -> list[MemorySearchResult]:
        """统一检索入口，内部选择最优后端"""
```

#### 功能要求：
1. **后端自动选择**: 根据 MSA 可用性和配置选择检索后端
2. **结果标准化**: 无论哪个后端，返回统一的 MemorySearchResult 格式
3. **混合模式**: 可同时查询两个后端并合并去重（可选）

#### Scenario: MSA 可用时
- **WHEN** MSA 已初始化且 healthy
- **THEN** 使用 MSA 语义检索
- **AND** 结果按相关性得分排序

#### Scenario: MSA 不可用时
- **WHEN** MSA 未初始化 / 异常 / 未启用
- **AND** `auto_fallback=True`
- **THEN** 回退到原有关键词检索
- **AND** 记录回退日志

### Requirement: memory/search.py 增强

新增函数 `msa_find_relevant_memories()`:

```python
def msa_find_relevant_memories(
    query: str,
    cwd: str | Path,
    *,
    max_results: int = 5,
) -> list[MemoryHeader]:
    """基于 MSA 语义检索的相关记忆"""
```

修改 `find_relevant_memories()` 增加 `backend` 参数:
- `backend="keyword"` (默认): 原有行为
- `backend="msa"`: 使用 MSA
- `backend="auto"`: 根据 settings 自动选择

### Requirement: AgentMemory 集成

`AgentMemory` 类修改：

1. **初始化**: 接收可选 `msa_config: OCHMSAConfig | None`
2. **recall() 方法签名扩展**:
   ```python
   async def recall(self, query, *, use_msa: bool | None = None, **kwargs):
       # use_msa=None → 根据全局配置决定
       # use_msa=True → 强制使用 MSA
       # use_msa=False → 强制使用关键词
   ```
3. **remember() 触发编码标记**: 当 `encode_on_write=True` 时，新条目加入待编码队列

### Requirement: System Prompt 注入

`build_runtime_system_prompt()` 修改：

在现有 "Relevant Memories" 段落后追加 MSA 检索结果：
```markdown
# MSA Relevant Memories (语义检索)
## 记忆来源1 (相关度: 0.92)
记忆内容...

## 记忆来源2 (相关度: 0.87)
记忆内容...
```

总 memory 注入 token 数受 `settings.memory.max_tokens` 限制。

### Requirement: REST API 扩展

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/v1/memory/msa/init` | 初始化 MSA 服务 |
| POST | `/api/v1/memory/msa/encode` | 触发（增量）编码 |
| POST | `/api/v1/memory/msa/recall` | MSA 语义检索 |
| GET | `/api/v1/memory/msa/status` | MSA 服务状态 |
| DELETE | `/api/v1/memory/msa/shutdown` | 关闭 MSA 服务 |

---

## MODIFIED Requirements

### Requirement: find_relevant_memories()
**原有**: 纯关键词启发式搜索
**修改后**: 支持 `backend` 参数选择检索后端，默认行为不变

### Requirement: AgentMemory.recall()
**原有**: 子串+标签关键词匹配
**修改后**: 支持 MSA 语义检索路径，保持返回类型一致

### Requirement: build_runtime_system_prompt()
**原有**: 从 MEMORY.md 加载记忆
**修改后**: 追加 MSA 语义检索结果段落

---

## REMOVED Requirements

无。完全向后兼容。

---

## Implementation Constraints

### 来自 MSA 源码的关键约束

| 约束 | 说明 | 影响 |
|------|------|------|
| **模型依赖** | MSA 必须使用 `EverMind-AI/MSA-4B` 或其微调版本 | 无法使用任意 LLM；需单独部署 MSA 模型 |
| **Flash Attention** | 必须安装 `flash-attn` | 需要 Ampere+ GPU (A100/RTX30+) |
| **Qwen3 Tokenizer** | 输入必须通过 Qwen3 tokenizer 编码 | Bridge 层需处理 tokenization |
| **多 GPU (推荐)** | 生产环境建议 ≥2× A800 | 单卡可运行但吞吐受限 |
| **doc_ids 编码** | 输入需标注 doc_ids (0=query, >0=doc, -2=template) | Bridge 需正确构造输入格式 |
| **NCCL** | 多卡通信依赖 NCCL | 需正确配置 CUDA/NCCL 环境 |

### 与 OCH 现有架构的兼容性约束

1. **异步兼容**: MSAEngine 使用多进程+队列，需包装为 asyncio 接口
2. **存储解耦**: MSA 有自己的 KV 缓存序列化格式，与 OCH 存储独立
3. **错误隔离**: MSA 故障不应影响 OCH 核心功能

---

## Dependencies

| 依赖 | 版本要求 | 用途 |
|------|----------|------|
| torch | >= 2.0 | 张量运算 |
| transformers | >= 4.36 | MSA 模型加载 |
| flash-attn | >= 2.0 | Flash Attention (必需) |
| accelerate | >= 0.26 | 模型设备映射 |
| sentence-transformers | >= 2.0 | 可选: 轻量级 fallback 嵌入 |

## Risk & Mitigations

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| MSA 模型加载失败 | 整个 MSA 功能不可用 | auto_fallback + 健康检查 |
| GPU 显存不足 | 无法启动 MSA 服务 | 支持 CPU-offload 模式；显存不足时优雅降级 |
| 首次编码耗时长 | 用户等待体验差 | 后台异步编码 + 进度 API |
| MSA 检索质量不达标 | Agent 行为退化 | A/B 测试 + 自动回退阈值 |
| KV 缓存膨胀 | 磁盘空间压力 | LRU 淘汰 + 压缩存储 |
| 进程管理复杂性 | 内存泄漏/僵尸进程 | 完善的生命周期管理 + watchdog |
