# OpenClaw-Harness 技术改进实施计划

## [ ] 任务 1：安全加固 - 密钥管理与验证
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 强制要求生产环境必须通过环境变量设置密钥
  - 移除默认密钥的硬编码值，改为必需配置
  - 添加密钥强度验证（长度、复杂度）
- **Acceptance Criteria Addressed**: 安全隐患排查 - 问题 3
- **Test Requirements**:
  - `programmatic` TR-1.1: 生产环境启动时缺少密钥会报错
  - `programmatic` TR-1.2: 开发环境仍可使用默认值但有警告
  - `programmatic` TR-1.3: 密钥长度检查（JWT_SECRET_KEY ≥ 32 字符）
- **Notes**: 修改 `backend/app/config.py` 中的 Settings 类

## [ ] 任务 2：安全加固 - 实现请求限流
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 使用 Flask-Limiter 或 Redis 实现 API 请求限流
  - 利用已配置的 RATE_LIMIT_REQUESTS 和 RATE_LIMIT_WINDOW_SECONDS
  - 添加限流信息到响应头
- **Acceptance Criteria Addressed**: 安全隐患排查 - 问题 3
- **Test Requirements**:
  - `programmatic` TR-2.1: 超过限制的请求返回 429
  - `programmatic` TR-2.2: 响应头包含限流信息
  - `programmatic` TR-2.3: 不同端点可以有不同限制
- **Notes**: 考虑使用 Redis 作为限流存储后端

## [ ] 任务 3：安全加固 - 收紧 CORS 策略
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - WebSocket 的 CORS 配置与 REST API 保持一致
  - 移除 cors_allowed_origins='*'
  - 使用 settings.CORS_ORIGINS 配置
- **Acceptance Criteria Addressed**: 安全隐患排查 - 问题 3
- **Test Requirements**:
  - `programmatic` TR-3.1: 非允许来源的 WebSocket 连接被拒绝
  - `programmatic` TR-3.2: 允许来源可以正常连接
- **Notes**: 修改 `backend/app/main.py` 中的 SocketIO 初始化

## [ ] 任务 4：修复 CoordinatorService 持久化 - 创建数据模型
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 创建 Team 数据模型
  - 创建 AgentDefinition 数据模型
  - 创建 TeamMember 关联模型
  - 添加 Alembic 迁移
- **Acceptance Criteria Addressed**: 核心功能模块分析 - 问题 3.3
- **Test Requirements**:
  - `programmatic` TR-4.1: Team 模型可以正常 CRUD
  - `programmatic` TR-4.2: AgentDefinition 模型可以正常 CRUD
  - `programmatic` TR-4.3: 数据库迁移可以正常执行
- **Notes**: 在 `backend/app/models/` 中创建新模型

## [ ] 任务 5：修复 CoordinatorService 持久化 - 重构服务
- **Priority**: P0
- **Depends On**: 任务 4
- **Description**:
  - 重构 CoordinatorService 使用数据库存储
  - 保持 API 接口不变
  - 添加 Redis 缓存层（可选，用于性能优化）
- **Acceptance Criteria Addressed**: 核心功能模块分析 - 问题 3.3
- **Test Requirements**:
  - `programmatic` TR-5.1: 服务重启后团队数据不丢失
  - `programmatic` TR-5.2: 所有现有 API 功能正常工作
  - `programmatic` TR-5.3: 并发操作数据一致性
- **Notes**: 修改 `backend/app/services/coordinator_service.py`

## [ ] 任务 6：优化异步处理 - 重构 async_handler
- **Priority**: P1
- **Depends On**: None
- **Description**:
  - 使用全局事件循环而非每次创建新循环
  - 优化线程池使用
  - 添加性能监控
- **Acceptance Criteria Addressed**: 技术栈选型评估 - 问题 4.1
- **Test Requirements**:
  - `programmatic` TR-6.1: 异步请求处理延迟降低
  - `programmatic` TR-6.2: 高并发下稳定性提升
  - `human-judgement` TR-6.3: 代码复杂度降低，可读性提升
- **Notes**: 修改 `backend/app/main.py` 和相关异步工具

## [ ] 任务 7：添加安全响应头
- **Priority**: P1
- **Depends On**: 任务 3
- **Description**:
  - 添加 CSP (Content Security Policy)
  - 添加 HSTS (HTTP Strict Transport Security)
  - 添加 X-Content-Type-Options, X-Frame-Options 等
- **Acceptance Criteria Addressed**: 安全隐患排查 - 问题 3
- **Test Requirements**:
  - `programmatic` TR-7.1: 响应包含所有必要的安全头
  - `programmatic` TR-7.2: 安全头配置正确有效
