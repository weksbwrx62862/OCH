# 🚀 OpenClaw-Harness (OCH) — 深度重构设计方案

> **基于 OpenHarness 核心架构的下一代 Agent 驾驭平台**
>
> **版本**: v1.0.0-design
> **日期**: 2026-04-07
> **状态**: 🎯 待实施

---

## 📌 项目愿景

### 一句话定义
**OCH = OpenHarness 的完整能力 + 现代化 Web 平台 + OpenClaw 无缝集成**

### 核心价值主张

| 传统方案 | OCH 解决方案 |
|---------|-------------|
| CLI 工具难上手 | 🖥️ 直观的 Web 界面 |
| 单 Agent 孤岛 | 🤝 多智能体协作 |
| 工具分散管理 | 🔧 43+ 工具统一管控 |
| 技能复用困难 | 📚 知识库即插即用 |
| 权限控制薄弱 | 🛡️ 企业级 RBAC + 路径隔离 |
| 执行过程黑盒 | 🔍 全链路可视化监控 |
| 扩展能力有限 | 🔌 插件生态 + MCP 协议 |

---

## 🏗️ 架构设计（深度优化版）

### 1. 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OCH Frontend (Next.js 14)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    App Router + Server Components                   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │Dashboard │ │Agent Chat│ │Tools Mgr │ │Skills Lib│ │Swarm Ctrl│  │   │
│  │  │(实时监控)│ │(流式对话)│ │(43+工具)│ │(.md知识)│ │(多智能体)│  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │Sessions  │ │Permissions│ │Config    │ │Plugins   │ │Audit Log │  │   │
│  │  │(历史回放)│ │(RBAC)    │ │Center    │ │Market    │ │(审计追踪)│  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│                        API Gateway (Nginx / Caddy)                         │
│  · SSL 终端 · Rate Limiting · CORS · Static Files · WebSocket Proxy       │
├─────────────────────────────────────────────────────────────────────────────┤
│                     OCH Backend (Flask + Flask-RESTful)                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Blueprint Architecture                                             │   │
│  │  ├── agents_bp.py        # Agent CRUD + 会话管理                    │   │
│  │  ├── sessions_bp.py      # 实时会话 + 历史记录                      │   │
│  │  ├── tools_bp.py         # 工具注册表查询 + 权限配置                │   │
│  │  ├── skills_bp.py        # 技能库管理 + 动态加载                    │   │
│  │  ├── coordinator_bp.py   # 多智能体协调 + 任务调度                  │   │
│  │  ├── permissions_bp.py   # RBAC + 路径规则 + 审计日志              │   │
│  │  ├── tasks_bp.py         # 后台任务 + DAG 依赖                      │   │
│  │  ├── config_bp.py        # 配置管理 + 迁移                          │   │
│  │  ├── plugins_bp.py       # 插件生命周期管理                         │   │
│  │  ├── mcp_bp.py           # MCP 服务器管理                           │   │
│  │  └── websocket.py        # Socket.IO 实时通信                       │   │
│  └────────────────────────────┬────────────────────────────────────────┘   │
│                               │                                            │
│  ┌────────────────────────────▼────────────────────────────────────────┐   │
│  │                    Service Layer (业务逻辑层)                        │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │   │
│  │  │SessionService│ │ToolService   │ │SkillService  │                │   │
│  │  │·会话生命周期 │ │·工具发现     │ │·技能解析     │                │   │
│  │  │·消息路由     │ │·权限检查     │ │·按需加载     │                │   │
│  │  │·状态同步     │ │·执行代理     │ │·缓存管理     │                │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │   │
│  │  │CoordinatorSvc│ │PermissionSvc │ │PluginService │                │   │
│  │  │·团队编排     │ │·多级权限     │ │·安装/卸载     │                │   │
│  │  │·任务分发     │ │·路径规则     │ │·Hook 管理     │                │   │
│  │  │·协议握手     │ │·拒绝追踪     │ │·兼容性检查    │                │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│                       OpenHarness Core (100% 保留 + 增强)                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Engine Layer                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ QueryEngine (Agent Loop 核心)                                │   │   │
│  │  │ · submit_message() → AsyncIterator[StreamEvent]             │   │   │
│  │  │ · continue_pending() → 断点续传                              │   │   │
│  │  │ · CostTracker → Token/费用统计                               │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐   │   │
│  │  │ Tools    │ │ Skills   │ │ Perms    │ │ Coordinator          │   │   │
│  │  │ (43+)    │ │ (.md)    │ │ (RBAC)   │ │ (Multi-Agent)        │   │   │
│  │  │          │ │          │ │          │ │                      │   │   │
│  │  │·Bash     │ │·commit   │ │·Default  │ │·Subagent Spawning    │   │   │
│  │  │·File I/O │ │·review   │ │·Auto     │ │·Team Registry        │   │   │
│  │  │·Search   │ │·debug    │ │·Plan Mode│ │·Protocol Handshake   │   │   │
│  │  │·Web      │ │·plan     │ │·Path Rule│ │·Autonomous Workers   │   │   │
│  │  │·MCP      │ │·pdf/xlsx │ │·Denial   │ │·DAG Dependencies     │   │   │
│  │  │·Notebook │ │·...40+   │ │ Tracking │ │                      │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘   │   │
│  │                                                                     │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐   │   │
│  │  │ Plugins  │ │ Memory   │ │ MCP      │ │ Hooks + Commands     │   │   │
│  │  │ (扩展)   │ │ (持久化)  │ │ (外部工具)│ │ (生命周期)          │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│                          Infrastructure Layer                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │
│  │ PostgreSQL   │ │ Redis        │ │ MinIO/S3     │ │ File System    │  │
│  │ (主数据库)   │ │ (缓存/队列)  │ │ (对象存储)   │ │ (工作目录)     │  │
│  │              │ │              │ │              │ │                │  │
│  │·Sessions     │ │·Session Cache│ │·Artifacts    │ │·Agent Workspaces│  │
│  │·Agents       │ │·Pub/Sub      │ │·Exports      │ │·Skill .md files│  │
│  │·Audit Logs   │ │·Rate Limit   │ │·Backups      │ │·Config files   │  │
│  │·Permissions  │ │·Locks        │ │              │ │·Bridge logs    │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 数据模型设计（基于 OpenHarness 实体）

### 核心实体关系图

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Agent     │──────<│  Session    │──────<│   Message   │
├─────────────┤  1:N  ├─────────────┤  1:N  ├─────────────┤
│ id (PK)     │       │ id (PK)     │       │ id (PK)     │
│ name        │       │ agent_id FK │       │ session_id  │
│ description │       │ status      │       │ role        │
│ system_prompt│      │ created_at  │       │ content     │
│ model       │       │ updated_at  │       │ tool_uses[] │
│ max_turns   │       │ messages_cnt│       │ tokens_used │
│ workspace   │       └──────┬──────┘       └──────┬──────┘
│ config_json │              │                     │
└──────┬──────┘              │                     │
       │                     │                     │
       │ 1:N                │ N:1                 │ 1:N
       ▼                     ▼                     ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ ToolPerm    │       │  Task       │       │ ToolUse     │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │       │ id (PK)     │
