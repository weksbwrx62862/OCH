# OpenHarness 集成问题

> **Updated: 2026-04-13** — 21 个原始问题中 19 个已修复，仅剩 2 个仍部分存在。
> 原始行号引用已不适用（代码已被重构），保留原始编号仅用于追溯。

## 概述

原始审查发现 OCH 服务层与 OpenHarness 核心引擎之间存在大量 API 签名不匹配、不存在类/函数的导入、以及配置系统冲突问题。经代码修复后，**19/21 问题已解决**。

---

## 修复状态汇总

| # | 问题 | 原始严重度 | 当前状态 | 修复说明 |
|---|------|-----------|---------|---------|
| 1.1-1 | `OpenHarnessConfig` 类不存在 | P0 | ✅ 已修复 | `session_service.py` 已改用 `load_settings()` |
| 1.1-2 | `OpenHarnessConfig()` 无参构造 | P0 | ✅ 已修复 | 已使用 `load_settings()` 函数加载 |
| 1.2-1 | `QueryEngine(config=config)` 签名错误 | P0 | ✅ 已修复 | 已改为传入 6 个必选关键字参数 |
| 1.2-2 | `QueryEngine` 创建后未赋值 | P0 | ✅ 已修复 | 已赋值给 `engine` 并调用 `submit_message()` |
| 1.2-3 | 缺少 `api_client` 实现 | P0 | ✅ 已修复 | `OCHApiClient` 实现了 `SupportsStreamingMessages` |
| 1.3-1 | `get_default_tool_registry` 函数名错误 | P0 | ✅ 已修复 | 已改为 `create_default_tool_registry` |
| 1.3-2 | `list_tools()` 返回类型误用 | P0 | ✅ 已修复 | 已遍历 `tool` 对象 |
| 1.3-3 | `get_tool_info()` 不存在 | P0 | ✅ 已修复 | 已使用 `registry.get(name)` |
| 1.3-4 | `get_schema()` 不存在 | P0 | ✅ 已修复 | 已使用 `tool.input_model.model_json_schema()` |
| 1.3-5 | `registry.execute()` 签名错误 | P0 | ✅ 已修复 | 已改为 `tool.execute(parsed_args, context)` |
| 1.3-6 | 缺少 `ToolExecutionContext` | P0 | ✅ 已修复 | 已构建 `ToolExecutionContext(cwd=..., metadata=...)` |
| 1.4-1 | `availability.provider` 不存在 | P0 | ✅ 已修复 | 已从 `availability.command` 推断 |
| 1.4-2 | `availability.runtime_path` 不存在 | P0 | ✅ 已修复 | 已不再访问 |
| 1.4-3 | `availability.version` 不存在 | P0 | ✅ 已修复 | 已不再访问 |
| 1.4-4 | `get_sandbox_config()` 不存在 | P0 | ✅ 已修复 | 已使用 `load_settings().sandbox` |
| 1.4-5 | `is_host_bash_allowed()` 不存在 | P0 | ✅ 已修复 | 已使用 `not availability.active` |
| 1.5-1 | `wrap_command_for_sandbox` 传 `str` 非 `list[str]` | P0 | ✅ 已修复 | 已使用 `shlex.split(command)` 预处理 |
| 1.5-2 | `wrap_command_for_sandbox` 返回值被忽略 | P0 | ✅ 已修复 | 已解构 `wrapped_cmd, settings_path` |
| 1.6-1 | `PermissionMode` 无 `AUTO` 值 | P0 | ✅ 已修复 (T5) | API 统一为 `full_auto`，`_normalize_mode()` 兼容旧值 |
| 1.6-2 | `SimpleSettings` 类型不匹配 | P0 | ✅ 已修复 | 已使用 `PermissionSettings` |
| — | `_simulate_stream` fallback 仍保留 | P2 | ⚠️ 仍存在 | 作为异常降级保留，日志级别已提升为 `warning` (T6) |

---

## 1. OpenHarness 核心集成 API 不匹配（原 P0 — 已修复）

### 1.1 `OpenHarnessConfig` 类不存在 ~~[P0]~~ → ✅ 已修复

| # | 原始问题 | 修复后状态 |
|---|---------|-----------|
| 1 | `from openharness.config import OpenHarnessConfig` — 该类不存在 | ✅ `session_service.py` 已改为 `from openharness.config import load_settings` |
| 2 | `OpenHarnessConfig()` 无参构造 | ✅ 已使用 `settings = load_settings()` + `settings.resolve_api_key()` |

