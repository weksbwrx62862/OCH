# OpenHarness v0.3.0 — Phase 1 核心功能实施计划

**计划日期**: 2026-04-06
**基于版本**: v0.2.0（511 测试通过，14 子系统）
**目标**: 实现路线图中推荐的 3 个高价值功能增强

***

## 📋 任务总览

| #        | 功能                          | 工作量             | 文件变更                | 新增测试 |
| -------- | --------------------------- | --------------- | ------------------- | ---- |
| **T1.1** | 缓存微压缩 (Cached Microcompact) | \~200 行新代码 + 修改 | 2 源码 + 1 测试         | \~10 |
| **T1.2** | Agent 内存管理系统 (Agent Memory) | \~250 行新代码      | 1 新源码 + 1 修改 + 1 测试 | \~12 |
| **T1.3** | 团队文件增强 (TeamFile V2)        | \~150 行修改       | 2 源码 + 1 测试         | \~8  |

***

## T1.1: 缓存微压缩 (Cached Microcompact)

### 背景

当前 `microcompact_messages()` 在清除旧工具输出时，被删除的内容**永久丢失**。Anthropic 的 prompt caching 技术允许在 API 调用间复用已缓存的前缀内容，但如果工具输出已被替换为 `[Old tool result content cleared]`，缓存命中率会下降。

### 设计

```
传统微压缩:
  [tool_use: read_file] → [tool_result: "5000 字符的文件内容"]
  ↓ microcompact
  [tool_use: read_file] → [tool_result: "[Old tool result content cleared]"]  ← 信息丢失！

缓存微压缩:
  [tool_use: read_file] → [tool_result: "5000 字符的文件内容"]
  ↓ cached_microcompact
  [tool_use: read_file] → [tool_result: "[Old tool result content cleared]"]
  同时记录到 CacheEntry:
    {tool_id, original_content_hash, summary_snippet(前100字符), timestamp}
  
  当 API 支持 cache editing 时，可从缓存恢复原始内容
  当前模式：保留摘要用于调试和上下文重建
```

### 数据模型

```python
@dataclass
class CachedToolResult:
    """被缓存的工具输出条目"""
    tool_id: str                    # 对应 ToolUseBlock.id
    tool_name: str                  # 工具名 (read_file, bash 等)
    content_hash: str               # SHA256 原始内容的哈希
    summary: str                    # 前 100 字符摘要（用于快速预览）
    original_length: int            # 原始内容长度（字符数）
    estimated_tokens: int           # 估算的 token 数
    cleared_at: float               # 清除时间戳 (time.time())
    content: str | None = None      # 可选：保留完整内容（内存模式）
```

```python
@dataclass
class CompactCache:
    """微压缩缓存管理器"""
    
    config: CompactCacheConfig       # 配置
    _entries: dict[str, CachedToolResult]  # tool_id → entry
    
    # --- 核心方法 ---
    def record_cleared(self, tool_id, tool_name, content) -> None:
        """记录一条被清除的工具输出"""
        
    def lookup(self, tool_id) -> CachedToolResult | None:
        """查找缓存条目"""
        
    def get_stats(self) -> dict:
        """返回缓存统计信息"""
        
    def clear_expired(self, max_age_seconds: float = 3600) -> int:
        """清理过期条目（默认 1 小时），返回清理数量"""
        
    def restore_for_tool_ids(self, tool_ids: list[str]) -> dict[str, str]:
        """批量恢复指定 tool_id 的完整内容 → {tool_id: content}"""
```

```python
@dataclass
class CompactCacheConfig:
    """缓存配置"""
    enabled: bool = True             # 是否启用缓存
    keep_full_content: bool = False   # 是否保留完整内容（True = 更多内存但可恢复）
    max_entries: int = 500            # 最大缓存条目数
    default_expiry_seconds: float = 3600  # 默认过期时间（秒）
    summary_max_length: int = 100     # 摘要最大长度
```

### 修改现有函数

**文件**: `src/openharness/services/compact/__init__.py`