│ agent_id FK │       │ session_id  │       │ message_id  │
│ tool_name   │       │ type        │       │ tool_name   │
│ permission  │       │ status      │       │ input_json  │
│ path_rules[]│       │ command     │       │ output      │
└─────────────┘       │ deps[]      │       │ duration_ms │
                     │ result      │       │ error       │
                     └──────┬──────┘       └─────────────┘
                            │
                            │ 1:N
                            ▼
                     ┌─────────────┐
                     │ TaskDep     │
                     ├─────────────┤
                     │ task_id FK  │
                     │ dep_task_id │
                     │ auto_unlock │
                     └─────────────┘
```

### SQLAlchemy 模型定义示例

```python
# models/agent.py
from sqlalchemy import Column, String, Text, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

class Agent(Base):
    """Agent 实体 — 对应 OpenHarness 的 Agent 配置"""
    __tablename__ = 'agents'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), nullable=False, unique=True)
    description = Column(Text, default='')
    system_prompt = Column(Text, default='')  # 自定义 System Prompt
    model = Column(String(64), default='claude-sonnet-4-20250514')
    max_turns = Column(Integer, default=8)
    max_tokens = Column(Integer, default=4096)
    workspace = Column(String(512), default='./workspace')
    config = Column(JSON, default=dict)  # 灵活配置存储

    # 关系
    sessions = relationship('Session', back_populates='agent', lazy='dynamic')
    permissions = relationship('ToolPermission', back_populates='agent', cascade='all, delete-orphan')

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Session(Base):
    """会话实体 — 对应 OpenHarness QueryEngine 实例"""
    __tablename__ = 'sessions'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey('agents.id'), nullable=False)
    status = Column(String(16), default='active')  # active, paused, completed, error
    title = Column(String(256), default='')

    # 统计信息
    total_messages = Column(Integer, default=0)
    total_turns = Column(Integer, default=0)
    total_tokens_input = Column(Integer, default=0)
    total_tokens_output = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)

    # 元数据
    metadata_ = Column('metadata', JSON, default=dict)

    # 关系
    agent = relationship('Agent', back_populates='sessions')
    messages = relationship('Message', back_populates='session', lazy='dynamic',
                           order_by='Message.created_at')
    tasks = relationship('Task', back_populates='session', cascade='all, delete-orphan')

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class Message(Base):
    """消息实体 — 对应 ConversationMessage"""
    __tablename__ = 'messages'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey('sessions.id'), nullable=False)
    role = Column(String(16), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)

    # Assistant 特有字段
    tool_uses = Column(JSON, default=list)  # [{name, input, ...}]
    stop_reason = Column(String(32), nullable=True)

    # Token 统计
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)

    # 关系
    session = relationship('Session', back_populates='messages')
    tool_results = relationship('ToolResult', back_populates='message',
                                cascade='all, delete-orphan')

    created_at = Column(DateTime, default=datetime.utcnow)

class ToolResult(Base):
    """工具执行结果"""
    __tablename__ = 'tool_results'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey('messages.id'), nullable=False)

    tool_name = Column(String(64), nullable=False)
    tool_input = Column(JSON, default=dict)
    tool_output = Column(Text, default='')
    is_error = Column(Boolean, default=False)
    duration_ms = Column(Integer, default=0)
    permission_decision = Column(String(16), nullable=True)  # allow, deny, ask

    # 关系
    message = relationship('Message', back_populates='tool_results')

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, default=datetime.utcnow)
```

---

## 🔌 API 设计（完整 RESTful 规范）

### 1. Agent Management API

```yaml
# /api/v1/agents

GET    /agents                          # 列出所有 Agent
POST   /agents                          # 创建新 Agent
GET    /agents/{id}                     # 获取 Agent 详情
PUT    /agents/{id}                     # 更新 Agent 配置
DELETE /agents/{id}                     # 删除 Agent
POST   /agents/{id}/duplicate           # 复制 Agent（含配置）
GET    /agents/{id}/stats               # 获取 Agent 统计数据
POST   /agents/{id}/export              # 导出 Agent 配置（JSON）
POST   /agents/{id}/import              # 导入 Agent 配置

# 请求示例
POST /api/v1/agents
{
  "name": "code-reviewer",
  "description": "代码审查专家",
  "system_prompt": "你是一个资深代码审查专家...",
  "model": "claude-sonnet-4-20250514",
  "max_turns": 12,
  "workspace": "./workspaces/reviewer",
  "config": {
    "permission_mode": "default",
    "allowed_tools": ["Bash", "Read", "Grep", "Glob"],
    "skills": ["review", "debug"],
    "auto_approve_patterns": ["*.md", "*.txt"]
  }
}
```

### 2. Session & Chat API（核心）

```yaml
# /api/v1/sessions

GET    /sessions                        # 列出所有会话（支持分页、筛选）
POST   /sessions                        # 创建新会话
GET    /sessions/{id}                   # 获取会话详情（含消息历史）
DELETE /sessions/{id}                   # 删除会话
PUT    /sessions/{id}/pause             # 暂停会话
PUT    /sessions/{id}/resume            # 恢复会话
PUT    /sessions/{id}/title             # 更新会话标题
GET    /sessions/{id}/messages          # 获取消息列表（分页）
GET    /sessions/{id}/messages/{msg_id} # 获取单条消息详情
GET    /sessions/{id}/stats             # 会话统计数据
GET    /sessions/{id}/export            # 导出会话（Markdown/JSON）

# Chat 接口（流式）
POST   /sessions/{id}/chat
Content-Type: application/json

{
  "message": "请审查 src/auth.py 文件的安全性",
  "stream": true,           // 是否使用 SSE 流式输出
  "max_turns": 8,           // 最大 Agent 循环次数
  "tools": ["Read", "Grep"] // 限制本次使用的工具集（可选）
}

# 流式响应（SSE）
data: {"type": "text_delta", "content": "正在分析..."}
data: {"type": "tool_start", "tool_name": "Read", "input": {"path": "src/auth.py"}}
data: {"type": "tool_end", "tool_name": "Read", "output": "...", "duration_ms": 120}
data: {"type": "text_delta", "content": "我发现以下安全问题：\n\n1. ..."}
data: {"type": "turn_complete", "stop_reason": "end_turn", "usage": {...}}
data: [DONE]
```

### 3. Tools Management API

```yaml
# /api/v1/tools

GET    /tools                           # 列出所有可用工具（43+）
GET    /tools/categories                # 获取工具分类
GET    /tools/{name}                    # 获取工具详细信息
GET    /tools/{name}/schema             # 获取工具输入 Schema（JSON Schema）
GET    /tools/{name}/examples           # 获取工具使用示例
POST   /tools/{name}/test               # 测试工具执行（dry-run）

