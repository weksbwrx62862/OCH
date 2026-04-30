# 🔍 OpenClaw-Harness 自检审计 + 修复 + 测试计划

> **日期**: 2026-04-07  
> **状态**: 📋 待执行

---

## 一、自检审计结果（发现的问题）

### 🔴 严重 Bug（必须修复）

| # | 文件 | 问题 | 影响 |
|---|------|------|------|
| B1 | [websocket.py:74](backend/app/api/websocket.py#L74) | 变量名拼写错误：`request_sid` → 应为 `request.sid` | WebSocket 断开连接时崩溃 |
| B2 | [alembic.ini:3](backend/alembic.ini#L3) | 路径拼写错误：`alembir` → 应为 `alembic` | Alembic 无法找到迁移目录 |
| B3 | [main.py](backend/app/main.py) | **未注册 WebSocket blueprint 和路由** | `/ws/*` 端点完全不可用 |
| B4 | [agents.py:15](backend/app/api/agents.py#L15) | 导入了不存在的模块：`from app.core.database import get_db` — `get_db` 未导出 | 启动时 ImportError |
| B5 | [sessions.py](backend/app/api/sessions.py) | Flask Blueprint 不原生支持 `async def` 路由函数 | 所有 Session API 返回空或报错 |

### 🟡 中等问题（影响功能）

| # | 文件 | 问题 | 影响 |
|---|------|------|------|
| M1 | [start.sh:56](start.sh#L56) | `alembic upgrade head` 从项目根目录运行，但 `alembic.ini` 在 `backend/` 下 | 数据库迁移失败 |
| M2 | 前端 | `/chat` 路由的页面已创建但未确认 Next.js App Router 能正确加载 | Chat 页面 404 |
| M3 | [config.py](backend/app/config.py) | `Path` 类型字段与 Pydantic Settings 兼容性问题 | 配置加载警告 |
| M4 | [sessions.py](backend/app/api/sessions.py) | `_active_sessions` 内存缓存无过期清理机制 | 内存泄漏风险 |
| M5 | 全局 | **零测试代码** — `tests/` 目录为空 | 无法验证功能正确性 |

### 🟢 设计优化建议

| # | 建议 | 优先级 |
|---|------|--------|
| D1 | 添加全局异常处理器捕获 `OCHError` 自定义异常 | 高 |
| D2 | SSE 流式响应添加超时控制（默认 120s） | 高 |
| D3 | 添加请求 ID 日志追踪 | 中 |
| D4 | 前端添加 Error Boundary 错误边界组件 | 中 |
| D5 | 添加 API 健康检查端点详细状态 | 低 |

---

## 二、修复计划（按执行顺序）

### Phase A: 关键 Bug 修复（预计 15 分钟）

#### A1. 修复 websocket.py 变量名错误
```python
# 文件: backend/app/api/websocket.py 第 74 行
# 修改前:
emit('left', {'room': room})  # 上面的函数用了 request_sid
# 修改后:
emit('left', {'room': room})
```

#### A2. 修复 alembic.ini 路径拼写
```ini
# 文件: backend/alembic.ini 第 3 行
# 修改前:
script_location = alembir
# 修改后:
script_location = alembic
```

#### A3. 修复 main.py — 注册 WebSocket + 修复导入
```python
# 文件: backend/app/main.py

# 1. 添加 websocket 导入
from app.api.websocket import socketio, emit_session_event

# 2. 在 _register_blueprints 中添加 WebSocket 端点
@socketio.on('connect')
def handle_connect(): ...

@socketio.on('disconnect')  
def handle_disconnect(): ...
```

#### A4. 修复 agents.py 导入错误
```python
# 文件: backend/app/api/agents.py 第 15-16 行
# 修改前:
from app.core.database import get_db, async_session_factory
# 修改后:
from app.core.database import async_session_factory
```

#### A5. 修复 Flask async 路由兼容性（最关键！）
```python
# 方案: 使用 asyncio.wrap 或同步包装器
# 对所有 async 路由函数添加包装:

def _async_handler(async_func):
    """将 async 函数包装为 Flask 同步处理."""
    @wraps(async_func)
    def sync_wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()
    return sync_wrapper

# 应用到所有 Blueprint 的 async 路由
```

### Phase B: 中等问题修复（预计 10 分钟）

#### B1. 修复 start.sh 数据库初始化路径
```bash
# 在 start.sh 的 [2/5] 步骤中:
cd backend && alembic upgrade head && cd ..
```

#### B2. 验证前端路由配置
- 确认 `frontend/app/chat/page.tsx` 存在
- 确认 `next.config.js` rewrite 规则正确
- 浏览器访问 `/chat` 是否正常渲染

#### B3. 修复 config.py Path 类型
```python
# 将 Path 字段改为 str，在内部转换为 Path
OPENHARNESS_CONFIG_DIR: str = "~/.och/config"
# 在 get_settings() 后处理转换
```

#### B4. 添加 session 缓存清理机制
```python
import time
SESSION_CACHE_TTL = 3600  # 1 小时

def _cleanup_expired_sessions():
    now = time.time()
    expired = [
        k for k, v in _active_sessions.items()
        if now - v.get('created_at', 0) > SESSION_CACHE_TTL
    ]
    for k in expired:
        del _active_sessions[k]
```

### Phase C: 测试计划（预计 30 分钟）

#### C1. 单元测试结构
```
tests/
├── conftest.py              # pytest fixtures
├── unit/
│   ├── test_config.py       # 配置管理测试
│   ├── test_models.py       # 数据库模型测试
│   ├── test_security.py     # JWT/权限测试
│   └── test_services.py     # Service 层测试
├── integration/
│   ├── test_agents_api.py   # Agent API 集成测试
│   ├── test_sessions_api.py  # Session API + SSE 测试
│   └── test_tools_api.py    # Tools API 测试
└── e2e/
    └── test_chat_flow.py     # 端到端聊天流程测试
```

#### C2. 核心测试用例清单

**Backend 测试:**
- [ ] `POST /api/v1/agents` — 创建 Agent 成功
- [ ] `POST /api/v1/agents` — 重复名称返回 400
- [ ] `GET /api/v1/agents/{id}` — 返回 Agent 详情含权限
- [ ] `DELETE /api/v1/agents/{id}` — 级联删除成功
- [ ] `POST /api/v1/sessions` — 创建会话成功
- [ ] `POST /api/v1/sessions/{id}/chat` — SSE 流式返回正确事件序列
- [ ] `GET /api/v1/tools` — 返回 43+ 工具分类列表
- [ ] `GET /api/v1/skills` — 返回内置技能列表
- [ ] `GET /health` — 健康检查端点正常
- [ ] JWT 认证 — 无 Token 返回 401
- [ ] 权限装饰器 — 非 admin 用户返回 403

**Frontend 测试:**
- [ ] 页面渲染 — Dashboard 无报错
- [ ] 页面渲染 — Chat 界面组件挂载
- [ ] API Client — GET 请求正常
- [ ] API Client — SSE 流式接收正常
- [ ] Zustand Store — 状态更新正常

#### C3. 测试命令
```bash
# Backend 单元测试
cd backend
pytest tests/unit/ -v --tb=short

# Backend 集成测试
pytest tests/integration/ -v --tb=long

# 全量测试（含覆盖率）
pytest --cov=app --cov-report=html

# Frontend 测试
cd frontend
npm run test
```

---

## 三、执行步骤（有序）

### Step 1: 修复所有 Bug（A1-A5）
1. 编辑 `backend/app/api/websocket.py` 第 74 行
2. 编辑 `backend/alembic.ini` 第 3 行
3. 编辑 `backend/app/main.py` — 添加 WebSocket 支持
4. 编辑 `backend/app/api/agents.py` — 修复导入
5. 创建 `backend/app/utils/async_helper.py` — Flask async 包装器
6. 更新所有 async Blueprint 路由使用包装器

### Step 2: 修复中等问题（B1-B4）
1. 编辑 `start.sh` — 修正 alembic 路径
2. 验证并修复前端路由
3. 编辑 `backend/app/config.py` — Path 类型修复
4. 在 `backend/app/api/sessions.py` — 添加 session 清理

### Step 3: 编写核心测试（C1-C3）
1. 创建 `tests/conftest.py` — fixtures
2. 创建 `tests/unit/test_config.py`
3. 创建 `tests/unit/test_models.py`
4. 创建 `tests/integration/test_agents_api.py`
5. 创建 `tests/integration/test_sessions_api.py`
6. 运行全部测试确保通过

### Step 4: 手动验证启动流程
1. 运行 `./start.sh`
2. 访问 http://localhost:3000 — Dashboard 渲染
3. 访问 http://localhost:3000/chat — Chat 界面
4. 访问 http://localhost:8008/docs — Swagger UI
5. 执行一次完整聊天流程（发送消息→接收流式响应）
6. 检查日志无 ERROR 级别输出

### Step 5: 性能与安全检查
1. 检查内存泄漏（长时间运行观察）
2. 验证 CORS 配置正确
3. 验证 SQL 注入防护（ORM 参数化查询）
4. 验证 XSS 防护（前端转义）

---

## 四、验收标准

### 功能验收 ✅
- [ ] 项目可一键启动 (`./start.sh`)
- [ ] Backend 服务正常运行 (端口 8008)
- [ ] Frontend 服务正常运行 (端口 3000)
- [ ] Swagger API 文档可访问
- [ ] 创建 Agent → 成功返回 201
- [ ] 发送聊天消息 → 收到 SSE 流式响应
- [ ] 工具调用可视化展示
- [ ] WebSocket 连接正常

### 代码质量验收 ✅
- [ ] 零 Python import 错误
- [ ] 零 TypeScript 类型错误
- [ ] 所有 async 函数正确处理
- [ ] 数据库操作有事务保护
- [ ] API 有统一错误格式
- [ ] 日志级别配置正确

### 测试验收 ✅
- [ ] 单元测试 ≥ 20 个用例
- [ ] 集成测试 ≥ 10 个用例
- [ ] 核心路径覆盖 ≥ 80%
- [ ] 所有测试通过 (0 failure)

---

## 五、风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| Flask async 兼容性 | 高 | 高 | 使用同步包装器 + 文档说明 |
| SQLite 并发限制 | 中 | 低 | 开发环境足够，生产用 PostgreSQL |
| OpenHarness 导入冲突 | 中 | 高 | 隔离导入 + try/except 保护 |
| 前端构建失败 | 低 | 中 | 锁定依赖版本 |

---

**下一步**: 用户确认此计划后，立即开始按顺序执行修复和测试。