修改 `microcompact_messages_time_aware()` 函数签名：

```python
def microcompact_messages_time_aware(
    messages,
    *,
    config: MicrocompactConfig | None = None,
    message_timestamps: list[float] | None = None,
    cache: CompactCache | None = None,  # ← 新增参数
) -> tuple[list[ConversationMessage], int]:
```

在清除每个 `ToolResultBlock` 时：

1. 如果 `cache` 不为 None 且 `cache.config.enabled` 为 True
2. 调用 `cache.record_cleared(block.tool_use_id, tool_name, block.content)`
3. 返回值不变（向后兼容）

新增函数 `cached_microcompact_messages()` 作为便捷包装：

```python
async def cached_microcompact_messages(
    messages,
    *,
    config: MicrocompactConfig | None = None,
    cache: CompactCache | None = None,
    message_timestamps: list[float] | None = None,
) -> tuple[list[ConversationMessage], int, CompactCache]:
    """带缓存的微压缩（自动创建 cache 如果未提供）"""
    if cache is None:
        cache = CompactCache()
    saved_msgs, tokens_saved = microcompact_messages_time_aware(
        messages, config=config, message_timestamps=message_timestamps, cache=cache
    )
    return saved_msgs, tokens_saved, cache
```

### 文件清单

| 操作     | 文件路径                                                 | 说明                                                                 |
| ------ | ---------------------------------------------------- | ------------------------------------------------------------------ |
| **新建** | `src/openharness/services/compact/cached_compact.py` | CachedToolResult, CompactCache, CompactCacheConfig (\~150 行)       |
| **修改** | `src/openharness/services/compact/__init__.py`       | 导出新增类/函数；`microcompact_messages_time_aware` 增加 cache 参数 (\~20 行改动) |
| **新建** | `tests/test_services/test_cached_compact.py`         | 缓存微压缩测试 (\~10 用例)                                                  |

### 验收标准

* [ ] `CompactCache.record_cleared()` 正确计算 SHA256 哈希和 token 估算

* [ ] `lookup()` 能找到刚记录的条目

* [ ] `clear_expired()` 删除超过 max\_age 的条目

* [ ] `restore_for_tool_ids()` 返回正确的内容映射

* [ ] `get_stats()` 返回正确的统计信息

* [ ] `microcompact_messages_time_aware(cache=...)` 在清除时自动记录缓存

* [ ] 不传 cache 时行为与之前完全一致（向后兼容）

* [ ] `keep_full_content=True` 时可恢复完整内容

* [ ] `keep_full_content=False` 时只保留摘要

* [ ] 所有原有 511 测试继续通过

***

## T1.2: Agent 内存管理系统 (Agent Memory)

### 背景

当前子 Agent（Worker）没有跨会话记忆能力。每次 Worker 启动都是「失忆」状态，无法利用之前的经验。Agent Memory 系统为每个 Agent 提供持久化的记忆存储。

### 设计

```
┌─────────────────────────────────────┐
│         AutonomousWorker              │
│                                      │
│  ┌──────────┐  ┌─────────────────┐  │
│  │ Mailbox  │  │ AgentMemory     │  │
│  │ (消息队列)│  │ (持久化记忆)    │  │
│  └──────────┘  └─────────────────┘  │
│         ↑                ↑          │
│    接收任务         记住经验        │
│                                      │
└─────────────────────────────────────┘
```

### 数据模型

```python
@dataclass
class MemoryEntry:
    """单条记忆条目"""
    id: str                         # UUID 格式唯一 ID
    agent_id: str                   # 所属 Agent ID
    category: str                   # 分类: general / error / pattern / decision / fact
    content: str                   # 记忆内容（自由文本）
    tags: list[str]                # 标签（便于检索）
    created_at: float               # 创建时间戳
    expires_at: float | None = None # 过期时间（None = 永不过期）
    importance: int = 5             # 重要程度 1-10（影响排序和保留策略）
    source_task_id: str | None = None  # 关联的任务 ID
```