# 响应示例
GET /api/v1/tools
{
  "total": 43,
  "categories": {
    "file_io": [
      {
        "name": "Bash",
        "description": "Execute shell commands",
        "input_schema": {
          "type": "object",
          "properties": {
            "command": {"type": "string", "description": "Shell command"},
            "cwd": {"type": "string", "description": "Working directory"}
          },
          "required": ["command"]
        },
        "requires_permission": true,
        "dangerous": true,
        "examples": [...]
      },
      // Read, Write, Edit, Glob, Grep ...
    ],
    "web": [WebFetch, WebSearch],
    "agent": [Agent, SendMessage, TeamCreate, TeamDelete],
    "task": [TaskCreate, TaskGet, TaskList, TaskStop, TaskOutput, TaskUpdate],
    "mcp": [MCPTool, ListMcpResources, ReadMcpResource],
    "mode": [EnterPlanMode, ExitPlanMode, EnterWorktree, ExitWorktree],
    "schedule": [CronCreate, CronList, CronDelete, CronToggle, RemoteTrigger],
    "meta": [Skill, Config, Brief, Sleep, AskUserQuestion, TodoWrite, ToolSearch]
  }
}
```

### 4. Skills Library API

```yaml
# /api/v1/skills

GET    /skills                          # 列出所有已安装技能
POST   /skills/install                 # 安装新技能（从 URL 或本地文件）
GET    /skills/{name}                   # 获取技能详情（Markdown 内容）
PUT    /skills/{name}/enable            # 启用技能
PUT    /skills/{name}/disable           # 禁用技能
DELETE /skills/{name}                   # 卸载技能
GET    /skills/search?q={query}         # 搜索技能
GET    /skills/categories               # 获取技能分类
POST   /skills/{name}/preview           # 预览技能效果（不实际执行）

# 技能元数据示例
{
  "name": "code-review",
  "description": "系统性审查代码质量、安全性和最佳实践",
  "category": "development",
  "version": "1.0.0",
  "enabled": true,
  "source": "builtin",  // builtin, user, plugin, marketplace
  "triggers": ["review this code", "check for bugs"],
  "content_md": "---\nname: code-review\n...\n\n# Code Review Skill\n\n...",
  "dependencies": ["Read", "Grep", "Glob"],
  "usage_count": 42
}
```

### 5. Multi-Agent Coordination API

```yaml
# /api/v1/coordinator

GET    /coordinator/teams               # 列出所有团队
POST   /coordinator/teams                # 创建团队
GET    /coordinator/teams/{team_id}      # 团队详情（成员 + 角色）
PUT    /coordinator/teams/{team_id}      # 更新团队配置
DELETE /cocoordinator/teams/{team_id}    # 解散团队

GET    /coordinator/agents               # 列出可用的子 Agent 定义
POST   /coordinator/agents               # 注册自定义 Agent 定义
GET    /coordinator/agents/{agent_id}    # Agent 定义详情

POST   /coordinator/spawn                # 生成子 Agent
{
  "team_id": "xxx",
  "agent_definition": "code-reviewer",
  "task": "审查 auth 模块",
  "parent_session_id": "yyy"
}

GET    /coordinator/tasks                # 列出协调任务
GET    /coordinator/tasks/{task_id}      # 任务详情（含 DAG）
GET    /coordinator/tasks/{task_id}/deps # 任务依赖图

GET    /coordinator/protocol/status      # 协议握手状态
POST   /coordinator/protocol/shutdown    # 发起关闭握手

# WebSocket: /ws/coordinator/{team_id}
// 实时事件：
// - agent_spawned, agent_completed, task_assigned
// - protocol_handshake, shutdown_initiated
```

### 6. Permissions & Security API

```yaml
# /api/v1/permissions

GET    /permissions/modes               # 可用权限模式列表
GET    /permissions/rules               # 列出所有路径规则
POST   /permissions/rules               # 创建路径规则
PUT    /permissions/rules/{rule_id}     # 更新规则
DELETE /permissions/rules/{rule_id}     # 删除规则
GET    /permissions/denials              # 权限拒绝记录（DenialTracker）
GET    /permissions/denials/stats       # 拒绝统计
POST   /permissions/denials/clear       # 清除拒绝记录

# Agent 级别权限
GET    /agents/{id}/permissions          # 获取 Agent 权限配置
PUT    /agents/{id}/permissions          # 更新 Agent 权限
{
  "mode": "default",  // default, auto, plan
  "tool_permissions": {
    "Bash": {
      "allow": true,
      "approved_commands": ["npm test", "python -m pytest"],
      "denied_commands": ["rm -rf *", "DROP TABLE"]
    },
    "Write": {
      "allow": true,
      "path_rules": [
        {"pattern": "/etc/*", "allow": false},
        {"pattern": "*.env", "ask": true}
      ]
    }
  }
}

# 审计日志
GET    /audit/logs                       # 审计日志（支持时间范围、类型筛选）
GET    /audit/stats                      # 审计统计
GET    /audit/export                     # 导出审计报告
```

### 7. Tasks & Background Jobs API

```yaml
# /api/v1/tasks

GET    /tasks                            # 后台任务列表
POST   /tasks                            # 创建后台任务
GET    /tasks/{task_id}                  # 任务详情
GET    /tasks/{task_id}/output           # 任务输出（支持 streaming）
PUT    /tasks/{task_id}/stop             # 停止任务
PUT    /tasks/{task_id}/update           # 更新任务状态（TodoWrite）
GET    /tasks/{task_id}/deps             # 任务依赖关系
POST   /tasks/{task_id}/deps             # 添加依赖

# DAG 依赖
POST   /tasks/create-with-deps           # 创建带依赖的任务组
{
  "tasks": [
    {"id": "t1", "command": "run tests", "deps": []},
    {"id": "t2", "command": "generate report", "deps": ["t1"]},
    {"id": "t3", "command": "send notification", "deps": ["t2"]}
  ]
}
```

### 8. Configuration API

```yaml
# /api/v1/config

GET    /config                           # 获取当前配置
PUT    /config                           # 更新配置（部分更新）
POST   /config/reset                     # 重置为默认值
GET    /config/schema                    # 配置 Schema（用于前端表单验证）
POST   /config/import                    # 导入配置文件
GET    /config/export                    # 导出配置文件
GET    /config/validation                # 验证配置有效性

# LLM Provider 配置
GET    /config/providers                 # 已配置的 Provider 列表
POST   /config/providers                 # 添加 Provider
PUT    /config/providers/{provider_id}   # 更新 Provider
DELETE /config/providers/{provider_id}   # 删除 Provider
POST   /config/providers/{provider_id}/test  # 测试连接

# Provider 示例
{
  "id": "anthropic-default",
  "type": "anthropic",  // anthropic, openai, copilot
  "base_url": "https://api.anthropic.com",
  "api_key": "sk-ant-...",
  "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514"],
  "default_model": "claude-sonnet-4-20250514",
  "rate_limit_rpm": 60,
  "max_tokens": 4096
}
```

### 9. Plugins & Extensions API

```yaml
# /api/v1/plugins

GET    /plugins                          # 已安装插件列表
GET    /plugins/available                # 可用插件市场（可选）
POST   /plugins/install                 # 安装插件（从 GitHub/NPM/本地）
DELETE /plugins/{plugin_name}            # 卸载插件
PUT    /plugins/{plugin_name}/enable     # 启用插件
PUT    /plugins/{plugin_name}/disable    # 禁用插件
GET    /plugins/{plugin_name}/detail     # 插件详情（commands, hooks, agents）
GET    /plugins/{plugin_name}/hooks      # 插件的 Hook 配置
PUT    /plugins/{plugin_name}/hooks      # 更新 Hook 配置

