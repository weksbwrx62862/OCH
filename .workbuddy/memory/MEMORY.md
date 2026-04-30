# MEMORY.md — OpenClaw-Harness 项目长期记忆

## 项目概况
- **名称**: OpenClaw-Harness (OCH) — 基于 OpenHarness 核心架构的多智能体协作平台
- **技术栈**: Flask 3.0 + SQLAlchemy 2.0 async + Next.js 14 + Socket.IO + Zustand
- **架构**: API(Blueprint) → Service → Model(SQLAlchemy) 三层分离，15 个领域 Blueprint
- **版本**: 0.1.0（早期阶段）

## 技术债修复记录（2026-04-10）
1. **P0 异步架构缺陷** ✅ 已修复：`async_utils.py` 改为模块级单例引擎 + 连接池，`get_db()` 只创建 session，不创建引擎
2. **P0 认证三重重复** ✅ 已修复：统一到 AuthMiddleware 入口，`init_security()` 不再注册 before_request，AuthMiddleware 直接写 `g.user`
3. **P0 信息泄露** ✅ 已修复：通用 Exception handler 生产环境只返回 "Internal server error"，开发环境保留详情
4. **P1 datetime.utcnow()** ✅ 已修复：25 个文件 65 处替换为 `datetime.now(timezone.utc)`
5. **P1 前端大文件** ✅ 已修复：chat/page.tsx 拆分为 types.ts + MessageBubble.tsx + MemorySidebar.tsx + ChatInput.tsx
6. **P1 CoordinatorService** ✅ 已修复：从纯内存字典改为数据库持久化（Team/TeamMember 模型）

## 项目亮点
- 配置管理优秀：pydantic-settings + 密钥验证器（非开发环境拒绝默认密钥）
- 错误处理体系完善：OCHError 层次结构清晰
- Swagger API 文档注解全面
- 中间件管道设计优雅（参考 DeerFlow 模式）

## 前后端一致性修复记录（2026-04-10）
1. **P0 StreamChat 绕过 BFF** ✅ 已修复：`api.ts` 的 `streamChat()` 改用 `/api/proxy/chat?sessionId=` BFF 代理，而非直连 `http://host:8008/...`
2. **P0 审计导出无认证** ✅ 已修复：`audit/page.tsx` 导出改为 `fetch()` + Blob 下载（携带 Bearer token），替代 `window.open()`
3. **P1 Chat Agent 创建 403** ✅ 已修复：后端新增 `POST /agents/quick-create`（仅需 `@require_auth`），前端 chat 页改用此端点
4. **P1 登录页缺密码** ✅ 已修复：`login/page.tsx` 添加 password 字段和输入框，请求体包含 `{ username, password }`
5. **P2 MCP 管理权限不匹配** ✅ 已修复：`settings/page.tsx` 添加 isAdmin 检查，非 admin 隐藏添加/移除 MCP 服务器按钮

## 用户偏好
- 中文沟通