```python
@dataclass
class MemoryQuery:
    """记忆查询条件"""
    query: str                      # 搜索关键词
    categories: list[str] | None = None  # 分类过滤
    tags: list[str] | None = None       # 标签过滤
    min_importance: int = 0             # 最低重要程度
    limit: int = 5                     # 最大返回数量
    include_expired: bool = False       # 是否包含已过期条目
```

```python
@dataclass
class AgentMemoryConfig:
    """Agent 记忆配置"""
    storage_path: str | None = None     # 存储路径（None = 使用默认 ~/.openharness/memory/）
    max_memories_per_agent: int = 200   # 每个 Agent 最大记忆数
    auto_expire_days: int = 30          # 自动过期天数（importance < 5 的条目）
    high_importance_keep_days: int = 90  # 高重要性条目保留天数
```

```python
class AgentMemory:
    """Agent 持久化记忆管理器"""
    
    def __init__(self, agent_id: str, config: AgentMemoryConfig | None = None):
        ...
    
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
        
    async def recall(self, query: MemoryQuery | str, **kwargs) -> list[MemoryEntry]:
        """根据查询检索相关记忆（支持模糊匹配和标签过滤）"""
        
    async def forget(self, memory_id: str) -> bool:
        """删除特定记忆"""
        
    async def forget_by_category(self, category: str) -> int:
        """按分类批量删除，返回删除数量"""
        
    async def consolidate(self) -> int:
        """整合重复/相似的记忆，返回合并数量"""
        
    def get_stats(self) -> dict:
        """返回记忆统计信息"""
        
    async def export_json(self, path: str) -> None:
        """导出所有记忆到 JSON 文件"""
        
    @classmethod
    async def import_json(cls, agent_id: str, path: str) -> AgentMemory:
        """从 JSON 文件导入记忆"""
```

### 存储后端

使用 JSON 文件存储（简单可靠，无需额外依赖）：

```
~/.openharness/memory/
├── worker-abc123.json          # Agent memory 文件（以 agent_id 命名）
├── researcher-def456.json
└── .gitignore                 # 不纳入版本控制
```

每行一个 MemoryEntry 的序列化 JSON。

### 与 AutonomousWorker 集成

修改 `AutonomousWorker.__init__()` 和 `_work_loop()`：

```python
# autonomous_worker.py 修改点:

# __init__ 中增加:
self.memory: AgentMemory | None = None  # 可选注入

# _work_loop 中:
# 1. 任务开始前: recall 相关记忆作为上下文
if self.memory:
    relevant = await self.memory.recall(f"task: {task_description}")
    if relevant:
        context_hint = "\n".join(f"[记忆] {m.content}" for m in relevant[:3])
        task_prompt = f"{task_prompt}\n\n历史经验:\n{context_hint}"

# 2. 任务完成后: 记录关键发现
if self.memory and task_result:
    await self.memory.remember(
        content=f"完成任务 '{subject}': {result_summary}",
        category="pattern",
        tags=[subject.split()[0]],
        importance=7 if success else 4,
        source_task_id=task.id,
    )
```

### 文件清单

| 操作     | 文件路径                                               | 说明                                                                 |
| ------ | -------------------------------------------------- | ------------------------------------------------------------------ |
| **新建** | `src/openharness/coordinator/agent_memory.py`      | AgentMemory, MemoryEntry, MemoryQuery, AgentMemoryConfig (\~250 行) |
| **修改** | `src/openharness/coordinator/autonomous_worker.py` | 注入 AgentMemory，在 work\_loop 中使用记忆 (\~30 行改动)                       |
| **新建** | `tests/test_coordinator/test_agent_memory.py`      | Agent Memory 测试 (\~12 用例)                                          |

### 验收标准

* [ ] `remember()` 创建 MemoryEntry 并持久化到 JSON

* [ ] `recall()` 支持文本模糊匹配、分类过滤、标签过滤、重要性过滤

* [ ] `forget()` 删除指定条目并更新文件

* [ ] `forget_by_category()` 批量删除