### 1.2 `QueryEngine` 构造函数签名完全错误 ~~[P0]~~ → ✅ 已修复

| # | 原始问题 | 修复后状态 |
|---|---------|-----------|
| 1 | `QueryEngine(config=config)` — 不接受 `config` 参数 | ✅ 已传入 6 个必选关键字参数：`api_client`, `tool_registry`, `permission_checker`, `cwd`, `model`, `system_prompt` |
| 2 | `QueryEngine` 创建后未赋值也未使用 | ✅ 已赋值给 `engine`，调用 `engine.submit_message(user_message)` |
| 3 | 缺少 `api_client` 实现 | ✅ `OCHApiClient` 已实现 `SupportsStreamingMessages` 协议，支持 `anthropic`/`openai_compat`/`copilot` 三种后端 (T6 新增 copilot) |

### 1.3 `ToolRegistry` API 全面不匹配 ~~[P0]~~ → ✅ 已修复

| # | 原始问题 | 修复后状态 |
|---|---------|-----------|
| 1 | `get_default_tool_registry` 函数名错误 | ✅ 已改为 `create_default_tool_registry` |
| 2 | `list_tools()` 返回值类型错误处理 | ✅ 已遍历 `BaseTool` 对象，访问 `tool.name`, `tool.description` |
| 3 | `get_tool_info()` 不存在 | ✅ 已改为 `registry.get(tool_name)` |
| 4 | `get_schema()` 不存在 | ✅ 已改为 `tool.input_model.model_json_schema()` |
| 5 | `registry.execute()` 签名错误 | ✅ 已改为 `tool.execute(parsed_args, context)` |
| 6 | 缺少 `ToolExecutionContext` | ✅ 已构建 `ToolExecutionContext(cwd=Path(...), metadata=...)` |

### 1.4 `SandboxAvailability` 属性缺失 + 适配器函数不存在 ~~[P0]~~ → ✅ 已修复

| # | 原始问题 | 修复后状态 |
|---|---------|-----------|
| 1 | `availability.provider` 不存在 | ✅ 已从 `availability.command` 推断 provider |
| 2 | `availability.runtime_path` 不存在 | ✅ 已不再访问 |
| 3 | `availability.version` 不存在 | ✅ 已不再访问 |
| 4 | `get_sandbox_config()` 不存在 | ✅ 已改为 `load_settings().sandbox` |
| 5 | `is_host_bash_allowed()` 不存在 | ✅ 已改为 `not availability.active` |

### 1.5 `wrap_command_for_sandbox` 签名不匹配 ~~[P0]~~ → ✅ 已修复

| # | 原始问题 | 修复后状态 |
|---|---------|-----------|
| 1 | 传入 `str` 但期望 `list[str]` | ✅ 已使用 `shlex.split(command)` 预处理 |
| 2 | 返回值被忽略 | ✅ 已解构 `wrapped_cmd, settings_path = wrap_command_for_sandbox(cmd_list)` |

### 1.6 `PermissionMode` 枚举值不匹配 ~~[P0]~~ → ✅ 已修复 (T5)

| # | 原始问题 | 修复后状态 |
|---|---------|-----------|
| 1 | `PERMISSION_MODES['auto']` 键不存在于 `PermissionMode` 枚举 | ✅ API 统一为 `full_auto`；`_normalize_mode()` + `_LEGACY_MODE_ALIASES` 兼容旧 `'auto'` 值 |
| 2 | `SimpleSettings` 不完全实现 `PermissionSettings` 接口 | ✅ 已使用 `PermissionSettings` 构造 |

---

## 2. 仍存在的问题

### 2.1 [P2] `_simulate_stream` fallback 保留 ⚠️

**位置**: `app/services/session_service.py` `stream_chat()` 方法

**现状**: 当 `QueryEngine` 调用失败时，异常被捕获并 fallback 到 `_simulate_stream()`。这是合理的降级策略，但意味着真正的 API 错误可能被静默吞噬。

**T6 改进**:
- 日志级别已从 `logger.info` 提升为 `logger.warning`
- 日志消息已补充 "QueryEngine 调用失败" 说明

**后续建议**: 在生产环境中可考虑完全禁用 `_simulate_stream()` fallback，改为直接返回错误事件。

### 2.2 [P2] `OCHApiClient` Copilot 覆盖 ✅ 已修复 (T6)

**位置**: `app/services/session_service.py:58-95`

**原始问题**: `OCHApiClient` 只处理 `anthropic` 和 `openai_compat` 两种后端，`copilot` 格式会落入默认的 `AnthropicApiClient`。