# Hook 管理
GET    /hooks                           # 全局 Hook 列表
POST   /hooks                          # 注册自定义 Hook
PUT    /hooks/{hook_id}                # 更新 Hook
DELETE /hooks/{hook_id}                # 删除 Hook
```

### 10. MCP (Model Context Protocol) API

```yaml
# /api/v1/mcp

GET    /mcp/servers                     # 已配置的 MCP 服务器列表
POST   /mcp/servers                     # 添加 MCP 服务器
PUT    /mcp/servers/{server_id}         # 更新服务器配置
DELETE /mcp/servers/{server_id}         # 移除服务器
GET    /mcp/servers/{server_id}/tools   # 服务器提供的工具列表
GET    /mcp/servers/{server_id}/resources # 服务器资源列表
POST   /mcp/servers/{server_id}/test    # 测试服务器连接

# MCP Server 配置示例
{
  "id": "filesystem-server",
  "name": "Filesystem Access",
  "type": "stdio",  // stdio, streamable-http
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"],
  "env": {},
  "enabled": true
}
```

---

## 🎨 前端架构设计（基于 Next.js 14）

### 1. 目录结构

```
frontend/
├── app/                          # App Router (Next.js 14)
│   ├── layout.tsx                # Root Layout
│   ├── page.tsx                  # Dashboard (首页重定向)
│   ├── globals.css               # Global Styles
│   │
│   ├── (auth)/                   # 认证路由组
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   │
│   ├── (dashboard)/              # 主仪表盘路由组
│   │   ├── layout.tsx            # Sidebar Layout
│   │   ├── page.tsx              # Dashboard 主页
│   │   │
│   │   ├── chat/
│   │   │   ├── page.tsx          # Chat 列表
│   │   │   └── [sessionId]/
│   │   │       ├── page.tsx      # Chat 详情（主界面）
│   │   │       └── components/
│   │   │
│   │   ├── tools/
│   │   │   ├── page.tsx          # Tools 浏览器
│   │   │   └── [toolName]/
│   │   │       └── page.tsx      # Tool 详情
│   │   │
│   │   ├── skills/
│   │   │   ├── page.tsx          # Skills Library
│   │   │   └── [skillName]/
│   │   │       └── page.tsx      # Skill 详情/编辑
│   │   │
│   │   ├── swarm/
│   │   │   ├── page.tsx          # Swarm Coordination
│   │   │   ├── teams/
│   │   │   │   └── [teamId]/
│   │   │   │       └── page.tsx  # Team 详情
│   │   │   └── agents/
│   │   │       └── page.tsx      # Agent Definitions
│   │   │
│   │   ├── sessions/
│   │   │   ├── page.tsx          # Sessions Monitor
│   │   │   └── [sessionId]/
│   │   │       └── page.tsx      # Session 回放
│   │   │
│   │   ├── settings/
│   │   │   ├── page.tsx          # General Settings
│   │   │   ├── providers/page.tsx # LLM Providers
│   │   │   ├── permissions/page.tsx
│   │   │   ├── plugins/page.tsx
│   │   │   ├── mcp/page.tsx
│   │   │   └── audit/page.tsx
│   │   │
│   │   └── agents/
│   │       ├── page.tsx          # Agent 管理
│   │       └── [agentId]/
│   │           ├── page.tsx      # Agent 详情
│   │           └── edit/page.tsx # 编辑 Agent
│   │
│   └── api/                      # API Routes (可选 BFF 层)
│       └── ...
│
├── components/                   # 共享组件
│   ├── ui/                       # 基础 UI 组件
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   ├── Card.tsx
│   │   ├── Table.tsx
│   │   ├── Badge.tsx
│   │   ├── Tabs.tsx
│   │   ├── Toast.tsx
│   │   └── ...
│   │
│   ├── chat/                     # Chat 相关组件
│   │   ├── ChatContainer.tsx     # 主聊天容器
│   │   ├── MessageList.tsx       # 消息列表
│   │   ├── MessageBubble.tsx     # 单条消息
│   │   ├── InputArea.tsx         # 输入区域
│   │   ├── ToolCallCard.tsx      # 工具调用卡片
│   │   ├── StreamingText.tsx     # 流式文本渲染
│   │   └── CodeBlock.tsx         # 代码块展示
│   │
│   ├── tools/                    # 工具相关组件
│   │   ├── ToolGrid.tsx          # 工具网格视图
│   │   ├── ToolCard.tsx          # 工具卡片
│   │   ├── ToolDetail.tsx        # 工具详情
│   │   ├── ToolSchemaForm.tsx    # Schema 表单
│   │   └── CategoryFilter.tsx    # 分类过滤器
│   │
│   ├── skills/                   # 技能相关组件
│   │   ├── SkillLibrary.tsx      # 技能库浏览
│   │   ├── SkillCard.tsx         # 技能卡片
│   │   ├── SkillViewer.tsx       # Markdown 渲染器
│   │   └── SkillEditor.tsx       # 技能编辑器
│   │
│   ├── coordinator/              # 协调器组件
│   │   ├── TeamView.tsx          # 团队视图
│   │   ├── AgentNode.tsx         # Agent 节点（树形/DAG）
│   │   ├── TaskFlow.tsx          # 任务流程图
│   │   └── ProtocolStatus.tsx    # 协议状态
│   │
│   ├── dashboard/                # 仪表盘组件
│   │   ├── StatsCards.tsx        # 统计卡片
│   │   ├── ActivityFeed.tsx      # 活动动态
│   │   ├── ResourceMonitor.tsx   # 资源监控
│   │   └── QuickActions.tsx      # 快捷操作
│   │
│   └── layout/                   # 布局组件
│       ├── Sidebar.tsx           # 侧边栏
│       ├── Header.tsx            # 顶部栏
│       ├── Breadcrumb.tsx        # 面包屑
│       └── CommandPalette.tsx    # 命令面板 (Cmd+K)
│
├── lib/                          # 工具函数和配置
│   ├── api.ts                    # API Client (封装 fetch/axios)
│   ├── websocket.ts              # WebSocket/Socket.IO client
│   ├── auth.ts                   # 认证逻辑
│   ├── utils.ts                  # 通用工具函数
│   ├── constants.ts              # 常量定义
│   └── types.ts                  # TypeScript 类型定义
│
├── hooks/                        # Custom React Hooks
│   ├── useChat.ts                # Chat 状态管理
│   ├── useSession.ts             # Session 管理
│   ├── useTools.ts               # 工具操作
│   ├── useSkills.ts              # 技能操作
│   ├── useWebSocket.ts           # WebSocket 连接
│   ├── usePermissions.ts         # 权限检查
│   └── useRealtime.ts            # 实时数据订阅
│
├── stores/                       # State Management (Zustand)
│   ├── agentStore.ts             # Agent 状态
│   ├── sessionStore.ts           # Session 状态
│   ├── chatStore.ts              # Chat 状态
│   ├── toolStore.ts              # 工具状态
│   ├── uiStore.ts                # UI 状态（侧边栏、主题等）
│   └── userStore.ts              # 用户状态
│
├── styles/                       # 样式文件
│   ├── globals.css               # 全局样式
│   ├── variables.css              # CSS 变量（主题色等）
│   ├── themes/                    # 主题定义
│   │   ├── dark.css               # Dark theme (默认)
│   │   └── light.css              # Light theme
│   └── components/                # 组件样式
│
└── public/                       # 静态资源
    ├── icons/
    ├── images/
    └── favicon.ico
