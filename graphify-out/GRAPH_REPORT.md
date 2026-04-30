# Graph Report - .  (2026-04-09)

## Corpus Check
- Large corpus: 315 files · ~153,677 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 4135 nodes · 9390 edges · 99 communities detected
- Extraction: 54% EXTRACTED · 46% INFERRED · 0% AMBIGUOUS · INFERRED: 4348 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `ToolExecutionContext` - 212 edges
2. `BaseTool` - 209 edges
3. `ToolResult` - 206 edges
4. `OutboundMessage` - 183 edges
5. `BaseChannel` - 174 edges
6. `MessageBus` - 166 edges
7. `ConversationMessage` - 155 edges
8. `Services package — business logic layer.` - 111 edges
9. `NotFoundError` - 95 edges
10. `Agent` - 82 edges

## Surprising Connections (you probably didn't know these)
- `Provider/auth capability helpers.` --uses--> `Settings`  [INFERRED]
  backend/openharness/api/provider.py → backend/openharness/config/settings.py
- `Resolved provider metadata for UI and diagnostics.` --uses--> `Settings`  [INFERRED]
  backend/openharness/api/provider.py → backend/openharness/config/settings.py
- `Infer the active provider and rough capability set using the registry.` --uses--> `Settings`  [INFERRED]
  backend/openharness/api/provider.py → backend/openharness/config/settings.py
- `Return a compact auth status string.` --uses--> `Settings`  [INFERRED]
  backend/openharness/api/provider.py → backend/openharness/config/settings.py
- `Load all bundled skills from the content/ directory.` --uses--> `SkillDefinition`  [INFERRED]
  backend/openharness/skills/bundled/__init__.py → backend/openharness/skills/types.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.01
Nodes (262): Agent, Agent model — represents an AI agent configuration., Agent 实体 — 对应 OpenHarness 的 Agent 配置., 工具级权限配置 — 每个 Agent 可以单独配置每个工具的权限., ToolPermission, Agent Management API — Complete CRUD with database operations., 创建新 Agent（需要 Admin 权限）     ---     tags:       - Agents     security:       - Be, 列出所有 Agent，支持分页、筛选和搜索     ---     tags:       - Agents     security:       - Bea (+254 more)

### Community 1 - "Community 1"
Cohesion: 0.01
Nodes (239): ChannelBridge, ChannelBridge: connects the MessageBus to a QueryEngine instance.  Usage::, Bridges inbound channel messages to the QueryEngine and routes replies back., Start the bridge loop as a background task., Stop the bridge loop gracefully., Run the bridge inline (blocks until stopped or cancelled)., Main processing loop: consume → process → publish., Process one inbound message and publish the reply. (+231 more)

### Community 2 - "Community 2"
Cohesion: 0.02
Nodes (265): AgentTool, AgentToolInput, Tool for spawning local agent tasks., Arguments for local agent spawning., Spawn a local agent subprocess., AskUserQuestionTool, AskUserQuestionToolInput, Tool for asking the interactive user a follow-up question. (+257 more)

### Community 3 - "Community 3"
Cohesion: 0.02
Nodes (269): Interactive session entry points., Run the default OpenHarness interactive application (React TUI)., Non-interactive mode: submit prompt, stream output, exit., run_print_mode(), run_repl(), AppState, Minimal application state model., Shared mutable UI/session state. (+261 more)

### Community 4 - "Community 4"
Cohesion: 0.02
Nodes (197): PermissionChecker, _drain_mailbox(), get_teammate_context(), InProcessBackend, In-process teammate execution backend.  Runs teammate agents as asyncio Tasks in, The reason provided to the most recent :meth:`request_cancel` call., All per-teammate state that must be isolated across concurrent agents.      Stor, Graceful cancellation event (delegates to :attr:`abort_controller`). (+189 more)

### Community 5 - "Community 5"
Cohesion: 0.03
Nodes (57): AutonomousWorker, 自治 Worker 模块  参考实现: Claude Code src/utils/swarm/inProcessRunner.ts  提供 Worker 的自, Worker 主循环          状态机实现:         - idle: 轮询任务看板和收件箱         - working: 执行已认领的任, 空闲循环：轮询收件箱和任务看板          参考 Claude Code inProcessRunner.ts 的空闲检测逻辑:         - 工作, 获取可认领的任务（pending 且无未完成依赖）, 身份信息注入          当上下文过短时（可能因为压缩），重新注入身份信息，         防止 Worker 忘记自己是谁。          参考, 从记忆中检索相关经验并追加到 prompt, 便捷函数：启动一个自治 Worker      Args:         config: Worker 配置（可选，使用默认值）         agent_ (+49 more)