* [ ] `consolidate()` 合并相似记忆（相同 category + 相似 content 前 50 字符）

* [ ] `export_json()` / `import_json()` 往返序列化

* [ ] 过期机制正常工作（auto\_expire\_days / expires\_at）

* [ ] 统计信息准确

* [ ] AutonomousWorker 可选接受 memory 参数

* [ ] 有 memory 的 Worker 在执行任务前后自动 recall/remember

* [ ] 无 memory 时行为不变（向后兼容）

***

## T1.3: 团队文件增强 (TeamFile V2)

### 背景

当前 `TeamMember` 和 `TeamFile` 类型缺少 UI 显示所需的字段（颜色、状态）和权限粒度控制。参考 Claude Code `teamHelpers.ts` 的 TeamFile 类型定义进行增强。

### 数据模型变更

**文件**: `src/openharness/swarm/team_lifecycle.py`

扩展 `TeamMember` 类（第 92 行附近）：

```python
@dataclass
class TeamMemberV2:
    """团队成员（V2 增强版）"""
    agent_id: str                       # 唯一标识符
    name: str                           # 显示名称
    color: str = "blue"                # UI 显示颜色（AGENT_COLORS 之一）
    permission_mode: str = "default"    # 权限模式: default / acceptEdits / bypassPermissions / plan / dontAsk
    is_active: bool = True              # idle/active 状态标记
    worktree_path: str | None = None    # 成员专属 git worktree 路径
    
    # --- 以下字段保持兼容 ---
    role: str = "teammate"
    model: str | None = None
    system_prompt: str | None = None
```

扩展 `TeamFile` 类（第 190 行附近）：

```python
@dataclass
class TeamFileV2:
    """团队配置文件（V2 增强版）"""
    name: str
    description: str = ""
    created_at: float = field(default_factory=time.time)
    lead_agent_id: str = ""
    
    # --- 成员列表 ---
    members: list[TeamMemberV2] = field(default_factory=list)
    
    # --- 新增：团队级路径白名单 ---
    allowed_paths: list[AllowedPath] = field(default_factory=list)
    
    # --- 兼容性属性 ---
    backend_type: BackendType = "in_process"

@dataclass
class AllowedPath:
    """路径白名单条目"""
    path: str                            # 路径（如 "/home/user/project/src"）
    mode: str = "read-write"            # read-only / read-write / execute
    description: str = ""                # 用途说明
    applies_to: list[str] | None = None  # 应用的成员 ID 列表（None = 全员）
```

### 序列化兼容

确保新旧格式都能正确读写：

```python
def serialize_team_file(team: TeamFileV2) -> dict:
    """序列化为字典（JSON 友好）"""
    return {
        "name": team.name,
        "description": team.description,
        "created_at": team.created_at,
        "lead_agent_id": team.lead_agent_id,
        "members": [
            {
                "agent_id": m.agent_id,
                "name": m.name,
                "color": m.color,
                "permission_mode": m.permission_mode,
                "is_active": m.is_active,
                "worktree_path": m.worktree_path,
                "role": m.role,
                "model": m.model,
            }
            for m in team.members
        ],
        "allowed_paths": [
            {
                "path": p.path,
                "mode": p.mode,
                "description": p.description,
                "applies_to": p.applies_to,
            }
            for p in team.allowed_paths
        ],
        "backend_type": team.backend_type,
    }

def deserialize_team_file(data: dict) -> TeamFileV2:
    """反序列化（兼容旧格式缺失字段）"""
    members_data = data.get("members", [])
    members = []
    for m in members_data:
        members.append(TeamMemberV2(
            agent_id=m.get("agent_id", ""),
            name=m.get("name", "unknown"),
            color=m.get("color", "blue"),
            permission_mode=m.get("permission_mode", "default"),
            is_active=m.get("is_active", True),
            worktree_path=m.get("worktree_path"),
            role=m.get("role", "teammate"),
            model=m.get("model"),
        ))
    
    paths_data = data.get("allowed_paths", [])
    allowed_paths = []
    for p in paths_data:
        allowed_paths.append(AllowedPath(
            path=p.get("path", ""),
            mode=p.get("mode", "read-write"),
            description=p.get("description", ""),
            applies_to=p.get("applies_to"),
        ))
    
    return TeamFileV2(
        name=data["name"],
        description=data.get("description", ""),
        created_at=data.get("created_at", time.time()),
        lead_agent_id=data.get("lead_agent_id", ""),
        members=members,
        allowed_paths=allowed_paths,
        backend_type=data.get("backend_type", "in_process"),
    )
```

