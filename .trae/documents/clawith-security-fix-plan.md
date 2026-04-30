# Clawith 项目安全与代码质量修复计划

> 基于全面代码审计发现的 18 个问题，按优先级分阶段实施

---

## 阶段一：紧急安全修复（P0 - 立即执行）

### 1.1 更换所有默认密钥

**涉及文件**: `.env`, `backend/app/config.py`

**问题描述**: 生产环境使用 `change-me-in-production` 和 `change-me-jwt-secret` 作为密钥

**修复步骤**:
1. 使用 `python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"` 生成强随机 SECRET_KEY
2. 使用同样方式生成 JWT_SECRET_KEY（至少 256 位）
3. 更新 `.env` 文件中的两个值
4. 修改 `config.py` 中默认值为空字符串，启动时检查是否为空并报错退出
5. 重启所有服务使新密钥生效

**验证方法**:
- 启动应用确认无报错
- 使用旧 Token 访问 API 应返回 401

```python
# config.py 修改示例
class Settings(BaseSettings):
    SECRET_KEY: str = ""  # 改为空字符串
    JWT_SECRET_KEY: str = ""  # 改为空字符串
    
    # ... 其他配置 ...

# 在 get_settings() 或 lifespan 中添加校验
def validate_settings(settings: Settings) -> None:
    if settings.SECRET_KEY in ("", "change-me-in-production"):
        raise RuntimeError("SECRET_KEY 必须设置为强随机值")
    if settings.JWT_SECRET_KEY in ("", "change-me-jwt-secret"):
        raise RuntimeError("JWT_SECRET_KEY 必须设置为强随机值")
```

---

### 1.2 数据库凭据加固

**涉及文件**: `.env`

**修复步骤**:
1. 生成强数据库密码（16+ 字符，包含大小写字母、数字、特殊字符）
2. 更新 `DATABASE_URL` 中的密码部分
3. 移除 `?ssl=disable` 或改为 `?ssl=require`
4. 如使用 PostgreSQL，确保 pg_hba.conf 配置正确

**验证方法**:
- 应用能正常连接数据库
- 检查连接是否使用 SSL（查看 PostgreSQL 日志）

---

### 1.3 修复 XSS 漏洞

**涉及文件**: `frontend/src/components/MarkdownRenderer.tsx`

**修复步骤**:
1. 安装 DOMPurify: `npm install dompurify @types/dompurify`
2. 导入并在渲染前清理 HTML
3. 添加白名单允许 target 属性
4. 对 URL 进行协议验证（仅允许 http/https/data）

```typescript
// MarkdownRenderer.tsx 修改方案
import DOMPurify from 'dompurify';

// 在 markdownToHtml 函数末尾添加
html = DOMPurify.sanitize(html, {
    ADD_TAGS: ['img'],
    ADD_ATTR: ['target', 'rel'],
});

// 图片链接处理中增加协议校验
if (finalUrl.startsWith('/api/agents/')) {
    // ... token 处理逻辑 ...
} else {
    // 仅允许安全协议
    if (!/^https?:\/\//i.test(finalUrl) && !finalUrl.startsWith('/') && !finalUrl.startsWith('data:')) {
        finalPath = '#'; // 不安全的URL替换为占位符
    }
}
```

**验证方法**:
- 构造包含 `<script>alert(1)</script>` 的消息发送，确认不执行
- 构造包含 `javascript:` 协议的链接，确认被过滤
- 正常图片和链接仍可正常显示

---

### 1.4 修复 Token URL 泄露

**涉及文件**: 
- `frontend/src/components/MarkdownRenderer.tsx`
- `frontend/src/pages/Chat.tsx`
- `backend/app/api/files.py` (download 接口)

**修复步骤**:

#### 方案 A：改用 Cookie 认证（推荐）

1. 登录成功后，将 Token 存入 httpOnly Cookie
2. 前端请求自动携带 Cookie
3. 移除所有 URL 中的 token 参数

```typescript
// Login.tsx 修改
const loginResult = await api.post('/auth/login', { username, password });
// Token 由后端 Set-Cookie 设置，前端无需手动存储

// api.ts 修改
const apiClient = axios.create({
    withCredentials: true,  // 自动携带 Cookie
    baseURL: '/api',
});
```

2. 后端修改认证中间件支持 Cookie 读取：

```python
# security.py 修改
from fastapi import Request, Cookie

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    token = credentials.credentials if credentials else access_token
    if not token:
        raise HTTPException(status_code=401, detail="未提供认证信息")
    # ... 后续解码逻辑不变
```