### Community 6 - "Community 6"
Cohesion: 0.02
Nodes (110): audit_stats(), export_audit_logs(), _export_impl(), get_audit_log(), _get_log_impl(), list_audit_logs(), _list_logs_impl(), _purge_impl() (+102 more)

### Community 7 - "Community 7"
Cohesion: 0.04
Nodes (95): Hook execution engine., Context passed into hook execution., Execute hooks for lifecycle events., Replace the active hook registry., Execute all matching hooks for an event., discover_plugin_paths(), _find_manifest(), get_custom_themes_dir() (+87 more)

### Community 8 - "Community 8"
Cohesion: 0.03
Nodes (36): _match_glob(), PermissionService, Permission Service — RBAC and path-based access control., 检查工具执行权限.          Returns:             {                 'allowed': bool,, perm_service(), Permission Service 单元测试 — 验证 RBAC 权限控制和路径规则管理.  测试覆盖范围： 1. 权限规则 CRUD（Create, Rea, 列出所有规则 — 不包含编译后的正则对象., allow 列表匹配返回 True — 安全路径被放行. (+28 more)

### Community 9 - "Community 9"
Cohesion: 0.04
Nodes (38): Tool Service 单元测试 — 验证工具注册、发现机制和安全验证逻辑.  测试覆盖范围： 1. 工具注册和发现机制（列表、详情、分类） 2. 工具调用权, 按分类筛选工具 — 验证 category 过滤功能., 列出所有可用工具 — 包含危险和非危险工具., 仅列出安全工具 — 排除 dangerous=True 的工具., 危险工具被自动拦截 — 返回 decision='ask'., 安全工具自动允许 — 返回 allowed=True., 安全验证测试 — 覆盖各类攻击向量.      测试场景包括：     - 危险命令检测（rm -rf, sudo, > /dev/sda）     - 路径遍, 阻止危险命令执行 — 攻击向量: {attack_desc}.          测试目标：验证系统能够识别并阻止常见的破坏性命令。 (+30 more)

### Community 10 - "Community 10"
Cohesion: 0.04
Nodes (68): add_hidden_pane_id(), AllowedPath, check_path_whitelist(), cleanup_session_teams(), cleanup_team_directories(), _destroy_worktree(), from_dict(), get_team_file_path() (+60 more)

### Community 11 - "Community 11"
Cohesion: 0.03
Nodes (30): CoordinatorService, Coordinator Service — multi-agent team management., 生成子 Agent 执行任务.          Returns task info with status tracking., # TODO: 实际启动子 Agent 进程/线程, 多智能体协调服务 — 管理团队、子 Agent、任务分发., Coordinator Service 单元测试 — 验证多智能体协调和任务分派., 创建 CoordinatorService 实例., 测试 Code Reviewer 的能力配置. (+22 more)

### Community 12 - "Community 12"
Cohesion: 0.05
Nodes (59): ABC, auth_copilot_login(), auth_copilot_logout(), auth_login(), auth_logout(), auth_status_cmd(), auth_switch(), cron_history_cmd() (+51 more)

### Community 13 - "Community 13"
Cohesion: 0.04
Nodes (22): _compute_integrity_hash(), _parse_plugin_metadata(), PluginService, Plugin Service — manage extensions lifecycle., # TODO: 执行插件的 enable hooks, # TODO: 执行插件的 disable hooks, 插件管理服务 — 安装、卸载、启用、禁用插件., 安装插件.          Args:             source: URL 或本地路径             source_type: 'loc (+14 more)

### Community 14 - "Community 14"
Cohesion: 0.07
Nodes (33): McpClientManager, Read one MCP resource and stringify the response., Manage MCP connections and expose tools/resources., Connect all configured stdio MCP servers., Reconnect all configured servers., Replace one server config in memory., Return one configured server object if present., Close all active MCP sessions. (+25 more)

### Community 15 - "Community 15"
Cohesion: 0.04
Nodes (23): Skill Service — manage .md knowledge base skills., # TODO: 实现启用逻辑（如创建软链接或修改状态）, # TODO: 实现禁用逻辑, 技能服务 — 管理 Markdown 知识库技能., 获取技能详情（含 Markdown 内容）., SkillService, Skill Service 单元测试 — 验证技能管理核心业务逻辑., 解析带 frontmatter 的 Markdown 文件. (+15 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (39): CircularDependencyError, 任务依赖图（DAG）管理器  参考实现: Claude Code src/utils/tasks.ts  提供任务依赖关系的创建、查询和自动解锁功能。 支持 D, 初始化 DAG 管理器          Args:             task_manager: BackgroundTaskManager 实例, Exception, CoordinationProtocolHandler, ProtocolTimeoutError, 协调协议处理器  实现团队协调协议的核心逻辑: 1. 关机握手流程（请求 → 收尾 → 确认 → 终止） 2. 权限审批流程（Worker → Leader →, Worker 处理关机请求          流程:         1. 收到请求         2. 如果 graceful=True，执行收尾工作: (+31 more)

### Community 17 - "Community 17"
Cohesion: 0.05
Nodes (28): add_memory_entry(), BackgroundTaskManager, BridgeSessionManager, get_bridge_manager(), get_task_manager(), list_memory_files(), Return the singleton bridge manager., Update mutable task metadata used for coordination and UI display. (+20 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (39): PathRule, PermissionDecision, Permission checking for tool execution., Result of checking whether a tool invocation may run., A glob-based path permission rule., Evaluate tool usage against the configured permission mode and rules., Return whether the tool may run immediately., PermissionMode (+31 more)

### Community 19 - "Community 19"
Cohesion: 0.04
Nodes (14): Permission API 单元测试 — 验证 RBAC 权限控制、路径规则管理和 DenialTracker 集成., 测试 DenialTracker 内存追踪器 API., 测试获取 DenialTracker 内存状态统计., 测试清除 DenialTracker 内存缓存., 测试统一工具权限检查 API（三重校验：DenialTracker + PermissionChecker + DB 规则）., 测试 Agent 级别权限配置 API (来自 agents.py)., 认证和授权测试 — 验证不同角色用户的访问权限., TestAgentPermissionsAPI (+6 more)

### Community 20 - "Community 20"
Cohesion: 0.05
Nodes (3): ApiClient, handlePurge(), loadData()

### Community 21 - "Community 21"
Cohesion: 0.06
Nodes (33): build_sandbox_runtime_config(), get_sandbox_availability(), Wrap an argv list with ``srt`` when sandboxing is active., Persist a temporary settings file for one sandboxed child process., Raised when sandboxing is required but unavailable., Computed sandbox-runtime availability for the current environment., Return whether sandboxing should be applied to child processes., Convert OpenHarness settings into an ``srt`` settings payload. (+25 more)

### Community 22 - "Community 22"
Cohesion: 0.06
Nodes (10): Task API 单元测试 — 验证后台任务 CRUD 操作、状态转换和 DAG 依赖管理., 测试更新任务状态（先转为 running，再转为 completed）., TestTaskCreateAPI, TestTaskDeleteAPI, TestTaskDependencyAPI, TestTaskGetAPI, TestTasksListAPI, TestTaskStatsAPI (+2 more)

### Community 23 - "Community 23"
Cohesion: 0.07
Nodes (25): format_task_notification(), get_coordinator_system_prompt(), get_coordinator_tools(), get_coordinator_user_context(), get_team_registry(), is_coordinator_mode(), match_session_mode(), parse_task_notification() (+17 more)

### Community 24 - "Community 24"
Cohesion: 0.06
Nodes (12): Tool API 单元测试 — 验证工具注册表查询、Schema 详情获取和分类筛选., 测试获取 Read 工具详情（验证不同工具的 Schema）., 测试获取 Bash 工具的 JSON Schema., 测试获取 Write 工具的 JSON Schema., 测试响应中不包含敏感信息（如 API Key）., TestToolCategoriesAPI, TestToolDetailAPI, TestToolExamplesAPI (+4 more)

### Community 25 - "Community 25"
Cohesion: 0.06
Nodes (10): Coordinator API 单元测试 — 验证多智能体任务协调、团队管理和并发控制., 测试列出任务依赖关系（通过 Agent 定义列表）., 测试创建团队缺少名称 (422/500)., 测试获取不存在的 Agent 定义 (404)., TestConcurrencyAPI, TestCoordinatorStatusAPI, TestSubagentExecutionAPI, TestTaskSubmissionAPI (+2 more)

### Community 26 - "Community 26"
Cohesion: 0.1
Nodes (30): append_history(), execute_job(), get_history_path(), get_pid_path(), is_scheduler_running(), _jobs_due(), load_history(), Background cron scheduler daemon.  Runs as a standalone process (``oh cron start (+22 more)

### Community 27 - "Community 27"
Cohesion: 0.06
Nodes (10): Skill API 单元测试 — 验证技能库 CRUD 操作、启用/禁用切换和安装管理., 测试缺少 directory 参数时使用默认路径., 测试分页参数支持（即使当前实现未使用分页）., TestSkillCategoriesAPI, TestSkillCreateAPI, TestSkillDeleteAPI, TestSkillGetAPI, TestSkillScanAPI (+2 more)

### Community 28 - "Community 28"
Cohesion: 0.06
Nodes (8): 消息渠道管理 API 单元测试 — 验证多平台渠道 CRUD、配置和健康检查., TestChannelDeleteAPI, TestChannelDetailAndUpdateAPI, TestChannelListAPI, TestChannelRegistrationAPI, TestChannelSendAndTestAPI, TestChannelStatsAPI, TestChannelTypesAPI

### Community 29 - "Community 29"
Cohesion: 0.09
Nodes (29): get_config_dir(), get_config_file_path(), get_cron_registry_path(), get_data_dir(), get_feedback_dir(), get_feedback_log_path(), get_logs_dir(), get_memory_entrypoint() (+21 more)

### Community 30 - "Community 30"
Cohesion: 0.07
Nodes (9): MCP 服务器管理 API 单元测试 — 验证服务器 CRUD、工具发现和连接状态., 测试获取服务器工具列表（Mock 数据）., 测试获取服务器资源列表（Mock 数据）., TestMCPConnectionTestAPI, TestMCPServerCreateAPI, TestMCPServerDeleteAPI, TestMCPServerGetAndUpdateAPI, TestMCPServerListAPI (+1 more)

### Community 31 - "Community 31"
Cohesion: 0.1
Nodes (20): create_team(), _create_team_impl(), delete_team(), _delete_team_impl(), get_team(), _get_team_impl(), list_agent_definitions(), _list_agents_impl() (+12 more)

### Community 32 - "Community 32"
Cohesion: 0.07
Nodes (9): Session & Chat API 单元测试 — 验证会话管理和 SSE 流式聊天., TestChatAPI, TestMessagesAPI, TestSessionCreateAPI, TestSessionDeleteAPI, TestSessionGetAPI, TestSessionListAPI, TestSessionPauseResumeAPI (+1 more)

### Community 33 - "Community 33"
Cohesion: 0.12
Nodes (20): _flatten_slug(), Git worktree isolation for swarm agents., Symlink large common directories from the main repo to avoid duplication., Remove symlinks created by _symlink_common_dirs., Manage git worktrees for isolated agent execution.      Worktrees are stored und, Create (or resume) a git worktree for *slug*.          If the worktree directory, Remove a worktree by slug.          Cleans up symlinks first, then runs ``git wo, Sanitize and validate a worktree slug.      Rules:     - Max 64 characters total (+12 more)

### Community 34 - "Community 34"
Cohesion: 0.08
Nodes (8): Agent API 单元测试 — 验证 CRUD 操作和权限控制., TestAgentCreateAPI, TestAgentDeleteAPI, TestAgentGetAPI, TestAgentListAPI, TestAgentPermissionsAPI, TestAgentStatsAPI, TestAgentUpdateAPI

### Community 35 - "Community 35"
Cohesion: 0.08
Nodes (8): Sandbox API 单元测试 — 验证沙箱环境管理、代码执行隔离和安全控制., 测试成功创建沙箱实例（通过 wrap 端点验证沙箱可用性）., 测试无效的沙箱配置请求 (422/400)., TestSandboxCreateAPI, TestSandboxExecutionAPI, TestSandboxLifecycleAPI, TestSandboxListAPI, TestSandboxSecurityCheckAPI

### Community 36 - "Community 36"
Cohesion: 0.12
Nodes (23): AgentDefinition, filter_agents_by_mcp_requirements(), get_agent_definition(), get_all_agent_definitions(), get_builtin_agent_definitions(), _get_user_agents_dir(), has_required_mcp_servers(), load_agents_dir() (+15 more)

### Community 37 - "Community 37"
Cohesion: 0.08
Nodes (9): 配置管理 API 单元测试 — 验证配置读取、更新权限和敏感信息脱敏., 测试获取配置 Schema（用于前端表单验证）., 测试 LLM Provider 管理 API., TestConfigGetAPI, TestConfigProvidersAPI, TestConfigResetAPI, TestConfigSchemaAPI, TestConfigUpdateAPI (+1 more)

### Community 38 - "Community 38"
Cohesion: 0.13
Nodes (22): _add_dep_impl(), add_dependency(), create_task(), _create_task_impl(), create_with_dependencies(), _create_with_deps_impl(), delete_task(), _delete_task_impl() (+14 more)

### Community 39 - "Community 39"
Cohesion: 0.12
Nodes (21): api_base(), _auth_file_path(), clear_github_token(), copilot_api_base(), CopilotAuthInfo, DeviceCodeResponse, load_copilot_auth(), load_github_token() (+13 more)

### Community 40 - "Community 40"
Cohesion: 0.17
Nodes (20): clear_provider_credentials(), _creds_path(), decrypt(), encrypt(), _keyring_available(), _keyring_key(), list_stored_providers(), load_credential() (+12 more)

### Community 41 - "Community 41"
Cohesion: 0.17
Nodes (7): AgentMemory, AgentMemoryConfig, get_memory_for_agent(), import_json(), MemoryEntry, MemoryQuery, Agent 内存管理系统（Agent Memory）  为每个 Agent 提供跨会话的持久化记忆存储能力。 支持记忆的记录、检索、删除、整合和导入导出。  参

### Community 42 - "Community 42"
Cohesion: 0.17
Nodes (19): delete_cron_job(), get_cron_job(), load_cron_jobs(), mark_job_run(), next_run_time(), Local cron-style registry helpers., Load stored cron jobs., Persist cron jobs to disk. (+11 more)

### Community 43 - "Community 43"
Cohesion: 0.18
Nodes (2): handle_submit(), OpenHarnessTerminalApp

### Community 44 - "Community 44"
Cohesion: 0.15
Nodes (19): create_fact(), _create_fact_impl(), delete_fact(), _delete_fact_impl(), get_fact(), _get_fact_impl(), list_facts(), _list_facts_impl() (+11 more)

### Community 45 - "Community 45"
Cohesion: 0.16
Nodes (18): agent_stats(), _agent_stats_impl(), create_agent(), _create_agent_impl(), delete_agent(), _delete_agent_impl(), duplicate_agent(), _duplicate_agent_impl() (+10 more)

### Community 46 - "Community 46"
Cohesion: 0.11
Nodes (17): decode_jwt(), generate_api_key(), hash_password(), init_security(), Security utilities: JWT authentication, password hashing, etc., Decorator to require specific roles., Generate a secure API key., Initialize security configuration on the Flask app. (+9 more)

### Community 47 - "Community 47"
Cohesion: 0.16
Nodes (16): detect_git_info(), detect_os(), detect_shell(), EnvironmentInfo, get_environment_info(), Environment detection for system prompt construction.  Gathers OS, shell, platfo, Gather all environment information into an EnvironmentInfo snapshot., Snapshot of the current runtime environment. (+8 more)

### Community 48 - "Community 48"
Cohesion: 0.18
Nodes (5): _ext_to_lexer(), _fmt_num(), _has_markdown(), OutputRenderer, _summarize_tool_input()

### Community 49 - "Community 49"
Cohesion: 0.17
Nodes (14): auth_status(), detect_provider(), ProviderInfo, Provider/auth capability helpers., Resolved provider metadata for UI and diagnostics., Infer the active provider and rough capability set using the registry., Return a compact auth status string., inspect_voice_capabilities() (+6 more)

### Community 50 - "Community 50"
Cohesion: 0.19
Nodes (15): disable_skill(), enable_skill(), get_skill(), _get_skill_impl(), install_skill(), _install_skill_impl(), _list_categories_impl(), list_skill_categories() (+7 more)

### Community 51 - "Community 51"
Cohesion: 0.17
Nodes (8): CompactWarningConfig, CompactWarningHook, CompactWarningResult, 压缩警告 Hook。  当对话接近模型的上下文窗口上限时，主动发出警告。 支持可配置的阈值和自定义警告消息。, 估算消息列表的总 token 数（复用专业 token 估算器）, 检查消息列表的上下文使用率          这是便捷方法，结合了 token 估算和使用率检查, 压缩警告检测器。      在每次添加消息到历史记录时检查上下文使用率，     当接近上限时发出警告。, 检查当前上下文使用率并决定是否需要警告          Args:             current_token_count: 当前已使用的 token

### Community 52 - "Community 52"
Cohesion: 0.21
Nodes (13): build_backend_command(), get_frontend_dir(), launch_react_tui(), Launch the default React terminal frontend., Launch the React terminal frontend as the default UI., Read the theme name from settings, defaulting to 'default'., Resolve the npm executable (npm.cmd on Windows)., Resolve the tsx command to invoke directly, bypassing ``npm exec``.      On Wind (+5 more)

### Community 53 - "Community 53"
Cohesion: 0.15
Nodes (8): emit_session_event(), emit_system_notification(), emit_tool_progress(), on_join_session(), WebSocket Handler — Real-time communication via Socket.IO.  Provides real-time u, 发送系统级通知（广播给所有连接的客户端）., 加入会话房间 — 接收该会话的实时更新.      Event data:     {       "session_id": "uuid"     }, 向特定会话的所有监听者发送事件.      Usage (from other modules):         from app.api.websocket

### Community 54 - "Community 54"
Cohesion: 0.27
Nodes (11): addSortIndicators(), enableUI(), getNthColumn(), getTable(), getTableBody(), getTableHeader(), loadColumns(), loadData() (+3 more)

### Community 55 - "Community 55"
Cohesion: 0.17
Nodes (11): build_inherited_cli_flags(), build_inherited_env_vars(), get_teammate_command(), is_inside_tmux(), is_tmux_available(), Shared utilities for spawning teammate processes., Build CLI flags to propagate from the current session to spawned teammates., Build environment variables to forward to spawned teammates.      Always include (+3 more)

### Community 56 - "Community 56"
Cohesion: 0.18
Nodes (6): InputSession, Input helpers built on prompt_toolkit., Update prompt decorations for active modes., Prompt the user for one line of input., Prompt the user for an ad-hoc answer., Async prompt wrapper.

### Community 57 - "Community 57"
Cohesion: 0.35
Nodes (8): a(), B(), D(), g(), i(), k(), Q(), y()

### Community 58 - "Community 58"
Cohesion: 0.27
Nodes (9): detect_platform(), get_platform(), get_platform_capabilities(), PlatformCapabilities, Platform and capability detection helpers., Capabilities that drive shell, swarm, and sandbox decisions., Return the normalized platform name for the current process., Return the detected platform for this process. (+1 more)

### Community 59 - "Community 59"
Cohesion: 0.29
Nodes (9): exclusive_file_lock(), _exclusive_posix_lock(), _exclusive_windows_lock(), Cross-platform file-lock helpers for swarm mailbox and permission storage., Base error for swarm lock failures., Raised when file locking is unavailable on the current platform., Acquire an exclusive file lock for swarm mailbox/permission operations., SwarmLockError (+1 more)

### Community 60 - "Community 60"
Cohesion: 0.22
Nodes (9): _create_session_factory(), get_db(), 统一异步工具 — 消除各 API 模块中 _run_async / _get_db 的重复定义.  核心修复：Flask 同步视图函数调用 async 代码时，, 设置测试用的会话工厂（由 conftest.py 调用）., 创建独立的数据库会话工厂（每次调用创建新引擎）., 在同步上下文中运行异步协程.      每次调用创建独立的事件循环，确保 asyncpg 连接池     不会跨事件循环复用。, 获取数据库会话（统一入口）.      测试模式下使用注入的测试会话工厂，     生产模式下每次调用创建独立的引擎和会话工厂。, run_async() (+1 more)

### Community 61 - "Community 61"
Cohesion: 0.25
Nodes (7): close_db(), get_db(), init_db(), Database connection and session management., Dependency that provides a database session., Initialize database tables (for simple cases, use Alembic for migrations)., Close database connections.

### Community 62 - "Community 62"
Cohesion: 0.29
Nodes (2): getCellValue(), rowComparator()

### Community 63 - "Community 63"
Cohesion: 0.33
Nodes (5): install_plugin_from_path(), Plugin installation helpers., Install a plugin directory into the user plugin directory., Remove a user plugin by directory name., uninstall_plugin()

### Community 64 - "Community 64"
Cohesion: 0.4
Nodes (5): discover_claude_md_files(), load_claude_md_prompt(), CLAUDE.md discovery and loading., Load discovered instruction files into one prompt section., Discover relevant CLAUDE.md instruction files from the cwd upward.

### Community 65 - "Community 65"
Cohesion: 0.4
Nodes (3): Alembic environment configuration., run_async_migrations(), run_migrations_online()

### Community 66 - "Community 66"
Cohesion: 0.7
Nodes (4): goToNext(), goToPrevious(), makeCurrent(), toggleClass()

### Community 67 - "Community 67"
Cohesion: 0.5
Nodes (3): Minimal Vim mode state helpers., Toggle Vim mode state., toggle_vim_mode()

### Community 68 - "Community 68"
Cohesion: 0.5
Nodes (3): Placeholder streaming STT interface., Return a placeholder message for unimplemented STT., transcribe_stream()

### Community 69 - "Community 69"
Cohesion: 0.5
Nodes (3): extract_keyterms(), Voice mode keyterm extraction., Extract likely key terms from a transcript.

### Community 70 - "Community 70"
Cohesion: 0.5
Nodes (3): load_memory_prompt(), Memory prompt helpers., Return the memory prompt section for the current project.

### Community 71 - "Community 71"
Cohesion: 0.5
Nodes (3): parse_keybindings(), Keybinding file parsing., Parse a JSON keybinding mapping.

### Community 72 - "Community 72"
Cohesion: 0.5
Nodes (3): Keybinding resolution., Merge user overrides over the default keybindings., resolve_keybindings()

### Community 73 - "Community 73"
Cohesion: 0.5
Nodes (3): ask_permission(), Interactive permission prompt., Prompt the user to approve a mutating tool.

### Community 74 - "Community 74"
Cohesion: 0.5
Nodes (1): Initial migration for OpenClaw-Harness.  Revision ID: 001_initial Create Date: 2

### Community 75 - "Community 75"
Cohesion: 0.67
Nodes (0): 

### Community 76 - "Community 76"
Cohesion: 1.0
Nodes (1): Default keybinding map.

### Community 77 - "Community 77"
Cohesion: 1.0
Nodes (0): 

### Community 78 - "Community 78"
Cohesion: 1.0
Nodes (0): 

### Community 79 - "Community 79"
Cohesion: 1.0
Nodes (1): Return the total number of accounted tokens.

### Community 80 - "Community 80"
Cohesion: 1.0
Nodes (1): Execute the flow and return the obtained credential value.

### Community 81 - "Community 81"
Cohesion: 1.0
Nodes (1): Attempt to open *url* in the default browser; return True if likely succeeded.

### Community 82 - "Community 82"
Cohesion: 1.0
Nodes (1): Construct a user message from raw text.

### Community 83 - "Community 83"
Cohesion: 1.0
Nodes (1): Return concatenated text blocks.

### Community 84 - "Community 84"
Cohesion: 1.0
Nodes (1): Return all tool calls contained in the message.

### Community 85 - "Community 85"
Cohesion: 1.0
Nodes (1): Return whether any hook blocked continuation.

### Community 86 - "Community 86"
Cohesion: 1.0
Nodes (1): Return the first blocking reason, if any.

### Community 87 - "Community 87"
Cohesion: 1.0
Nodes (1): The type identifier for this backend.

### Community 88 - "Community 88"
Cohesion: 1.0
Nodes (1): Human-readable display name for this backend.

### Community 89 - "Community 89"
Cohesion: 1.0
Nodes (1): Whether this backend supports hiding and showing panes.

### Community 90 - "Community 90"
Cohesion: 1.0
Nodes (1): Load a TeamFile from *path*.          Raises:             FileNotFoundError: if

### Community 91 - "Community 91"
Cohesion: 1.0
Nodes (1): Unique key for session identification.

### Community 92 - "Community 92"
Cohesion: 1.0
Nodes (0): 

### Community 93 - "Community 93"
Cohesion: 1.0
Nodes (0): 

### Community 94 - "Community 94"
Cohesion: 1.0
Nodes (0): 

### Community 95 - "Community 95"
Cohesion: 1.0
Nodes (0): 

### Community 96 - "Community 96"
Cohesion: 1.0
Nodes (0): 

### Community 97 - "Community 97"
Cohesion: 1.0
Nodes (0): 

### Community 98 - "Community 98"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **509 isolated node(s):** `Platform and capability detection helpers.`, `Capabilities that drive shell, swarm, and sandbox decisions.`, `Return the normalized platform name for the current process.`, `Return the detected platform for this process.`, `Return the capability matrix for a normalized platform name.` (+504 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 76`** (2 nodes): `default_bindings.py`, `Default keybinding map.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 77`** (2 nodes): `appStore.ts`, `appStore.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 78`** (2 nodes): `MarkdownRenderer.tsx`, `handleCopy()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 79`** (1 nodes): `Return the total number of accounted tokens.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 80`** (1 nodes): `Execute the flow and return the obtained credential value.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 81`** (1 nodes): `Attempt to open *url* in the default browser; return True if likely succeeded.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 82`** (1 nodes): `Construct a user message from raw text.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 83`** (1 nodes): `Return concatenated text blocks.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 84`** (1 nodes): `Return all tool calls contained in the message.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 85`** (1 nodes): `Return whether any hook blocked continuation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 86`** (1 nodes): `Return the first blocking reason, if any.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 87`** (1 nodes): `The type identifier for this backend.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 88`** (1 nodes): `Human-readable display name for this backend.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 89`** (1 nodes): `Whether this backend supports hiding and showing panes.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 90`** (1 nodes): `Load a TeamFile from *path*.          Raises:             FileNotFoundError: if`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 91`** (1 nodes): `Unique key for session identification.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 92`** (1 nodes): `next.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 93`** (1 nodes): `jest.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 94`** (1 nodes): `next-env.d.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 95`** (1 nodes): `postcss.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 96`** (1 nodes): `tailwind.config.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 97`** (1 nodes): `jest.setup.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 98`** (1 nodes): `fileMock.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Services package — business logic layer.` connect `Community 2` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 9`, `Community 11`, `Community 12`, `Community 13`, `Community 15`, `Community 18`, `Community 21`?**
  _High betweenness centrality (0.355) - this node is a cross-community bridge._
- **Why does `ConversationMessage` connect `Community 3` to `Community 0`, `Community 2`, `Community 4`, `Community 7`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `OutboundMessage` connect `Community 1` to `Community 2`, `Community 5`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 210 inferred relationships involving `ToolExecutionContext` (e.g. with `TaskOutputToolInput` and `TaskOutputTool`) actually correct?**
  _`ToolExecutionContext` has 210 INFERRED edges - model-reasoned connections that need verification._
- **Are the 204 inferred relationships involving `BaseTool` (e.g. with `TaskOutputToolInput` and `TaskOutputTool`) actually correct?**
  _`BaseTool` has 204 INFERRED edges - model-reasoned connections that need verification._
- **Are the 204 inferred relationships involving `ToolResult` (e.g. with `TaskOutputToolInput` and `TaskOutputTool`) actually correct?**
  _`ToolResult` has 204 INFERRED edges - model-reasoned connections that need verification._
- **Are the 181 inferred relationships involving `OutboundMessage` (e.g. with `ChannelBridge` and `ChannelBridge: connects the MessageBus to a QueryEngine instance.  Usage::`) actually correct?**
  _`OutboundMessage` has 181 INFERRED edges - model-reasoned connections that need verification._