```

### 2. 核心页面设计

#### 🎯 Dashboard（主页）

```
┌─────────────────────────────────────────────────────────────────────┐
│ OCH Dashboard                              [🔍 Search...] [⚙️] [👤]│
├────┬────────────────────────────────────────────────────────────────┤
│    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│ 📊 │  │Active    │ │Total     │ │Today's   │ │Tokens    │          │
│    │  │Sessions  │ │Agents    │ │Cost      │ │Used      │          │
│    │  │    12    │ │    8     │ │ $2.34    │ │ 125K     │          │
│    │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│    │                                                                 │
│    │  ┌─────────────────────────┐ ┌─────────────────────────────┐   │
│    │  │ Recent Activity Feed    │ │ Active Sessions (Live)      │   │
│    │  │                         │ │                              │   │
│    │  │ ✅ code-reviewer 完成    │ │ 💬 reviewer-session         │   │
│    │  │    审查 auth.py          │ │    正在分析...              │   │
│    │  │                         │ │                              │   │
│    │  │ 🔧 planner-agent 启动    │ │ 💬 debugger-session        │   │
│    │  │    新任务: 重构 API      │ │    等待用户输入...          │   │
│    │  │                         │ │                              │   │
│    │  │ ⚠️ security-bot 拒绝     │ │ 🔄 crawler-session         │   │
│    │  │    权限: rm -rf /        │ │    执行中... (3/8 turns)   │   │
│    │  │                         │ │                              │   │
│    │  └─────────────────────────┘ └─────────────────────────────┘   │
│    │                                                                 │
│    │  ┌─────────────────────────────────────────────────────────┐   │
│    │  │ Tool Usage Heatmap (7 days)                              │   │
│    │  │ ████░░ Bash  ████████ Read  ████░░ Grep  ██░░░░ Write  │   │
│    │  │ ░░░░░░ Glob  █████░░░ WebFetch  ███░░░░ Grep  ...      │   │
│    │  └─────────────────────────────────────────────────────────┘   │
├────┴────────────────────────────────────────────────────────────────┤
│ 🏠 Dashboard │ 💬 Chat │ 🔧 Tools │ 📚 Skills │ 🤝 Swarm │ ⚙️ Settings│
└─────────────────────────────────────────────────────────────────────┘
```

#### 💬 Chat Interface（核心界面 - 类似 Claude.ai / ChatGPT）

```
┌─────────────────────────────────────────────────────────────────────┐
│ ← Back to Sessions    [🔄 New Chat]  [⚙️ Config]    Agent: code-reviewer│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 👤 User                  10:23 AM                             │   │
│  │ 请审查 src/auth.py 文件的安全性问题，重点关注 SQL 注入和 XSS  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🤖 Assistant             10:23 AM                             │   │
│  │                                                             │   │
│  │ 我来帮你审查 `src/auth.py` 的安全性。让我先读取文件内容...    │   │
│  │                                                             │   │
│  │  ┌─ 🔧 Tool: Read ──────────────────────────────────────┐   │   │
│  │  │ 📂 Path: src/auth.py                               │   │   │
│  │  │ ⏱️ Duration: 120ms                                  │   │   │
│  │  │ ✅ Status: Success                                 │   │   │
│  │  │ [▶ Expand] [📋 Copy Output]                        │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  │                                                             │   │
│  │  ┌─ 🔧 Tool: Grep ─────────────────────────────────────┐   │   │
│  │  │ 🔍 Pattern: (execute|query)\(.*f".*{0}\)           │   │   │
│  │  │ 📂 Path: src/auth.py                               │   │   │
│  │  │ ✅ Found 3 matches                                 │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  │                                                             │   │
│  │ ## 安全性审查结果                                          │   │
│  │                                                             │   │
│  │ ### 🔴 严重问题 (Critical)                                  │   │
│  │                                                             │   │
│  │ **1. SQL 注入漏洞 (第 45-52 行)**                           │   │
│  │ ```python                                                   │   │
│  │ query = f"SELECT * FROM users WHERE id = {user_id}"        │   │
│  │ ```                                                         │   │
│  │ ⚠️ 直接拼接用户输入，攻击者可注入任意 SQL。                  │   │
│  │                                                             │   │
│  │ **建议修复:**                                               │   │
│  │ ```python                                                   │   │
│  │ # 使用参数化查询                                           │   │
│  │ query = "SELECT * FROM users WHERE id = %s"                │   │
│  │ cursor.execute(query, (user_id,))                          │   │
│  │ ```                                                         │   │
│  │                                                             │   │
│  │ ---                                                         │   │
│  │                                                             │   │
│  │ ### 🟡 中等问题 (Medium)                                    │   │
│  │ **2. XSS 风险 (第 78 行)** ...                              │   │
│  │                                                             │   │
│  │ ---                                                         │   │
│  │                                                             │   │
│  │ 📊 **总结**: 发现 2 个严重问题，1 个中等问题                │   │
│  │ 💰 **Token 使用**: Input: 1,234 / Output: 2,567             │   │
│  │ 🔄 **Turn**: 3/8                                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 👤 User                  10:25 AM                             │   │
│  │ 请帮我修复这些问题                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🤖 Assistant (Streaming...)  10:25 AM                        │   │
│  │                                                             │   │
│  │ 好的，我来修复这些安全问题...▌                               │   │
│  │                                                             │   │
│  │  ┌─ 🔧 Tool: Edit ─────────────────────────────────────┐   │   │
│  │  │ 📂 File: src/auth.py                                │   │   │
│  │  │ ✏️ Old: query = f"SELECT..."                        │   │   │
│  │  │ ✅ New: query = "SELECT ... WHERE id = %s"          │   │   │
│  │  │ ⏳ Executing...                                     │   │   │
│  │  └────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 💬 Type your message...                          [📎][▶Send]│   │
│  └─────────────────────────────────────────────────────────────┘   │
│  [🔧 Tools] [📚 Skills] [📋 Clipboard] [+ More]                    │
└─────────────────────────────────────────────────────────────────────┘
```

#### 🔧 Tools Manager 页面

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🔧 Tools Library (43 tools)                    [🔍 Search...] [🔄] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Categories: [All] [File I/O] [Search] [Web] [Agent] [Task] [MCP]  │
│                                                                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│  │ 🖥️ Bash    │  │ 📄 Read    │  │ ✏️ Write   │  │ 🔍 Grep    │       │
│  │ Execute    │  │ Read files │  │ Write files│  │ Search     │       │
│  │ shell cmds │  │ content    │  │ to disk    │  │ in files   │       │
│  │ ⚠️ Danger  │  │ ✓ Safe     │  │ ⚠️ Needs   │  │ ✓ Safe     │       │
│  │            │  │            │  │ permission │  │            │       │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │
│                                                                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│  │ 🌐 WebFetch│  │ 🔎 WebSearch│ │ 🤖 Agent  │  │ 📋 TodoWrite│       │
│  │ Fetch URLs │  │ Search web │  │ Spawn sub │  │ Manage     │       │
│  │            │  │            │  │ agents    │  │ todo lists │       │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │
│                                                                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│  │ 📅 Cron*   │  │ 📦 Task*   │  │ 🔌 MCP*   │  │ 📝 Skill   │       │
│  │ Schedule   │  │ Background │  │ External  │  │ Load .md  │       │
│  │ jobs       │  │ tasks      │  │ tools     │  │ knowledge │       │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │
│                                                                     │
│  ── Selected Tool Detail ──────────────────────────────────────     │
│  🖥️ **Bash** - Execute shell commands                              │
│                                                                     │
│  **Description:**                                                  │
│  Execute a bash command and return the output. Supports working     │
│  directory specification and environment variables.                │
│                                                                     │
│  **Input Schema (JSON Schema):**                                   │
│  ```json                                                           │
│  {                                                                 │
│    "type": "object",                                               │
│    "properties": {                                                 │
│      "command": {                                                  │
│        "type": "string",                                           │
│        "description": "The shell command to execute"               │
│      },                                                            │
│      "cwd": {                                                      │
│       type": "string",                                             │
│        "description": "Working directory for the command"         │
│      }                                                             │
│    },                                                              │
│    "required": ["command"]                                         │
│  }                                                                 │
│  ```                                                               │
│                                                                     │
│  **Examples:**                                                      │
│  - `ls -la`                                                        │
│  - `npm test`                                                      │
│  - `python script.py --input data.csv`                             │
│                                                                     │
│  **Security:** ⚠️ Requires permission approval                      │
│  **Category:** File I/O                                            │
│                                                                     │
│  [▶ Test Run] [📋 Copy Schema] [🔗 View Source]                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 安全架构（深度强化）

### 多层安全模型

```
┌─────────────────────────────────────────────────────────────────┐
│                    Layer 7: Application Security                 │
│  · JWT Token Authentication                                      │
│  · Role-Based Access Control (RBAC)                             │
│  · API Key Management (for OpenClaw integration)                │
│  · CSRF Protection                                              │
├─────────────────────────────────────────────────────────────────┤
│                    Layer 6: Permission System (OpenHarness)      │
│  · Permission Modes: Default / Auto / Plan                      │
│  · Path-level Rules (allow/deny patterns)                       │
│  · Command Whitelist/Blacklist                                  │
│  · Denial Tracking (smart denial learning)                      │
│  · YOLO Classifier (auto-approve safe ops)                      │
├─────────────────────────────────────────────────────────────────┤
│                    Layer 5: Tool Execution Sandbox               │
│  · Working Directory Isolation                                  │
│  · Command Timeout (configurable)                               │
│  · Resource Limits (CPU, Memory, File Descriptors)               │
│  · Network Access Control                                       │
│  · Environment Variable Sanitization                            │
├─────────────────────────────────────────────────────────────────┤
│                    Layer 4: Audit & Monitoring                   │
│  · Complete Audit Trail (who, what, when, result)               │
│  · Real-time Alerting (suspicious activities)                   │
│  · Session Recording & Replay                                   │
│  · Anomaly Detection (ML-based, optional)                       │
├─────────────────────────────────────────────────────────────────┤
│                    Layer 3: Data Protection                      │
│  · Encryption at Rest (AES-256)                                 │
│  · Encryption in Transit (TLS 1.3)                              │
│  · API Key Encryption (hashed storage)                          │
│  · Sensitive Data Masking in Logs                               │
├─────────────────────────────────────────────────────────────────┤
│                    Layer 2: Infrastructure Security              │
│  · Container Isolation (Docker namespaces)                      │
│  · Network Segmentation (internal APIs not exposed)             │
│  · Secret Management (Vault / Environment)                      │
│  · Regular Security Updates                                     │
├─────────────────────────────────────────────────────────────────┤
│                    Layer 1: Compliance & Governance              │
│  · GDPR / SOC2 Ready (data retention, right to forget)          │
│  · Data Residency Controls                                      │
│  · Policy as Code (Open Policy Agent)                           │
│  · Regular Penetration Testing                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 性能优化策略

### 1. Backend Optimization

```python
# 使用 asyncio + uvloop 提升并发性能
import uvicorn
from flask import Flask

app = Flask(__name__)

# 配置
config = {
    'async_mode': 'threading',  # 或 'gevent'/'eventlet'
    'thread_pool_size': 64,
    'websocket_compression': True,
}

# 缓存层
from functools import lru_cache
from redis import Redis

redis_client = Redis(host='localhost', port=6379, db=0)

@lru_cache(maxsize=1024)
def get_tool_schema(tool_name: str) -> dict:
    """缓存工具 Schema（TTL 由 Redis 控制）"""
    cached = redis_client.get(f"tool:schema:{tool_name}")
    if cached:
        return json.loads(cached)
    schema = compute_tool_schema(tool_name)
    redis_client.setex(f"tool:schema:{tool_name}", 3600, json.dumps(schema))
    return schema

# 连接池
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)
```

### 2. Frontend Optimization

```typescript
// lib/api.ts - 智能 API Client
import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// 请求去重 + 缓存
const apiClient = {
  get: async <T>(url: string, options?: RequestInit): Promise<T> => {
    const cacheKey = `GET:${url}`;
    // 检查缓存
    const cached = queryCache.get<T>(cacheKey);
    if (cached && !options?.forceRefresh) return cached;

    const response = await fetch(`/api/v1${url}`, {
      ...options,
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    });

    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    const data = await response.json();

    // 写入缓存
    queryCache.set(cacheKey, data, { ttl: 5 * 60 * 1000 }); // 5 分钟
    return data;
  },

  // SSE 流式请求
  stream: async (
    url: string,
    body: any,
    onEvent: (event: StreamEvent) => void,
    signal?: AbortSignal
  ): Promise<void> => {
    const response = await fetch(`/api/v1${url}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getAuthToken()}`,
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(body),
      signal,
    });

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') return;
          try {
            onEvent(JSON.parse(data));
          } catch (e) {
            console.error('SSE Parse Error:', e);
          }
        }
      }
    }
  },
};
```

