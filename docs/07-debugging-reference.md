# 各模块独立调试命令速查

## 1. 后端模块

| 模块 | 调试命令 |
|------|---------|
| 配置 | `python3 -c "from app.config import get_settings; print(get_settings().model_dump())"` |
| 数据库 | `python3 -c "import asyncio; from app.core.database import init_db; asyncio.run(init_db())"` |
| 安全 | `python3 -c "from app.core.security import create_jwt, verify_token; t=create_jwt({'sub':'test','username':'test','role':'admin'}); print(verify_token(t))"` |
| 异步工具 | `python3 -c "from app.core.async_utils import run_async; print(run_async(asyncio.sleep(0.1)))"` |
| 认证 API | `curl -X POST http://localhost:8008/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"admin"}'` |
| 健康检查 | `curl http://localhost:8008/health` |
| 中间件 | `curl http://localhost:8008/api/v1/middleware` |
| Swagger | `curl http://localhost:8008/apispec.json` |

### 1.1 应用入口 `main.py`

```bash
cd /home/xxh/openclaw-harness/backend
source .venv/bin/activate 2>/dev/null || python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=/home/xxh/openclaw-harness/backend
python -m app.main
```

### 1.2 配置管理 `config.py`

```bash
cd /home/xxh/openclaw-harness/backend
python3 -c "from app.config import get_settings; s = get_settings(); print(f'DB={s.DATABASE_URL}'); print(f'Redis={s.REDIS_URL}'); print(f'Env={s.APP_ENV}')"
```

### 1.3 数据库层 `core/database.py`

```bash
cd /home/xxh/openclaw-harness/backend
python3 -c "
import asyncio
from app.core.database import init_db, get_engine
asyncio.run(init_db())
print('DB init OK')
print(f'Engine: {get_engine().url}')
"
```

### 1.4 安全层 `core/security.py`

```bash
cd /home/xxh/openclaw-harness/backend
python3 -c "
from app.core.security import create_jwt, verify_token, hash_password, verify_password
token = create_jwt({'sub': 'test', 'username': 'test', 'role': 'admin'})
print(f'Token: {token[:50]}...')
payload = verify_token(token)
print(f'Verified: {payload}')
hashed = hash_password('test123')
print(f'Verify: {verify_password(\"test123\", hashed)}')
"
```

### 1.5 中间件 `middleware/__init__.py`

```bash
# 启动后端后访问中间件信息端点
curl http://localhost:8008/api/v1/middleware
```

### 1.6 认证 API `api/auth.py`

```bash
# 登录
curl -X POST http://localhost:8008/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": ""}'

# 验证
curl http://localhost:8008/api/v1/auth/verify \
  -H "Authorization: Bearer <token>"
```

### 1.7 会话与聊天 API `api/sessions.py`

```bash
# 先获取 token
TOKEN=$(curl -s -X POST http://localhost:8008/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 创建会话
curl -X POST http://localhost:8008/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "测试会话"}'

# 列出会话
curl http://localhost:8008/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN"
```

### 1.8 OpenHarness 核心引擎

```bash
cd /home/xxh/openclaw-harness/backend
python3 -c "
from openharness.engine.query_engine import QueryEngine
from openharness.tools import create_default_tool_registry
print('QueryEngine imported OK')
tools = create_default_tool_registry()
print(f'Tools: {len(tools)} registered')
"
```

## 2. 前端模块

| 模块 | 调试命令 |
|------|---------|
| 类型检查 | `npx tsc --noEmit` |
| 构建 | `npm run build` |
| 测试 | `npm test` |
| Lint | `npm run lint` |

### 2.1 依赖安装与启动

```bash
cd /home/xxh/openclaw-harness/frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

### 2.2 API 客户端 `lib/api.ts`

```bash
# 检查 API 连通性
cd /home/xxh/openclaw-harness/frontend
curl http://localhost:3000/api/v1/health  # 应代理到后端
```

### 2.3 类型定义 `lib/types.ts`

```bash
cd /home/xxh/openclaw-harness/frontend
npx tsc --noEmit
```

### 2.4 认证流程 `AuthProvider.tsx`

调试步骤：
1. 访问 `http://localhost:3000` — 应重定向到 `/login`
2. 输入任意用户名（开发模式）登录
3. 检查 `localStorage` 中 `och_token` 是否存在

## 3. Docker 环境

| 操作 | 命令 |
|------|------|
| 启动全部 | `docker compose up -d` |
| 查看日志 | `docker compose logs -f backend` |
| 重启后端 | `docker compose restart backend` |
| 进入容器 | `docker compose exec backend bash` |
| 清理重建 | `docker compose down -v && docker compose up --build -d` |

### 3.1 Docker Compose 调试步骤

```bash
cd /home/xxh/openclaw-harness
docker compose up -d postgres redis  # 先启动数据库
docker compose up backend            # 再启动后端
docker compose up frontend           # 最后启动前端
```

## 4. 模块间集成调试

### 4.1 前后端认证联调

```bash
# 1. 启动后端
cd /home/xxh/openclaw-harness/backend && python -m app.main

# 2. 启动前端
cd /home/xxh/openclaw-harness/frontend && npm run dev

# 3. 访问 http://localhost:3000/login 登录
# 4. 打开浏览器 DevTools Network 查看 API 请求
```

### 4.2 聊天流程联调

```bash
# 1. 登录获取 token
TOKEN=$(curl -s -X POST http://localhost:8008/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Quick-create Agent
AGENT_ID=$(curl -s -X POST http://localhost:8008/api/v1/agents/quick-create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-agent"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent',d).get('id',''))")

# 3. 创建 Session
SESSION_ID=$(curl -s -X POST http://localhost:8008/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"test\", \"agent_id\": \"$AGENT_ID\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")

# 4. 发送聊天 (SSE)
curl -N -X POST "http://localhost:8008/api/v1/sessions/$SESSION_ID/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "stream": true}'
```

## 5. WebSocket 调试

**调试步骤**（JavaScript）：

```javascript
// 浏览器控制台
const socket = io('http://localhost:8008', {
  auth: { token: 'your-jwt-token' }
});
socket.on('connected', (data) => console.log('Connected:', data));
socket.emit('join_session', { session_id: 'your-session-id' });
```

**问题**：前端已安装 `socket.io-client` 依赖（`package.json` 中版本 `^4.7.0`），但前端源代码中未实际使用该依赖，WebSocket 客户端功能尚未实现。

**调整建议**：

在前端源代码中创建 WebSocket 连接管理模块，引入已安装的 `socket.io-client` 依赖：

```typescript
// lib/websocket.ts
import { io, Socket } from 'socket.io-client';

export function createSocket(token: string): Socket {
  return io({
    auth: { token },
  });
}
```