- **Notes**: 使用 Flask 的 after_request 或中间件

## [ ] 任务 8：引入 Redis 缓存 - 基础架构
- **Priority**: P1
- **Depends On**: None
- **Description**:
  - 创建缓存服务抽象层
  - 实现 Redis 缓存后端
  - 添加缓存装饰器
- **Acceptance Criteria Addressed**: 潜在性能瓶颈 - 问题 6.2
- **Test Requirements**:
  - `programmatic` TR-8.1: 缓存可以正常读写
  - `programmatic` TR-8.2: TTL 过期机制正常
  - `programmatic` TR-8.3: 缓存失效机制正常
- **Notes**: 在 `backend/app/core/` 中创建 cache.py

## [ ] 任务 9：引入 Redis 缓存 - Agent 列表缓存
- **Priority**: P1
- **Depends On**: 任务 8
- **Description**:
  - 缓存 Agent 列表查询
  - 缓存单个 Agent 详情
  - 在创建/更新/删除时失效缓存
- **Acceptance Criteria Addressed**: 潜在性能瓶颈 - 问题 6.2
- **Test Requirements**:
  - `programmatic` TR-9.1: 重复查询命中缓存
  - `programmatic` TR-9.2: 更新操作后缓存失效
  - `programmatic` TR-9.3: 查询延迟显著降低
- **Notes**: 修改 `backend/app/api/agents.py`

## [ ] 任务 10：添加 Prometheus 指标
- **Priority**: P1
- **Depends On**: None
- **Description**:
  - 集成 prometheus-client
  - 添加 HTTP 请求指标（计数、延迟、状态码）
  - 添加数据库查询指标
  - 添加业务指标（Agent 数、会话数等）
- **Acceptance Criteria Addressed**: 可观测性 - 问题 5
- **Test Requirements**:
  - `programmatic` TR-10.1: /metrics 端点返回 Prometheus 格式数据
  - `programmatic` TR-10.2: HTTP 请求被正确计数
  - `programmatic` TR-10.3: 指标包含正确的标签
- **Notes**: 创建新的 metrics 模块

## [ ] 任务 11：添加结构化 JSON 日志
- **Priority**: P1
- **Depends On**: None
- **Description**:
  - 配置 Python logging 使用 JSON 格式
  - 添加请求 ID 追踪
  - 包含关键元数据（时间、级别、模块、请求信息等）
- **Acceptance Criteria Addressed**: 可观测性 - 问题 5
- **Test Requirements**:
  - `programmatic` TR-11.1: 日志输出为有效的 JSON
  - `programmatic` TR-11.2: 包含所有必要字段
  - `human-judgement` TR-11.3: 日志可被 ELK/Grafana Loki 解析
- **Notes**: 使用 python-json-logger 库

## [ ] 任务 12：数据库优化 - 添加慢查询日志
- **Priority**: P1
- **Depends On**: None
- **Description**:
  - 配置 SQLAlchemy 记录慢查询
  - 设置阈值（如 > 100ms）
  - 将慢查询记录到专用日志
- **Acceptance Criteria Addressed**: 数据库优化 - 问题 6
- **Test Requirements**:
  - `programmatic` TR-12.1: 慢查询被正确记录
  - `programmatic` TR-12.2: 包含查询文本和执行时间
  - `programmatic` TR-12.3: 正常查询不被记录
- **Notes**: 修改 `backend/app/core/database.py`

## [ ] 任务 13：添加 E2E 测试 - 基础框架
- **Priority**: P2
- **Depends On**: None
- **Description**:
  - 选择 Playwright 或 Cypress
  - 配置测试环境
  - 创建测试 fixtures
- **Acceptance Criteria Addressed**: 测试覆盖 - 问题 4
- **Test Requirements**:
  - `programmatic` TR-13.1: E2E 测试框架可以正常运行
  - `programmatic` TR-13.2: 测试可以启动前端和后端
  - `programmatic` TR-13.3: 基础导航测试通过
- **Notes**: 在项目根目录创建 e2e/ 文件夹

## [ ] 任务 14：添加 E2E 测试 - Agent 管理流程
- **Priority**: P2
- **Depends On**: 任务 13
- **Description**:
  - 测试 Agent 创建流程
  - 测试 Agent 列表查看
  - 测试 Agent 编辑和删除
- **Acceptance Criteria Addressed**: 测试覆盖 - 问题 4
- **Test Requirements**:
  - `programmatic` TR-14.1: Agent CRUD 流程测试通过
  - `programmatic` TR-14.2: 权限控制正确
  - `programmatic` TR-14.3: 表单验证正常工作