### 3. WebSocket Real-time Communication

```python
# websocket.py - Socket.IO 实现
from flask_socketio import SocketIO, emit, join_room, leave_room

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@socketio.on('join_session')
def handle_join_session(data):
    """加入会话房间，接收实时更新"""
    session_id = data['session_id']
    join_room(f'session:{session_id}')
    emit('joined', {'session_id': session_id})

@socketio.on('leave_session')
def handle_leave_session(data):
    session_id = data['session_id']
    leave_room(f'session:{session_id}')

# 在 QueryEngine 中 emit 事件
async def stream_with_websocket(session_id: str, query_engine: QueryEngine, prompt: str):
    async for event in query_engine.submit_message(prompt):
        socketio.emit('stream_event', event.to_dict(), room=f'session:{session_id}')

        # 同时持久化到数据库
        if isinstance(event, (AssistantTextDelta, ToolExecutionStarted, ToolExecutionCompleted)):
            save_event_to_db(session_id, event)
```

---

## 🔌 OpenClaw 集成方案

### 双向同步机制

```python
# services/openclaw_integration.py
"""OpenClaw ↔ OCH 双向同步服务"""

import json
from pathlib import Path
from typing import Optional
import aiofiles

OPENCLAW_CONFIG_PATH = Path.home() / '.openclaw' / 'openclaw.json'
OPENCLAW_BACKUP_DIR = Path.home() / '.openclaw' / 'backups'

class OpenClawIntegration:
    """OpenClaw 集成服务"""

    def __init__(self):
        self.config_path = OPENCLAW_CONFIG_PATH
        self.backup_dir = OPENCLAW_BACKUP_DIR
        self.backup_dir.mkdir(exist_ok=True)

    async def read_openclaw_config(self) -> dict:
        """读取 OpenClaw 配置"""
        async with aiofiles.open(self.config_path, 'r') as f:
            content = await f.read()
        return json.loads(content)

    async def write_openclaw_config(self, config: dict) -> None:
        """写入 OpenClaw 配置（自动备份）"""
        # 备份现有配置
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f'openclaw.json.bak.{timestamp}'

        if self.config_path.exists():
            async with aiofiles.open(self.config_path, 'r') as f:
                existing = await f.read()
            async with aiofiles.open(backup_path, 'w') as f:
                await f.write(existing)

        # 写入新配置
        async with aiofiles.open(self.config_path, 'w') as f:
            await f.write(json.dumps(config, indent=2, ensure_ascii=False))

    async def sync_agents_to_openclaw(self, agents: list[Agent]) -> None:
        """将 OCH 的 Agent 同步到 OpenClaw"""
        config = await self.read_openclaw_config()

        openclaw_agents = []
        for agent in agents:
            openclaw_agent = {
                'id': agent.id,
                'workspace': agent.workspace or f'~/.openclaw/workspace-{agent.name}',
                'subagents': {'allowAgents': []},  # 根据团队配置填充
            }
            openclaw_agents.append(openclaw_agent)

        config['agents']['list'] = openclaw_agents
        await self.write_openclaw_config(config)

    async def sync_skills_to_openclaw(self, skills: list[Skill]) -> None:
        """将 OCH 的技能同步到 OpenClaw skills 目录"""
        skills_dir = Path.home() / '.openclaw' / 'skills'
        skills_dir.mkdir(exist_ok=True)

        for skill in skills:
            if skill.source in ['builtin', 'user']:
                skill_file = skills_dir / f'{skill.name}.md'
                async with aiofiles.open(skill_file, 'w') as f:
                    await f.write(skill.content_md)

    async def sync_providers_to_openclaw(self, providers: list[Provider]) -> None:
        """将 LLM Providers 同步到 OpenClaw"""
        config = await self.read_openclaw_config()

        providers_config = {}
        for provider in providers:
            provider_key = f"{provider.type}-{provider.id}"
            providers_config[provider_key] = {
                'baseUrl': provider.base_url,
                'apiKey': provider.api_key,
                'api': provider.api_type,
                'models': [{
                    'id': m.id,
                    'name': m.name,
                    'reasoning': m.reasoning,
                    'input': m.input_types,
                    'contextWindow': m.context_window,
                    'maxTokens': m.max_tokens,
                } for m in provider.models]
            }

        config['models']['providers'] = providers_config
        await self.write_openclaw_config(config)

    async def create_api_key_for_agent(self, agent_id: str) -> str:
        """为 Agent 生成 API Key 用于 OpenClaw 连接"""
        api_key = f"och-{uuid.uuid4().hex[:32]}"

        # 存储 API Key（加密）
        hashed = bcrypt.hash(api_key)
        await db.agent_api_keys.insert({
            'agent_id': agent_id,
            'key_hash': hashed,
            'created_at': datetime.utcnow(),
        })

        return api_key
```

