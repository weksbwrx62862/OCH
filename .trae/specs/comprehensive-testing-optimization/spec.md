# OpenClaw-Harness 全面测试优化规范

## Why
当前 openclaw-harness 项目作为 openclaw 的外挂扩展项目，虽然核心 API 测试已通过（34/34），但整体测试覆盖率仅 47%，Service 层测试几乎为空（0-40%），且存在 Pydantic V2 配置过时、事件循环警告等技术债务。需要系统性地提升测试质量、修复技术问题、并参考 openclaw-main 源码的测试模式建立完善的测试体系。

## What Changes

### 高优先级优化 🔴
1. **补充 Service 层单元测试** - 覆盖 7 个服务模块（session_service, skill_service, tool_service, permission_service, plugin_service, coordinator_service, subagent_executor）
2. **扩展 API 模块测试** - 新增 tasks, skills, tools, permissions, audit, memory, mcp, channels, config, sandbox, coordinator 等 11 个 API 模块测试
3. **添加集成测试场景** - 端到端业务流程测试（Agent 创建 → Session 建立 → Chat 交互 → 消息记录）

### 中优先级优化 🟡
4. **Pydantic V2 配置迁移** - 将 `class Config` 更新为 `model_config = ConfigDict()` 方式
5. **事件循环警告修复** - 解决 conftest.py 中 `asyncio.get_event_loop()` 的 DeprecationWarning
6. **前端单元测试框架搭建** - 引入 Jest + React Testing Library，为核心组件编写测试

### 低优先级优化 🟢
7. **依赖安全修复** - 执行 npm audit fix 修复高危漏洞
8. **前端性能优化** - 聊天页面代码分割（41.8 kB → 动态加载）
9. **API 文档完善** - 补充 OpenAPI/Swagger 文档和架构说明

## Impact

### 受影响的规范
- 测试框架：pytest + pytest-asyncio（后端）、Jest + RTL（前端）
- 代码覆盖率目标：从 47% 提升至 75%+
- CI/CD 集成：支持自动化测试流水线

### 受影响的关键代码文件
**后端新增测试文件：**
- `backend/tests/test_session_service.py`
- `backend/tests/test_skill_service.py`
- `backend/tests/test_tool_service.py`
- `backend/tests/test_permission_service.py`
- `backend/tests/test_plugin_service.py`
- `backend/tests/test_coordinator_service.py`
- `backend/tests/test_subagent_executor.py`
- `backend/tests/test_tasks_api.py`
- `backend/tests/test_skills_api.py`
- `backend/tests/test_tools_api.py`
- `backend/tests/test_permissions_api.py`
- `backend/tests/test_audit_api.py`
- `backend/tests/test_memory_api.py`
- `backend/tests/test_integration.py`

**后端修改文件：**
- `backend/app/config.py` (Pydantic V2 迁移)
- `backend/tests/conftest.py` (事件循环修复)

**前端新增文件：**
- `frontend/jest.config.js`
- `frontend/jest.setup.ts`
- `frontend/__tests__/components/*.test.tsx`

**前端修改文件：**
- `frontend/package.json` (添加 Jest 依赖)
- `frontend/app/chat/page.tsx` (代码分割)

---

## ADDED Requirements

### Requirement: Service 层单元测试覆盖
系统应为所有 Service 模块提供完整的单元测试，覆盖率达到 70%+。

#### Scenario: SessionService 核心方法测试
- **WHEN** 调用 `create_session()` 方法
- **THEN** 应成功创建 Session 记录并返回包含 id, agent_id, status 的对象

#### Scenario: SkillService CRUD 操作测试
- **WHEN** 执行技能的增删改查操作
- **THEN** 所有操作应正确反映到数据库，并处理边界条件（重复名称、不存在 ID 等）

#### Scenario: ToolService 权限验证测试
- **WHEN** 验证工具调用权限
- **THEN** 应根据 PermissionRule 正确允许或拒绝工具执行

### Requirement: API 模块完整测试覆盖
系统应为所有 API 端点提供完整的 HTTP 层测试，包括认证、授权、输入验证和错误处理。

#### Scenario: Tasks API CRUD 测试
- **WHEN** 用户通过 REST API 操作任务
- **THEN** API 应正确响应 201/200/404/422 等状态码，并返回符合契约的数据结构

#### Scenario: Permissions API 权限控制测试
- **WHEN** 不同角色用户访问权限管理接口
- **THEN** Admin 角色应拥有完全权限，普通用户应被限制访问敏感操作

### Requirement: 端到端集成测试
系统应提供完整的业务流程集成测试，验证多组件协作的正确性。

#### Scenario: 完整对话流程测试
- **GIVEN** 已创建 Agent 和 Session
- **WHEN** 用户发送消息并接收流式响应
- **THEN** 消息应正确保存到数据库，Token 统计准确，Session 状态更新及时

### Requirement: Pydantic V2 配置现代化
配置类应使用 Pydantic V2 推荐的 `model_config = ConfigDict()` 语法。

#### Scenario: Settings 类迁移
- **WHEN** 加载应用配置
- **THEN** 应使用 ConfigDict 替代旧的 class Config，保持功能兼容性

### Requirement: 前端测试基础设施
前端项目应具备可运行的单元测试环境，能够测试 React 组件渲染和交互。

#### Scenario: 核心组件渲染测试
- **WHEN** 渲染 Agent 列表组件
- **THEN** 组件应正确显示 Agent 数据，处理加载和错误状态

---

## MODIFIED Requirements

### Requirement: 测试基础设施增强
现有的 conftest.py 应修复已知警告并提供更完善的测试辅助函数。

#### 场景：事件循环管理优化
- **WHEN** pytest 运行测试套件
- **THEN** 不应产生 DeprecationWarning，应使用 asyncio.new_event_loop() 或 pytest-asyncio 提供的 loop fixture

### Requirement: 代码质量门禁
所有新增代码应通过类型检查和 lint，覆盖率不低于 60%。

#### 场景：CI/CD 质量检查
- **WHEN** 提交代码或创建 PR
- **THEN** 自动运行测试套件，覆盖率低于阈值应阻断合并

---

## REMOVED Requirements
无（本次为增量优化，不删除现有功能）

---

## 技术约束与参考

### OpenClaw-Main 参考模式
基于 `/home/xxh/claudecode源码(仅用于学习交流)/openclaw-main/openclaw-main/src` 的测试实践：
- 使用 Vitest 作为测试运行器（TypeScript 项目）
- 测试文件命名：`*.test.ts` / `*.test.tsx`
- 采用 describe/it 组织测试结构
- 广泛使用 mock 和 fixture 模式

### 虚拟环境要求
- Python 虚拟环境位置：`/home/xxh/openclaw-harness/backend/venv/`
- 激活命令：`source /home/xxh/openclaw-harness/backend/venv/bin/activate`
- Node.js 环境：`/home/xxh/openclaw-harness/frontend/node_modules/.bin/`

### 测试数据管理
- 使用 SQLite 内存数据库进行隔离测试
- 每个 test function 使用独立的 db_session fixture
- 敏感数据使用 factory 模式生成唯一值避免冲突

---

## 成功标准

1. **后端测试数量**：从 34 个增至 150+ 个
2. **代码覆盖率**：从 47% 提升至 75%+
3. **Service 层覆盖率**：从 0-40% 提升至 70%+
4. **前端测试**：建立可运行的 Jest 环境，至少覆盖 5 个核心组件
5. **技术债务清零**：Pydantic 警告、事件循环警告全部修复
6. **所有测试在虚拟环境中通过**：确保环境一致性