- **Notes**: 覆盖关键用户流程

## [ ] 任务 15：前端优化 - 虚拟列表
- **Priority**: P2
- **Depends On**: None
- **Description**:
  - 为 Agent 列表添加虚拟滚动
  - 为会话列表添加虚拟滚动
  - 选择合适的虚拟列表库（如 react-window）
- **Acceptance Criteria Addressed**: 前端性能 - 问题 7
- **Test Requirements**:
  - `programmatic` TR-15.1: 1000+ 项列表滚动流畅
  - `programmatic` TR-15.2: 内存使用显著降低
  - `human-judgement` TR-15.3: 用户体验无明显变化
- **Notes**: 修改 `frontend/app/agents/page.tsx` 等列表页面

## [ ] 任务 16：前端优化 - 错误边界
- **Priority**: P2
- **Depends On**: None
- **Description**:
  - 创建通用错误边界组件
  - 包裹主要页面和组件
  - 添加用户友好的错误提示
- **Acceptance Criteria Addressed**: 前端性能 - 问题 7
- **Test Requirements**:
  - `programmatic` TR-16.1: 组件错误不导致整个应用崩溃
  - `programmatic` TR-16.2: 错误信息正确显示
  - `human-judgement` TR-16.3: 用户可以从错误中恢复
- **Notes**: 在 `frontend/` 中创建 ErrorBoundary 组件

## [ ] 任务 17：修复迁移目录拼写
- **Priority**: P2
- **Depends On**: None
- **Description**:
  - 将 `alembir/` 重命名为 `alembic/`
  - 更新 alembic.ini 配置
  - 测试迁移仍然正常工作
- **Acceptance Criteria Addressed**: 技术栈 - 小问题
- **Test Requirements**:
  - `programmatic` TR-17.1: 目录名称正确
  - `programmatic` TR-17.2: `alembic upgrade head` 正常工作
  - `programmatic` TR-17.3: `alembic downgrade` 正常工作
- **Notes**: 注意 git 历史处理

## [ ] 任务 18：完善 API 文档 - Swagger/OpenAPI
- **Priority**: P2
- **Depends On**: None
- **Description**:
  - 集成 Flask-RESTX 或 flasgger
  - 为所有 API 端点添加文档
  - 添加请求/响应 schema
- **Acceptance Criteria Addressed**: 文档完善 - 问题 8
- **Test Requirements**:
  - `programmatic` TR-18.1: /docs 端点可访问
  - `programmatic` TR-18.2: 所有 API 端点都有文档
  - `human-judgement` TR-18.3: 文档清晰易用
- **Notes**: 可以考虑 FastAPI 迁移（长期）

## [ ] 任务 19：依赖安全审计 - 工具配置
- **Priority**: P2
- **Depends On**: None
- **Description**:
  - 配置 pip-audit 用于后端
  - 配置 npm audit 用于前端
  - 添加到 CI 流程
- **Acceptance Criteria Addressed**: 依赖安全 - 问题 7.3
- **Test Requirements**:
  - `programmatic` TR-19.1: pip-audit 可以正常运行
  - `programmatic` TR-19.2: npm audit 可以正常运行
  - `programmatic` TR-19.3: 发现的漏洞被正确报告
- **Notes**: 在 package.json 和 requirements.txt 中添加脚本

## [ ] 任务 20：锁定依赖版本
- **Priority**: P2
- **Depends On**: 任务 19
- **Description**:
  - 将 requirements.txt 中的 >= 改为 == 或 ~=
  - 使用 pip freeze 生成准确的版本锁定
  - 前端同样锁定 package.json 版本
- **Acceptance Criteria Addressed**: 依赖安全 - 问题 7.3
- **Test Requirements**:
  - `programmatic` TR-20.1: 所有依赖都有确切版本
  - `programmatic` TR-20.2: 依赖安装可复现
  - `programmatic` TR-20.3: 应用仍然正常工作
- **Notes**: 使用 pip-tools 或 poetry 更好管理

---

## 实施阶段总结

### 阶段 1：安全与稳定性（P0 任务）
- 任务 1-3: 安全加固
- 任务 4-5: CoordinatorService 持久化

### 阶段 2：性能优化（P1 任务）
- 任务 6: 异步处理优化
- 任务 7: 安全头
- 任务 8-9: Redis 缓存
- 任务 10-11: 监控与日志
- 任务 12: 数据库优化

### 阶段 3：体验与完善（P2 任务）
- 任务 13-14: E2E 测试
- 任务 15-16: 前端优化
- 任务 17-20: 杂项改进
