# Tasks — 第二轮深度问题修复

## 阶段一：Critical 安全与稳定性修复

- [x] Task 1: 登录接口添加密码验证
  - [x] 1.1: 在 auth.py 中添加密码验证逻辑，当 APP_ENV != 'development' 时验证密码哈希
  - [x] 1.2: 在 User 模型或 auth 模块中添加密码哈希验证函数
  - [x] 1.3: 前端 login/page.tsx 添加密码输入字段
  - [x] 1.4: 移除前端"输入任意用户名即可登录"提示，区分开发/生产模式

- [x] Task 2: 修复 async_utils.get_db() 连接池泄漏
  - [x] 2.1: 修改 async_utils.get_db() 复用 database.py 的引擎单例
  - [x] 2.2: 删除 async_utils 中 _create_session_factory() 的独立引擎创建逻辑
  - [x] 2.3: 确保 run_async() 使用统一的会话工厂
  - [x] 2.4: 验证高并发下不再创建多余引擎

- [x] Task 3: 补全缺失的数据库迁移脚本
  - [x] 3.1: 创建 002_add_skills_teams_mcp_memory.py 迁移脚本
  - [x] 3.2: 包含 skills、teams、team_members、mcp_servers、memory_facts 五张表
  - [x] 3.3: 验证 `alembic upgrade head` 在新数据库中创建所有表

- [x] Task 4: 注册 Flask 全局错误处理器
  - [x] 4.1: 在 main.py 中注册 @app.errorhandler(OCHError) 及其子类
  - [x] 4.2: NotFoundError → 404 JSON，ValidationError → 422 JSON，OCHError → 400 JSON
  - [x] 4.3: 统一 channels.py 中的 ValueError 为 ValidationError

## 阶段二：High 级别安全修复

- [x] Task 5: 权限端点访问控制加固
  - [x] 5.1: permissions.py PUT /permissions/modes/<mode_id> 改为 @require_role('admin')
  - [x] 5.2: permissions.py POST /permissions/denials/clear 改为 @require_role('admin')

- [x] Task 6: WebSocket 连接认证
  - [x] 6.1: 在 websocket.py handle_connect() 中验证 JWT Token
  - [x] 6.2: 从 query 参数或 header 中获取 Token
  - [x] 6.3: 未认证连接返回 disconnect

- [x] Task 7: SocketIO CORS 白名单
  - [x] 7.1: 修改 main.py 中 SocketIO 的 cors_allowed_origins 从 '*' 改为读取 Settings.CORS_ORIGINS
  - [x] 7.2: 确保 WebSocket 和 REST API 的 CORS 策略一致

- [x] Task 8: 前端审计导出认证修复
  - [x] 8.1: 修改 audit/page.tsx 的导出功能，使用 fetch + Authorization header 下载
  - [x] 8.2: 创建 Blob URL 触发下载，而非 window.open()

## 阶段三：High 级别 Bug 修复

- [x] Task 9: 修复后端多个 Bug
  - [x] 9.1: coordinator.py update_team 删除错误的 `field + '_'` 后缀逻辑
  - [x] 9.2: memory.py 将去重检查和写入合并到同一数据库事务
  - [x] 9.3: team.py to_dict() 修复 `self._members` 为 `self.members`
  - [x] 9.4: tools.py test_tool() 添加 _find_tool 返回 None 检查
  - [x] 9.5: message.py ToolResult 的 completed_at 移除默认值
  - [x] 9.6: audit.py 修复 stats 中的 lambda 语法为标准 SQLAlchemy 用法

- [x] Task 10: 修复前端 Chat 页面多个 Bug
  - [x] 10.1: usage 状态改用 useRef 追踪，流式完成后从 ref 读取
  - [x] 10.2: tool_end 事件只提取 ToolUse 相关字段，不展开整个 event
  - [x] 10.3: 流式错误时确保用户消息被添加到消息列表
  - [x] 10.4: activeToolCall 改为 activeToolCalls 数组，支持多工具调用

- [x] Task 11: 修复 useApi hook 无限循环风险
  - [x] 11.1: 使用 JSON.stringify 稳定化 options 依赖
  - [x] 11.2: 验证 settings 页面不再触发无限重渲染

## 阶段四：部署配置修复

- [x] Task 12: Docker 和部署配置修复
  - [x] 12.1: backend/Dockerfile 添加非 root 用户
  - [x] 12.2: docker-compose.yml 为 backend 添加健康检查
  - [x] 12.3: docker-compose.yml 移除 --reload 参数（或创建 prod 配置）
  - [x] 12.4: .env.example 修正 DATABASE_URL 端口为 5433、REDIS_URL 端口为 6380
  - [x] 12.5: 创建 backend/.dockerignore 排除 venv、__pycache__、*.db 等

- [x] Task 13: 前端部署和安全配置
  - [x] 13.1: next.config.js 后端地址改用环境变量 BACKEND_URL
  - [x] 13.2: next.config.js 添加安全响应头（X-Frame-Options、X-Content-Type-Options 等）
  - [x] 13.3: 清理 api.ts 中的 console.log 调试日志

## 阶段五：前端体验和代码质量

- [x] Task 14: 前端操作反馈和体验改进
  - [x] 14.1: 在 appStore 中实现 addNotification 机制，各页面操作失败时显示错误通知
  - [x] 14.2: Settings 页面权限模式切换失败时回滚到之前值
  - [x] 14.3: Tasks 页面乐观更新改用函数式 setState
  - [x] 14.4: 删除无效的 memoizedMessages，直接使用 messages

- [x] Task 15: 前端代码质量清理
  - [x] 15.1: 删除未使用的导入（agents/STATUS_LABELS、skills/formatDate 等）
  - [x] 15.2: 提取共享接口定义到 lib/types.ts（AuditLog 等）
  - [x] 15.3: NavLink active 状态改用 usePathname() 动态判断
  - [x] 15.4: Sessions/Tasks/Audit 页面过滤计算添加 useMemo

## 阶段六：测试和 CI 修复

- [x] Task 16: 测试质量修复
  - [x] 16.1: 修复 test_coordinator_api.py 中 16 处 `in (200, 500)` 宽松断言
  - [x] 16.2: 修复 test_integration.py 中 5 处类似宽松断言
  - [x] 16.3: 修复 conftest.py sample_task fixture 的 sample_session 引用

- [x] Task 17: CI 配置修复
  - [x] 17.1: 移除 CI 中 pip install 的 `2>/dev/null || true`
  - [x] 17.2: 移除前端测试步骤的 continue-on-error: true
  - [x] 17.3: 集成测试修复后移除 continue-on-error: true

# Task Dependencies
- Task 2 → Task 9（数据库会话修复后再修 Bug）
- Task 4 → Task 9（错误处理器注册后统一异常处理）
- Task 1 和 Task 5 可并行（独立安全修复）
- Task 6 和 Task 7 可并行（独立安全修复）
- Task 10 和 Task 11 可并行（独立前端修复）
- Task 12 和 Task 13 可并行（独立部署修复）
- Task 14 依赖 Task 11（useApi 修复后再做通知机制）
- Task 16 独立于其他任务