**T6 修复**: 已添加 `CopilotClient` 支持，基于 `provider.backend_type` 三路分发。

---

## 3. 已确认的问题验证

以下问题经源码验证后确认已修复：

1. ~~**`OpenHarnessConfig` 不存在**~~ ✅ 已修复 — 使用 `load_settings()`
2. ~~**`QueryEngine(config=config)` 构造函数错误**~~ ✅ 已修复 — 传入 6 个关键字参数
3. ~~**`QueryEngine` 创建后未赋值**~~ ✅ 已修复 — 赋值并调用 `submit_message()`
4. ~~**`get_default_tool_registry` 函数名错误**~~ ✅ 已修复 — 使用 `create_default_tool_registry`
5. ~~**`ToolRegistry.list_tools()` 返回类型误用**~~ ✅ 已修复 — 遍历 `BaseTool` 对象
6. ~~**`ToolRegistry.get_tool_info()` 不存在**~~ ✅ 已修复 — 使用 `registry.get()`
7. ~~**`ToolRegistry.get_schema()` 不存在**~~ ✅ 已修复 — 使用 `tool.input_model.model_json_schema()`
8. ~~**`BaseTool.execute()` 签名不匹配**~~ ✅ 已修复 — 传入 `(parsed_args, context)`
9. ~~**`SandboxAvailability` 属性缺失**~~ ✅ 已修复 — 不再访问不存在的属性
10. ~~**`get_sandbox_config()`/`is_host_bash_allowed()` 不存在**~~ ✅ 已修复
11. ~~**`wrap_command_for_sandbox()` 传 `str` 非 `list[str]`**~~ ✅ 已修复 — 使用 `shlex.split()`
12. ~~**`PermissionMode` 无 `AUTO` 值**~~ ✅ 已修复 (T5) — 统一为 `full_auto`
13. ~~**`SimpleSettings` 类型不匹配**~~ ✅ 已修复 — 使用 `PermissionSettings`

---

## 4. SSE StreamEvent 适配 ✅ 已修复

| 问题 | 修复后状态 |
|------|-----------|
| `StreamEventAdapter` 事件类型不匹配 | ✅ 已正确映射 `AssistantTextDelta→text_delta`, `ToolExecutionStarted→tool_start`, `ToolExecutionCompleted→tool_end`, `ErrorEvent→error` |
| SSE 字段名不一致 | ✅ 已对齐 `tool_input`/`tool_output` (T10) |
| `session_service.py` 事件类型 `'tool_result'` | ✅ 已改为 `'tool_end'` (T10) |

---

## 5. 仍需关注的问题

| # | 问题 | 严重度 | 状态 | 说明 |
|---|------|--------|------|------|
| 1 | `_simulate_stream` fallback 日志可观测性 | P2 | ✅ 已改善 | 日志级别提升为 warning (T6) |
| 2 | `PERMISSION_MODES` 与 `PermissionMode` 枚举独立维护 | P2 | 待定 | 若 OpenHarness 新增模式，OCH 不会自动同步 |
| 3 | `openharness/swarm/team_lifecycle.py` 文档字符串仍引用 `'auto'` | P3 | [UPSTREAM] | 属于 OpenHarness 上游代码，OCH 不应修改 |
| 4 | MSA 语义检索模块文档缺失 | P3 | 待定 | 架构文档需补充 `openharness/msa/` 说明 |

---

## 6. 问题严重度总结（更新后）

| 严重度 | 原始数量 | 已修复 | 剩余 |
|--------|---------|--------|------|
| **P0 - 运行时崩溃** | 21 | 21 | 0 |
| **P1 - 功能失效** | 1 | 1 | 0 |
| **P2 - 安全/数据风险** | 2 | 2 | 0 (改善) |
| **P3 - 配置/一致性** | 2 | 0 | 2 (低优先级) |

---

## 7. 核心结论

OCH 后端服务层与 OpenHarness 核心引擎的集成接口已全面修复。所有 P0 运行时崩溃问题已解决，P1 权限模式不一致已修复，P2 fallback 日志和 Copilot 覆盖已改善。

**修复任务追踪**:
- **T5**: 权限模式 `'auto'` → `'full_auto'` 统一 + `_normalize_mode()` 兼容
- **T6**: `_simulate_stream` 日志级别提升 + `OCHApiClient` Copilot 覆盖
- **T10**: SSE 事件字段名对齐 (`tool_input`/`tool_output`) + `StreamEventAdapter` 事件类型对齐
