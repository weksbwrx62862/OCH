# 安全问题

## 1. 安全漏洞汇总

| # | 严重度 | 问题 | 位置 | 调整建议 |
|---|--------|------|------|---------|
| 1 | **高** | 沙箱本地模式无命令过滤 | `sandbox.py:208-224` | `_execute_locally()` 直接 `subprocess.run(shlex.split(command))`，任何认证用户都可以通过 API 执行任意系统命令 |
| 2 | **高** | `ADMIN_PASSWORD` 明文 vs bcrypt 不匹配 | `auth.py:51` | `verify_password(password, settings.ADMIN_PASSWORD)` 将明文密码当作哈希使用，导致生产环境登录永远失败 |
| 3 | **高** | 开发模式无密码即 admin | `auth.py:46` | 任何用户名都能获得 `role='admin'` 的 JWT token，如果误在生产环境设置 `APP_ENV=development`，将导致严重安全问题 |
| 4 | **中** | 配置 API 直接 setattr 绕过验证 | `config_api.py:112` | `setattr(settings, key, data[key])` 不经过 Pydantic 验证，可以设置无效值（如 `OPENHARNESS_MAX_TOKENS=-1`） |
| 5 | **中** | `SECRET_KEY` 默认值为 `change-me-in-production` | `config.py` | 如果生产环境未修改，JWT 签名可被伪造 |
| 6 | **中** | 安全检测模式使用简单 `in` 匹配 | `sandbox.py:338` | `format` 会匹配 `information`，导致误报；同时也容易被绕过（如 `rm  -rf  /` 双空格） |
| 7 | **低** | CORS 默认允许 localhost | `config.py:39` | 本地开发正常，但生产部署时需要配置实际域名 |

## 2. 沙箱安全问题

### 2.1 沙箱本地模式无命令过滤

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `_execute_locally()` 无任何安全检查 | `sandbox.py:208-224` | 当 `use_sandbox=False` 或沙箱不可用时，直接执行用户输入的命令，存在命令注入风险。应至少进行基本危险命令过滤 |
| 2 | 安全检查使用简单字符串匹配 | `sandbox.py:338` | `security_check()` 使用 `pattern.lower() in command.lower()` 而非正则。简单的子串匹配容易绕过。例如 `rrm -rf /`（含空格变异）、`/bin/rm -rf /`（带路径前缀）可绕过 `'rm -rf /'` 匹配。且部分模式如 `wget.* | sh` 含正则语法但被当作字面量处理，`.*` 不会匹配任意字符。应使用正则表达式 `re.search()` |

### 2.2 安全边缘案例

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `_execute_locally()` 无命令过滤 | `sandbox.py:208-224` | 通过沙箱逃逸检查后，命令直接执行无任何过滤。恶意 Agent 理论上可构造破坏性命令（如 `rm -rf`）。应添加命令黑名单或白名单过滤 |
| 2 | `sandbox.py` 的 `_execute_locally()` 无任何安全检查 | `sandbox.py:208-224` | 当 `use_sandbox=False` 或沙箱不可用时，直接执行用户输入的命令，存在命令注入风险。应至少进行基本危险命令过滤 |

## 3. 认证与权限安全

### 3.1 认证问题

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | `ADMIN_PASSWORD` 空密码 | `auth.py:49` | 空字符串通过 `if not password` 检查，但 `secrets.compare_digest('', '')` 返回 True，意味着空密码可登录。必须在启动时检查 ADMIN_PASSWORD 非空 |
| 2 | JWT Secret 默认 `dev-secret-key` | `config.py:JWT_SECRET_KEY` | 生产环境如果不设置 `JWT_SECRET_KEY`，将使用硬编码的 dev key，任何人可伪造 token。应在启动时对生产环境强制检查 |
| 3 | 开发环境无需密码即可登录 | `auth.py:46` | 任何用户名都能获得 admin 权限，这是开发便利设计，但需确保生产环境 `APP_ENV != 'development'` |
| 4 | `ADMIN_PASSWORD` 为空时生产环境无法登录 | `auth.py:49-50` | `.env` 中 `ADMIN_PASSWORD` 未设置，生产环境启动后会返回 "Login disabled"，需要配置 |

### 3.2 需要修正的认证问题说明

| # | 原始描述 | 修正说明 |
|---|---------|---------|
| 1 | auth.py "ADMIN_PASSWORD 空密码意味着生产环境登录完全失效" | **需补充细节**：`auth.py:46-52` 在非 `development` 环境下，空 `ADMIN_PASSWORD` 会返回 "Login disabled"，**不是**允许空密码登录。但在 `development` 模式下，`auth.py:46` 跳过密码检查，任何人可以 admin 身份登录。这是开发模式的预期行为，但应在文档中区分说明 |

## 4. 插件与权限安全

| # | 问题 | 位置 | 调整建议 |
|---|------|------|---------|
| 1 | 插件安装无安全校验 | `plugin_service.py:172-189` | `subprocess.run(["pip", "install", ...])` 直接安装任意 pip 包，存在供应链攻击风险。应限制为只允许白名单仓库或添加 hash 校验 |
| 2 | `plugins.py` 的 `enable_plugin()` 不限制角色 | `plugins.py:113-124` | `enable/disable` 只需 `@require_auth`（任何认证用户），而 `install/uninstall` 需要 `@require_role('admin')`。启用/禁用插件应有更严格的权限控制 |
| 3 | `permissions.py` 中 `_current_permission_mode` 是模块级全局变量 | `permissions.py:69` | 只在当前进程生效，多 worker 部署时各 worker 模式不一致。应持久化到 DB 或 Redis |

## 5. 安全问题严重度总结

| 严重度 | 数量 | 关键问题 |
|--------|------|---------|
| **P0 - 运行时崩溃** | 4 | `Settings.load()` 不存在、`wrap_command_for_sandbox` 返回值类型错误（tuple 非 str）、`_NullHookExecutor` 降级也崩溃、`api_client=None` 传给必填参数 |
| **P1 - 功能失效** | 4 | WebSocket 代理不工作、安全检测绕过、plugin async 阻塞事件循环、spawn_subagent 不持久化 |
| **P2 - 安全/数据风险** | 2 | 多 worker 权限模式不同步、CompactCache 线程安全 |
| **P3 - 配置/一致性** | 2 | SSE 事件格式前后端契约不对齐、get_sandbox_availability 未传 Settings |

## 6. 建议修复优先级

1. **P0 - 立即修复**：
   - 沙箱本地模式无命令过滤
   - `ADMIN_PASSWORD` 明文 vs bcrypt 不匹配
   - 开发模式无密码即 admin

2. **P1 - 尽快修复**：
   - 配置 API 直接 setattr 绕过验证
   - `SECRET_KEY` 默认值问题
   - 安全检测模式使用简单 `in` 匹配

3. **P2 - 计划修复**：
   - CORS 默认允许 localhost（生产环境）
   - 插件安装无安全校验
   - 权限模式不持久化
