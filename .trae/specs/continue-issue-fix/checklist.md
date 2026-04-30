# Checklist — 第二轮深度问题修复

## 阶段一：Critical 安全与稳定性修复

- [x] C-01: /api/v1/auth/login 在非开发环境验证密码，密码错误返回 401
- [x] C-02: 前端登录页有密码输入字段
- [x] C-03: async_utils.get_db() 不再每次创建新引擎，复用 database.py 单例
- [x] C-04: 高并发调用 get_db() 不产生多余数据库引擎
- [x] C-05: alembic upgrade head 创建所有 14 张表（含 skills、teams、team_members、mcp_servers、memory_facts）
- [x] C-06: Flask 抛出 NotFoundError 返回 404 JSON（而非 500 HTML）
- [x] C-07: Flask 抛出 ValidationError 返回 422 JSON
- [x] C-08: channels.py 中 ValueError 已替换为 ValidationError

## 阶段二：High 级别安全修复

- [x] C-09: PUT /permissions/modes/<mode_id> 需要 admin 角色
- [x] C-10: POST /permissions/denials/clear 需要 admin 角色
- [x] C-11: WebSocket 连接需要有效 JWT Token，无 Token 连接被拒绝
- [x] C-12: SocketIO cors_allowed_origins 不再为 '*'，使用 Settings 配置
- [x] C-13: 审计导出使用 fetch + Authorization header，非 window.open()

## 阶段三：High 级别 Bug 修复

- [x] C-14: coordinator update_team 正确更新 name/description 字段（无 _ 后缀）
- [x] C-15: memory fact 创建去重检查和写入在同一事务中
- [x] C-16: Team.to_dict() 正确返回 member_count
- [x] C-17: tools.py test_tool() 工具不存在时返回 404 而非 500
- [x] C-18: ToolResult completed_at 无默认值，与 started_at 不同
- [x] C-19: audit stats 使用标准 SQLAlchemy 语法
- [x] C-20: Chat 页面流式完成后 usage 为最新值
- [x] C-21: Chat 页面 tool_end 不污染 ToolUse 对象
- [x] C-22: Chat 页面流式错误时用户消息不丢失
- [x] C-23: Chat 页面支持多工具调用（activeToolCalls 数组）
- [x] C-24: useApi hook 不因 options 引用变化触发无限重渲染

## 阶段四：部署配置修复

- [x] C-25: 后端 Docker 容器以非 root 用户运行
- [x] C-26: docker-compose backend 有健康检查配置
- [x] C-27: docker-compose 后端不使用 --reload（或有 prod 配置）
- [x] C-28: .env.example DATABASE_URL 端口与 docker-compose 一致（5433）
- [x] C-29: .env.example REDIS_URL 端口与 docker-compose 一致（6380）
- [x] C-30: backend/.dockerignore 存在且排除 venv、__pycache__、*.db 等
- [x] C-31: next.config.js 后端地址使用环境变量
- [x] C-32: next.config.js 配置安全响应头
- [x] C-33: api.ts 无 console.log 调试日志

## 阶段五：前端体验和代码质量

- [x] C-34: 操作失败时页面显示错误通知
- [x] C-35: Settings 权限模式切换失败时回滚
- [x] C-36: Tasks 页面使用函数式 setState
- [x] C-37: 无无效的 memoizedMessages
- [x] C-38: 无未使用的导入
- [x] C-39: 共享接口定义在 lib/types.ts
- [x] C-40: NavLink active 状态随路由动态变化
- [x] C-41: 列表页过滤计算使用 useMemo

## 阶段六：测试和 CI 修复

- [x] C-42: test_coordinator_api.py 无 `in (200, 500)` 宽松断言
- [x] C-43: test_integration.py 无宽松断言
- [x] C-44: sample_task fixture 正确引用 sample_session
- [x] C-45: CI pip install 不忽略错误
- [x] C-46: CI 前端测试失败阻塞流水线