---

## 📦 项目结构（最终版）

```
openclaw-harness/
├── README.md                       # 项目说明
├── LICENSE                         # Apache 2.0
├── .env.example                    # 环境变量模板
├── docker-compose.yml              # Docker 编排
├── Dockerfile.backend              # Backend Docker
├── Dockerfile.frontend             # Frontend Docker
│
├── backend/                        # Flask Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # Flask App 入口
│   │   ├── config.py               # 配置管理
│   │   │
│   │   ├── api/                    # API Blueprint 目录
│   │   │   ├── __init__.py
│   │   │   ├── agents.py           # Agent API
│   │   │   ├── sessions.py         # Session & Chat API
│   │   │   ├── tools.py            # Tools API
│   │   │   ├── skills.py           # Skills API
│   │   │   ├── coordinator.py      # Multi-Agent API
│   │   │   ├── permissions.py      # Permissions API
│   │   │   ├── tasks.py            # Tasks API
│   │   │   ├── config.py           # Configuration API
│   │   │   ├── plugins.py          # Plugins API
│   │   │   ├── mcp.py              # MCP API
│   │   │   ├── audit.py            # Audit Log API
│   │   │   └── websocket.py        # WebSocket Handler
│   │   │
│   │   ├── services/               # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── session_service.py  # 会话管理
│   │   │   ├── tool_service.py     # 工具服务
│   │   │   ├── skill_service.py    # 技能服务
│   │   │   ├── coordinator_service.py  # 协调器服务
│   │   │   ├── permission_service.py   # 权限服务
│   │   │   ├── plugin_service.py   # 插件服务
│   │   │   ├── task_service.py     # 任务服务
│   │   │   └── openclaw_integration.py  # OpenClaw 集成
│   │   │
│   │   ├── models/                 # SQLAlchemy Models
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── agent.py
│   │   │   ├── session.py
│   │   │   ├── message.py
│   │   │   ├── tool_result.py
│   │   │   ├── task.py
│   │   │   ├── permission.py
│   │   │   ├── audit_log.py
│   │   │   └── plugin.py
│   │   │
│   │   ├── schemas/                # Pydantic Schemas
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   ├── session.py
│   │   │   ├── tool.py
│   │   │   ├── skill.py
│   │   │   └── ...
│   │   │
│   │   ├── core/                   # 核心模块
│   │   │   ├── database.py         # DB 连接
│   │   │   ├── security.py         # 认证/授权
│   │   │   ├── exceptions.py       # 自定义异常
│   │   │   └── dependencies.py     # 依赖注入
│   │   │
│   │   └── utils/                  # 工具函数
│   │       ├── __init__.py
│   │       ├── caching.py
│   │       ├── logging.py
│   │       └── helpers.py
│   │
│   ├── openharness/                # OpenHarness Core (完整保留)
│   │   ├── __init__.py
│   │   ├── engine/                 # Agent Engine
│   │   ├── tools/                  # 43+ Tools
│   │   ├── skills/                 # Skills System
│   │   ├── coordinator/            # Multi-Agent
│   │   ├── permissions/            # Permission System
│   │   ├── plugins/                # Plugin System
│   │   ├── memory/                 # Persistent Memory
│   │   ├── mcp/                    # MCP Client
│   │   ├── hooks/                  # Lifecycle Hooks
│   │   ├── commands/               # 54 Commands
│   │   ├── tasks/                  # Task Management
│   │   ├── services/compact/       # Context Compression
│   │   ├── config/                 # Configuration
│   │   ├── state/                  # State Management
│   │   ├── sandbox/                # Execution Sandbox
│   │   ├── voice/                  # Voice I/O
│   │   ├── channels/               # IM Channels
│   │   ├── bridge/                 # Bridge Service
│   │   ├── api/                    # API Clients
│   │   ├── auth/                   # Auth (Copilot etc.)
│   │   ├── prompts/                # Prompt Templates
│   │   ├── output_styles/          # Output Formatting
│   │   ├── themes/                 # UI Themes
│   │   ├── keybindings/            # Key Bindings
│   │   ├── ui/                     # TUI Components
│   │   ├── utils/                  # Utilities
│   │   ├── types/                  # Type Definitions
│   │   └── vim/                    # Vim Plugin
│   │
│   ├── tests/                      # 测试套件
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   │
│   ├── alembic/                    # 数据库迁移
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── scripts/                    # 维护脚本
│   │   ├── setup.sh
│   │   ├── seed_data.py
│   │   └── backup.sh
│   │
│   ├── requirements.txt            # Python 依赖
│   ├── pyproject.toml
│   └── pytest.ini
│
├── frontend/                       # Next.js 14 Frontend
│   ├── app/                        # App Router Pages
│   ├── components/                 # React Components
│   ├── lib/                        # Utilities & API Client
│   ├── hooks/                      # Custom Hooks
│   ├── stores/                     # Zustand Stores
│   ├── styles/                     # CSS / Tailwind
│   ├── public/                     # Static Assets
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── postcss.config.js
│
├── docs/                           # 文档
│   ├── architecture.md
│   ├── api-reference.md
│   ├── deployment.md
│   └── migration-guide.md
│
└── infrastructure/                  # 基础设施配置
    ├── nginx/
    │   └── och.conf
    ├── redis/
    │   └── redis.conf
    └── postgres/
        └── init.sql
```