### 权限检查集成

在权限审批流程中增加路径白名单检查：

```python
def check_path_whitelist(
    team: TeamFileV2,
    agent_id: str,
    target_path: str,
    operation: str = "read",
) -> tuple[bool, str]:
    """检查操作是否在路径白名单中
    
    Returns:
        (allowed, reason) — (True, "") 表示允许
    """
    for ap in team.allowed_paths:
        if not target_path.startswith(ap.path):
            continue
        
        # 检查适用范围
        if ap.applies_to is not None and agent_id not in ap.applies_to:
            continue
        
        # 检查操作权限
        if operation == "write" and ap.mode == "read-only":
            return False, f"路径 {ap.path} 为只读模式"
        
        if operation == "execute" and ap.mode not in ("execute", "read-write"):
            return False, f"路径 {ap.path} 不允许执行操作"
        
        return True, ""
    
    # 白名单中没有匹配项 → 默认允许（由其他权限层决定）
    return True, ""
```

### 文件清单

| 操作     | 文件路径                                      | 说明                                                                                              |
| ------ | ----------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **修改** | `src/openharness/swarm/team_lifecycle.py` | TeamMember → TeamMemberV2, TeamFile → TeamFileV2, 新增 AllowedPath, 序列化/反序列化, 路径白名单检查 (\~150 行改动) |
| **修改** | `src/openharness/swarm/types.py`          | 如需新增类型则在此添加（否则不需要）                                                                              |
| **新建** | `tests/test_swarm/test_team_file_v2.py`   | TeamFile V2 测试 (\~8 用例)                                                                         |

### 验收标准

* [ ] `TeamMemberV2` 包含 color, permission\_mode, is\_active, worktree\_path 字段

* [ ] `TeamFileV2` 包含 allowed\_paths 列表

* [ ] `serialize_team_file()` 输出包含所有新字段

* [ ] `deserialize_team_file()` 兼容旧格式（缺少新字段时用默认值）

* [ ] `check_path whitelist()` 正确判断路径权限

* [ ] applies\_to 限制只在指定成员间生效

* [ ] 无 allowed\_paths 时默认放行（不破坏现有行为）

* [ ] 所有原有团队相关测试通过

***

## 📅 实施顺序

```
Day 1 上午: T1.1 缓存微压缩
         ├── 创建 cached_compact.py
         ├── 修改 compact/__init__.py
         └── 编写 test_cached_compact.py

Day 1 下午: T1.2 Agent 内存管理
         ├── 创建 agent_memory.py
         ├── 修改 autonomous_worker.py（集成）
         └── 编写 test_agent_memory.py

Day 2 上午: T1.3 团队文件增强
         ├── 修改 team_lifecycle.py
         └── 编写 test_team_file_v2.py

Day 2 下午: 全量验证
         ├── 运行全部测试（预计 ~530+ 通过）
         ├── Ruff Lint 检查
         └── 更新 CHANGELOG.md（v0.3.0 条目）
```

## ⚠️ 注意事项

1. **向后兼容优先**: 所有新增参数都设为 Optional（带默认值），不传参时行为不变
2. **遵循现有模式**: 使用 `@dataclass` + Pydantic 验证 + logging + 异步风格
3. **中文注释**: 所有新增代码注释使用中文
4. **测试先行**: 每个功能模块先写测试再实现
5. **不引入新依赖**: 仅使用标准库 + 已有依赖（yaml, pydantic 等）

