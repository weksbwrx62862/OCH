# Checklist — 部署问题修复

## 阶段 1: 核心问题修复

- [x] `run_async()` 修复后连续 10 次请求 `/api/v1/agents` 全部返回 200
- [x] 所有 API 端点（sessions/skills/coordinator/mcp/audit）不再返回 500 事件循环错误
- [x] 未认证请求 `/api/v1/nonexistent` 返回 404（非 401）

## 阶段 2: 配置与依赖修复

- [x] `flasgger>=0.9.7` 已添加到 requirements.txt
- [x] `.env.example` 中 CORS_ORIGINS 为 JSON 数组格式
- [x] `.env.example` 中 ALLOWED_HOSTS 为 JSON 数组格式
- [x] 从 `.env.example` 复制为 `.env` 后应用可正常启动
- [x] `alembir/` 目录已删除，迁移文件在 `alembic/versions/` 中
- [x] `alembic/env.py` 从环境变量读取 DATABASE_URL
- [x] `alembic upgrade head` 成功执行迁移

## 阶段 3: Docker 部署修复

- [x] `frontend/Dockerfile` 存在且可构建
- [x] `docker-compose.yml` 端口映射不与本地服务冲突

## 阶段 4: 全面测试验证

- [ ] `pytest tests/` 全部通过（0 failed, 0 error）— 93/100 通过，7 个失败为测试隔离问题
- [x] 所有 12 个 API 模块端点返回有效响应（无 500）
- [x] 未认证请求返回 401 + JSON 错误体
- [x] 不存在路径返回 404 + JSON 错误体
- [x] 无效 Token 返回 401 + JSON 错误体
- [x] 缺少必填字段返回 422 + JSON 错误体
- [x] 所有 9 个前端页面返回 200
- [x] 前端到后端 API 连通性正常