---

## 🎯 实施路线图（Phase by Phase）

### Phase 1: 基础设施搭建（Week 1-2）

**目标**: 搭建项目骨架，实现核心运行时

- [x] 初始化项目结构（Monorepo）
- [ ] 配置 Flask + Next.js 开发环境
- [ ] 迁移 OpenHarness Core 到 backend/openharness/
- [ ] 实现数据库模型和 Alembic 迁移
- [ ] 实现 JWT 认证系统
- [ ] 创建基础 API Blueprint 骨架
- [ ] 配置 Docker Compose 开发环境

**交付物**:
- 可启动的开发环境
- 数据库 Schema 完成
- 认证 API 可用

### Phase 2: 核心 API 开发（Week 3-4）

**目标**: 实现最关键的 API 端点

- [ ] Session & Chat API（SSE 流式输出）
- [ ] Tools Management API（完整 43+ 工具）
- [ ] Skills Library API（加载、搜索、预览）
- [ ] Agent CRUD API
- [ ] WebSocket 实时通信（Socket.IO）
- [ ] 基础前端页面（Chat 界面原型）

**交付物**:
- 可以通过 Web 界面与 Agent 对话
- 工具和技能可以浏览和管理
- 实时消息流正常工作

### Phase 3: 高级功能开发（Week 5-6）

**目标**: 实现多智能体和企业级功能

- [ ] Multi-Agent Coordination API
- [ ] Permission System API（RBAC + 路径规则）
- [ ] Task Management API（DAG 依赖）
- [ ] Configuration & Provider Management
- [ ] Plugin System API
- [ ] MCP Server Integration
- [ ] 完整前端页面（所有模块）

**交付物**:
- 多智能体协作功能可用
- 权限系统完整
- 所有管理页面完成

### Phase 4: OpenClaw 集成（Week 7）

**目标**: 与 OpenClaw 无缝集成

- [ ] OpenClaw 配置双向同步
- [ ] API Key 认证机制
- [ ] Agent/技能/Provider 同步
- [ ] Workspace 映射
- [ ] 飞书/Lark 集成（可选）
- [ ] 文档和部署指南

**交付物**:
- OpenClaw 用户可以直接使用 OCH
- 配置自动同步
- 完整的使用文档

### Phase 5: 优化与发布（Week 8）

**目标**: 生产就绪

- [ ] 性能优化（缓存、连接池、异步）
- [ ] 安全加固（渗透测试、审计）
- [ ] 监控告警（Prometheus + Grafana）
- [ ] 自动化测试（覆盖率 > 80%）
- [ ] CI/CD Pipeline
- [ ] 用户手册和 API 文档
- [ ] v1.0.0 Release

**交付物**:
- 生产级稳定版本
- 完整文档
- 可复现的部署流程

---

## 📈 成功指标

| 指标 | 目标值 |
|------|--------|
| API 响应时间 (P95) | < 200ms |
| SSE 首字节延迟 | < 100ms |
| WebSocket 消息延迟 | < 50ms |
| 并发会话数 | > 100 |
| 工具执行成功率 | > 99% |
| 测试覆盖率 | > 80% |
| 页面加载时间 | < 2s |
| OpenHarness 功能迁移率 | 100% |

---

## 🎨 设计原则总结

### ✅ 我们坚持的原则

1. **完整性优先** — 100% 迁移 OpenHarness 能力，不做阉割
2. **Web-Native** — 所有 CLI 功能通过现代 Web API 暴露
3. **实时优先** — 流式输出、WebSocket、即时反馈
4. **开发者友好** — 清晰的 API 文档、TypeScript 类型、SDK
5. **安全第一** — 多层防护、零信任、完全审计
6. **可扩展性** — 插件化架构、MCP 协议、开放生态
7. **性能至上** — 异步优先、智能缓存、连接池
8. **用户体验** — 类似 ChatGPT/Claude.ai 的流畅体验

### ❌ 我们避免的反模式

- ~~过度工程~~ — 不引入不必要的抽象层
- ~~供应商锁定~~ — 保持对多种 LLM 的支持
- ~~API 不一致~~ — 统一的 RESTful 风格和错误码
- ~~前端耦合~~ — 前后端完全解耦，通过 API 通信
- ~~忽略安全~~ — 安全不是事后补充，而是设计时就考虑

---

## 🚀 下一步行动

**立即开始**:
1. 创建项目仓库 `openclaw-harness`
2. 初始化 Monorepo 结构
3. 配置开发环境（Flask + Next.js + PostgreSQL + Redis）
4. 开始 Phase 1 实施

**预期成果**:
- 一个功能完整的、现代化的 Agent 驾驭平台
- OpenClaw 的完美 Web 扩展
- 开源社区的优质基础设施项目

---

**文档版本**: v1.0.0  
**最后更新**: 2026-04-07  
**作者**: AI Architect (based on deep analysis of OpenHarness + Clawith)  
**状态**: ✅ Design Complete — Ready for Implementation