3. 文件下载接口移除 token query 参数，改为依赖 Cookie

#### 方案 B：短期快速修复（如果无法改 Cookie）

1. 移除 MarkdownRenderer 中的 token 附加逻辑
2. 文件下载改用 POST + Body 或 Session-based 临时授权
3. WebSocket 保持现有方式但添加过期时间限制

**验证方法**:
- 浏览器 Network 面板检查图片请求 URL 无 token 参数
- 图片正常加载显示
- WebSocket 连接正常工作

---

## 阶段二：高危漏洞修复（P1 - 1周内完成）

### 2.1 沙箱安全增强

**涉及文件**: 
- `backend/app/services/sandbox/local/subprocess_backend.py`
- `backend/app/services/agent_tools.py` (execute_code 相关)

**修复方案（分层防御）**:

#### 层级 1：改进模式匹配（立即实施）

```python
_DANGEROUS_BASH_ALWAYS = [
    "rm -rf /", "rm -rf ~", "sudo ", "mkfs", "dd if=",
    ":(){ :", "chmod 777 /", "chown ", "shutdown", "reboot",
    "python3 -c", "python -c",
    # 新增变体检测
    r"rm\s+-[a-z]*rf",  # rm -rf 变体
    r"/bin/(ba)?sh",     # shell 调用
    r">\s*/dev/",        # 设备写入
    r"curl\s", r"wget\s", # 网络下载（始终阻止）
    r"nc\s", r"ncat\s",  # netcat
    r"\|.*sh",            # 管道到shell
    r"\$\(",             # 命令替换
    r"eval\s",            # eval
    r"source\s",          # source
]

# 使用正则表达式而非简单 in 匹配
import re
def _check_bash_safety(code: str) -> str | None:
    for pattern in _DANGEROUS_BASH_REGEXES:
        if re.search(pattern, code, re.IGNORECASE):
            return f"Blocked: dangerous pattern detected"
    return None
```

#### 层级 2：环境隔离（1周内）

```python
async def execute(self, code, language, timeout=30, work_dir=None):
    # 清理环境变量，只保留必要项
    safe_env = {
        "HOME": str(work_path),
        "PATH": "/usr/bin:/bin",  # 限制 PATH
        "TMPDIR": str(work_path / "_tmp"),
        "PYTHONDONTWRITEBYTECODE": "1",
        # 移除所有敏感变量
    }
    
    # 创建临时目录用于沙箱
    tmp_dir = work_path / "_tmp"
    tmp_dir.mkdir(exist_ok=True)
    
    # 使用 prlimit 限制资源
    proc = await asyncio.create_subprocess_exec(
        "prlimit", "--nofile=64", "--nproc=8", "--as=268435456",  # 256MB地址空间
        *cmd_prefix, str(script_path),
        cwd=str(work_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=safe_env,
    )
```

#### 层级 3：容器化沙箱（长期目标）

- 评估 E2B / CodeSandbox / Judge0 等托管沙箱服务
- 或部署 gvisor/runsc 容器运行时

---

### 2.2 路径遍历防护强化

**涉及文件**: `backend/app/api/files.py`, `backend/app/services/agent_tools.py`

**修复步骤**:

```python
import os

def _safe_path(agent_id: uuid.UUID, rel_path: str) -> Path:
    base = _agent_base_dir(agent_id).resolve()
    
    # 规范化路径，解析 .. 和符号链接
    clean_path = rel_path.replace("\\", "/").lstrip("/")
    clean_path = os.path.normpath(clean_path)
    
    # 禁止绝对路径
    if os.path.isabs(clean_path):
        raise HTTPException(status_code=403, detail="绝对路径不被允许")
    
    full = (base / clean_path).resolve()
    
    # 双重检查：确保最终路径在 base 内且不是符号链接逃逸
    try:
        full.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=403, detail="路径遍历不被允许")
    
    return full
```

**额外措施**:
- 白名单允许的扩展名
- 限制最大路径深度
- 记录可疑路径访问尝试

---

### 2.3 文件上传安全加固

**涉及文件**: `backend/app/api/upload.py`

**修复步骤**:

```python
import magic  # python-magic 库

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), ...):
    # 1. 扩展名白名单
    ALLOWED_EXTENSIONS = {
        ".txt", ".md", ".pdf", ".png", ".jpg", ".jpeg", ".gif",
        ".docx", ".xlsx", ".pptx", ".csv", ".json", ".xml"
    }
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"不支持的文件类型: {ext}")
    
    # 2. 总体大小限制
    content = await file.read()
    MAX_SIZE = 50 * 1024 * 1024  # 50MB
    if len(content) > MAX_SIZE:
        raise HTTPException(400, "文件过大 (最大 50MB)")
    
    # 3. Magic bytes 验证（内容类型与扩展名匹配）
    mime_type = magic.from_buffer(content, mime=True)
    EXT_MIME_MAP = {
        ".png": "image/png", ".jpg": "image/jpeg", ".pdf": "application/pdf",
        # ... 完整映射
    }
    if ext in EXT_MIME_MAP and not mime_type.startswith(EXT_MIME_MAP[ext].split("/")[0]):
        raise HTTPException(400, f"文件内容与扩展名不匹配 (实际: {mime_type})")
    
    # 4. 安全文件名（去除特殊字符）
    import re
    safe_name = re.sub(r'[^\w\.\-\u4e00-\u9fff]', '_', file.filename)
    if safe_name.startswith('.'):
        safe_name = '_' + safe_name
    
    # 5. 使用 UUID 作为实际文件名
    save_name = f"{uuid.uuid4().hex[:12]}_{safe_name}"
    save_path = uploads_dir / save_name
```

---

### 2.4 WebSocket 连接管理优化

**涉及文件**: `backend/app/api/websocket.py`

**修复步骤**:

```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[tuple]] = {}
        self._connection_times: dict[int, float] = {}  # 追踪连接时间
    
    async def connect(self, agent_id, websocket, session_id=None):
        await websocket.accept()
        if agent_id not in self.active_connections:
            self.active_connections[agent_id] = []
        self.active_connections[agent_id].append((websocket, session_id))
        self._connection_times[id(websocket)] = time.time()
    
    async def cleanup_stale_connections(self, max_age_seconds=3600):
        """定期清理超时连接"""
        now = time.time()
        for agent_id, connections in list(self.active_connections.items()):
            alive = []
            for ws, sid in connections:
                conn_time = self._connection_times.get(id(ws), now)
                if now - conn_time > max_age_seconds:
                    try:
                        await ws.close(code=1001)
                    except Exception:
                        pass
                else:
                    alive.append((ws, sid))
            if alive:
                self.active_connections[agent_id] = alive
            else:
                del self.active_connections[agent_id]
    
    # 在 main.py lifespan 中启动清理任务
    asyncio.create_task(periodic_cleanup())
```

---

## 阶段三：中危问题修复（P2 - 2周内）

### 3.1 CORS 配置收紧

**涉及文件**: `backend/app/main.py`, `backend/app/config.py`

```python
# config.py
class Settings(BaseSettings):
    CORS_ORIGINS: list[str] = []  # 默认空列表，强制显式配置
    
    @validator('CORS_ORIGINS', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

# main.py
_cors_origins = settings.CORS_ORIGINS
if not _cors_origins:
    logger.warning("⚠️ CORS_ORIGINS 未配置，将只允许同源请求")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["http://localhost:3000"],  # 仅开发默认值
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],  # 明确列出
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)
```

---

### 3.2 日志脱敏

**涉及文件**: 多个日志输出位置

**修复方案**: 创建统一的日志脱敏工具

```python
# backend/app/core/log_utils.py
import re
import logging

SENSITIVE_PATTERNS = [
    (r'(token["\s:]+)["\s]*([^"]{10,})"', r'\1***REDACTED***'),
    (r'(api_key["\s:]+)["\s]*([^"]{10,})]', r'\1***REDACTED***'),
    (r'(password["\s:]+)["\s]*([^"]+)"', r'\1***REDACTED***'),
    (r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer ***REDACTED***'),
]

def sanitize_log_message(message: str) -> str:
    for pattern, replacement in SENSITIVE_PATTERNS:
        message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
    return message

class SanitizingLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return sanitize_log_message(str(msg)), kwargs
```

---

### 3.3 错误信息标准化

**涉及文件**: `backend/app/api/auth.py`, 所有异常处理位置

```python
# 创建统一错误响应工具
# backend/app/core/errors.py

class AppError(HTTPException):
    """统一的应用错误类"""
    def __init__(self, status_code: int, user_msg: str, log_msg: str = None):
        super().__init__(status_code=status_code, detail=user_msg)
        self.log_msg = log_msg or user_msg

# 使用示例
# auth.py login 函数
if not user or not verify_password(data.password, user.password_hash):
    # 统一的错误提示，不暴露用户是否存在
    raise AppError(401, "用户名或密码错误", f"Login failed for username: {data.username}")
```

---

### 3.4 依赖锁定

**修复步骤**:

```bash
# 后端：使用 poetry 或 pip-tools 锁定版本
pip install pip-tools
pip-compile requirements.in  # 生成 requirements-lock.txt
pip-sync  # 安装锁定版本

# 前端：确保 package-lock.json 提交到仓库
npm ci  # 而非 npm install

# 添加 GitHub Dependabot 配置
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
```

---

### 3.5 注册接口加固

**涉及文件**: `backend/app/api/auth.py`

**修复步骤**:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("5/minute")  # 速率限制：每分钟最多5次注册
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    # 密码强度验证
    password = data.password
    if len(password) < 8:
        raise HTTPException(400, "密码长度至少8位")
    if not re.search(r'[A-Z]', password):
        raise HTTPException(400, "密码需包含大写字母")
    if not re.search(r'\d', password):
        raise HTTPException(400, "密码需包含数字")
    
    # 用户名格式验证
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', data.username):
        raise HTTPException(400, "用户名只能包含字母、数字、下划线，长度3-20位")
    
    # 首个用户管理员竞态保护（使用数据库锁）
    # ... 其余逻辑
```

---

## 阶段四：性能优化与代码质量（P3 - 持续改进）

### 4.1 前端性能优化

**虚拟滚动集成**:

```bash
npm install react-window react-virtuoso
```

```typescript
// Chat.tsx 消息列表改造
import { Virtuoso } from 'react-virtuoso';

<Virtuoso
    data={messages}
    itemContent={(index, msg) => <MessageItem key={msg.id} message={msg} />}
    followOutput="smooth"
    overscan={20}
/>
```

**图片懒加载**:

```typescript
// MarkdownRenderer.tsx 图片懒加载
return `<img src="${finalUrl}" alt="${alt}" loading="lazy" decoding="async" ... />`;
```

**React.memo 优化消息组件**:

```typescript
export const MessageItem = React.memo(function MessageItem({ message }: Props) {
    // ...
}, (prev, next) => prev.message.id === next.message.id && prev.message.content === next.message.content);
```

---

### 4.2 Docker 安全加固

**docker-compose.yml 增强**:

```yaml
services:
  backend:
    image: clawith-backend
    user: "1000:1000"          # 非 root 运行
    read_only: true            # 只读文件系统（配合 tmpfs）
    tmpfs:
      - /tmp:size=100M
      - /var/tmp:size=50M
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
  
  postgres:
    environment:
      - POSTGRES_INITDB_ARGS=--scram-sha-256
    command: >
      postgres
      -c ssl=on
      -c ssl_cert_file=/var/lib/postgresql/server.crt
      -c ssl_key_file=/var/lib/postgresql/server.key
```

---

### 4.3 CI/CD 安全流水线

**GitHub Actions 示例**:

```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]
jobs:
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: TruffleHog Secret Scan
        uses: trufflesecurity/trufflehog@v3
  
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Python Dependency Check
        run: |
          pip install safety
          safety check -r requirements.txt || true
      - name: npm Audit
        run: npm audit --audit-level moderate
  
  sast-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Bandit Scan
        run: pip install bandit && bandit -r backend/ -ll || true
```

---

## 实施时间表

| 阶段 | 任务 | 预计工时 | 优先级 |
|------|------|----------|--------|
| P0-1.1 | 更换默认密钥 | 0.5h | 🔴 紧急 |
| P0-1.2 | 数据库凭据加固 | 0.5h | 🔴 紧急 |
| P0-1.3 | XSS 漏洞修复 | 2h | 🔴 紧急 |
| P0-1.4 | Token 泄露修复 | 4h | 🔴 高 |
| **小计** | **阶段一** | **7h** | |
| P1-2.1 | 沙箱安全增强 | 8h | 🔴 高 |
| P1-2.2 | 路径遍历防护 | 2h | 🟠 中 |
| P1-2.3 | 文件上传加固 | 3h | 🟠 中 |
| P1-2.4 | WebSocket 管理 | 2h | 🟠 中 |
| **小计** | **阶段二** | **15h** | |
| P2-3.x | 中危问题修复 | 16h | 🟢 低 |
| P3-4.x | 性能与质量 | 20h | 🟢 低 |
| **总计** | | **~58h** | |

---

## 验证清单

每个阶段完成后需要执行的验证：

- [ ] 单元测试通过 (`pytest backend/`)
- [ ] 前端构建成功 (`npm run build`)
- [ ] Docker 编译成功 (`docker-compose build`)
- [ ] 安全扫描无新增高危问题
- [ ] 手动测试核心流程：注册 → 登录 → 创建Agent → 聊天 → 上传文件
