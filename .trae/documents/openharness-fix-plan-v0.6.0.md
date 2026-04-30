# OpenHarness v0.5.0 审计问题修复计划

**基于审计报告**: `openharness-full-audit-report-v0.5.0.md`
**目标版本**: v0.6.0
**修复范围**: 24 项问题（3 高 / 7 中 / 8 低 + 2 安全 + 6 性能）

---

## 修复总览

| 阶段 | 修复项 | 涉及文件 | 预计改动量 |
|------|--------|----------|-----------|
| Phase 1: P0 紧急修复 | H1, H2, H3 | 3 文件 | ~20 行 |
| Phase 2: P1 中优先级 | M1-M7 | 7 文件 | ~150 行 |
| Phase 3: P2 低优先级 | L1-L8 | 8+ 文件 | ~120 行 |
| **总计** | **18+ 项** | **15+ 文件** | **~290 行** |

---

## Phase 1: P0 紧急修复（立即执行）

### Fix-H1: TaskStatus.COMPLETED → "completed"
- **文件**: `src/openharness/coordinator/autonomous_worker.py`
- **位置**: 第 334-339 行
- **操作**: 删除 `from openharness.tasks.types import TaskStatus` 导入，将 `TaskStatus.COMPLETED` 改为 `"completed"` 字符串字面量
- **验证**: 运行现有测试确保不回归

### Fix-H2: check_path_whitelist 默认拒绝
- **文件**: `src/openharness/swarm/team_lifecycle.py`
- **位置**: 第 324 行
- **操作**: 将 `return True, ""` 改为 `log.warning(...) + return False, f"路径不在白名单中"`
- **影响测试**: `tests/test_swarm/test_team_file_v2.py` 中的路径白名单测试需更新断言

### Fix-H3: flows.py Windows shell=True
- **文件**: `src/openharness/auth/flows.py`
- **位置**: 第 86-93 行
- **操作**: Windows 分支改用 `os.startfile(url)` 替代 `subprocess.Popen(["start", "", url], shell=True)`
- **注意**: 需在文件顶部添加 `import os`

---

## Phase 2: P1 中优先级修复

### Fix-M1: AgentMemory 并发写入保护
- **文件**: `src/openharness/coordinator/agent_memory.py`
- **操作**:
  1. 在 `AgentMemory.__init__` 中创建 `self._lock = asyncio.Lock()`
  2. `_save()` 和 `_load()` 方法加 `async with self._lock:` 保护
  3. `remember()` / `forget()` / `consolidate()` / `export_json()` / `import_json()` 均使用已保护的 `_save()`
- **注意**: `_load()` 在 `__init__` 中同步调用无需锁（此时无并发）

### Fix-M2: DenialTracker 线程安全
- **文件**: `src/openharness/permissions/denial_tracking.py`
- **操作**:
  1. 添加 `import threading`
  2. 创建模块级 `_tracker_lock = threading.Lock()`
  3. `get_denial_tracker()` 加锁保护单例创建
  4. `record_denial()` / `clear_denials()` / `_cleanup()` 加锁

### Fix-M3: PathWhitelistManager 路径规范化
- **文件**: `src/openharness/permissions/path_whitelist.py`
- **操作**:
  1. `check_path()` 方法开头添加 `resolved = str(Path(target_path).resolve())`（捕获异常回退到原始值）
  2. 后续匹配使用 `resolved` 而非原始 `target_path`
  3. 测试中增加路径遍历用例

### Fix-M4: CompactCache OrderedDict LRU
- **文件**: `src/openharness/services/compact/cached_compact.py`
- **操作**:
  1. 导入 `collections.OrderedDict`
  2. 将 `_entries: dict` 改为 `OrderedDict`
  3. `lookup()` 方法命中时调用 `self._entries.move_to_end(tool_id)` 更新访问顺序
  4. `record_cleared()` 淘汰时直接 `self._entries.popitem(last=False)` 取最旧

### Fix-M5: YOLO 分类器复合命令检查
- **文件**: `src/openharness/permissions/yolo_classifier.py`
- **操作**:
  1. `classify()` 方法中，safe pattern match 命中后追加检查：将命令按 `&&`, `||`, `;`, `|` 拆分为子命令
  2. 对每个子命令重新执行危险模式 search 检查
  3. 若任何子命令命中危险模式，返回 deny 覆盖 allow
  4. 新增复合命令测试用例

### Fix-M6: DAG DFS 深度限制
- **文件**: `src/openharness/tasks/dag.py`
- **操作**:
  1. `_check_circular_dependency()` 添加 `max_depth: int = 1000` 参数
  2. 每次递归调用时 depth += 1
  3. 超过 max_depth 时抛出 `CircularDependencyError` 或自定义 `DependencyChainTooDeepError`
  4. 测试中添加超长链用例

### Fix-M7: autonomous_worker TODO 标注清理
- **文件**: `src/openharness/coordinator/autonomous_worker.py`
- **操作**:
  1. 将 3 个 `# TODO: ...` 替换为明确的 `# Phase 3 待实现: ...` 标注
  2. 为每个占位函数添加 `raise NotImplementedError("Phase 3 待实现")` 或空 pass + docstring 说明预期行为
  3. 确保不影响现有测试

---

## Phase 3: P2 低优先级优化

### Fix-L1: 类型注解统一为 T | None
- **涉及文件**:
  - `src/openharness/permissions/denial_tracking.py` (第32行)
  - `src/openharness/coordinator/autonomous_worker.py` (第26行)
  - `src/openharness/cli.py` (第8行)
  - `src/openharness/coordinator/coordinator_mode.py` (第8行)
  - `src/openharness/tasks/types.py` (第34, 50行)
- **操作**: 将 `from typing import Optional` 及所有 `Optional[T]` 替换为 `T | None`，删除 Optional 导入

### Fix-L2: CompactWarningHook 复用 token_estimation
- **文件**: `src/openharness/hooks/compact_warning.py`
- **操作**:
  1. 导入 `from openharness.services.token_estimation import estimate_tokens`
  2. 重写 `estimate_message_tokens()` 方法：对每条消息的文本内容调用 `estimate_tokens()` 求和
  3. 删除固定因子 0.4 的简化逻辑

### Fix-L3: path_whitelist from_config_file 异常处理
- **文件**: `src/openharness/permissions/path_whitelist.py`
- **操作**:
  1. `from_config_file()` 整体包裹 try-except
  2. 捕获 `(json.JSONDecodeError, KeyError, TypeError, ValueError)` 记录 warning 日志
  3. 异常时返回空的默认配置（而非崩溃）
  4. 对每个 rule 构造也做 try-except 保护

### Fix-L4: todo_write_tool 匹配逻辑改进
- **文件**: `src/openharness/tools/todo_write_tool.py`
- **操作**:
  1. `_sync_to_task_system()` 完成匹配时增加 `.strip()` 两端空白处理
  2. 使用部分匹配（`in` 操作符）替代精确相等作为 fallback
  3. 添加日志记录匹配过程便于调试

### Fix-L5: TeamMember dataclasses.replace 更新
- **文件**: `src/openharness/swarm/team_lifecycle.py`
- **位置**: `set_member_mode()` (第544行) 和 `set_multiple_member_modes()` (第596行)
- **操作**:
  1. 添加 `from dataclasses import replace`
  2. 将 `TeamMember(**{**m.to_dict(), "mode": mode})` 改为 `replace(m, mode=mode)`
  3. 同理修改 `set_member_active()` 中的 is_active 更新

### Fix-L6: 时间戳回退逻辑优化
- **文件**: `src/openharness/services/compact/__init__.py`
- **位置**: 第239行
- **操作**: 将 `time.time() if not message_timestamps else message_timestamps[-1]` 改为 `(message_timestamps or [time.time()])[-1]`

### Fix-L7: mypy 配置统一
- **文件**: `pyproject.toml`
- **操作**: 将 `[tool.mypy]` 下 `strict = true` 改为：
  ```toml
  [tool.mypy]
  python_version = "3.11"
  strict = false
  check_untyped_defs = true
  disallow_any_generics = true
  warn_return_any = true
  warn_unused_configs = true
  ```

### Fix-L8: 补充测试覆盖盲区
- **新建测试文件**:
  1. `tests/test_swarm/test_mailbox.py` — mailbox 基础功能测试
  2. `tests/test_services/test_session_storage.py` — session 存储测试
- **增强现有测试**:
  3. `tests/test_engine/test_query_engine.py` — 增加 submit_message / continue_pending 边界测试
  4. `tests/test_permissions/test_path_whitelist.py` — 增加路径遍历防护测试

---

## 执行顺序与依赖关系

```
Fix-H1 ──────────────────────────────┐
Fix-H2 ──────────────────────────────┤──→ 运行全量测试 ──→ Phase 1 完成
Fix-H3 ──────────────────────────────┘
         │
         ▼
Fix-M1 ──┐
Fix-M2 ├──┤
Fix-M3 ├──┼──→ 运行全量测试 ──→ Phase 2 完成
Fix-M4 ├──┤
Fix-M5 ├──┤
Fix-M6 ├──┤
Fix-M7 ──┘
         │
         ▼
Fix-L1 ~ L8（可并行）──→ 运行全量测试 + Ruff ──→ Phase 3 完成
         │
         ▼
   版本升级 v0.6.0 + CHANGELOG 更新
```

---

## 验证清单

每完成一个 Phase 后执行：

1. **单元测试**: `python3 -m pytest tests/ -q` — 全部通过
2. **代码规范**: `python3 -m ruff check src tests` — All checks passed
3. **类型检查**: `python3 -m mypy src/openharness --ignore-missing-imports --no-strict` — 无新增错误
4. **回归验证**: 确保 647 个原有测试不受影响

---

## 版本发布计划

- **v0.6.0**: 包含 Phase 1-3 所有修复
- **CHANGELOG 条目**:
  - Fixed: TaskStatus Literal 类型错误导致 Worker 崩溃
  - Fixed: 团队路径白名单默认放行安全风险
  - Fixed: Windows 平台 shell=True 潜在注入风险
  - Security: PathWhitelistManager 路径规范化防遍历
  - Security: DenialTracker 线程安全加固
  - Performance: CompactCache LRU 淘汰策略优化
  - Performance: AgentMemory 并发写入保护
  - Robustness: DAG 循环检测深度限制防栈溢出
  - Code Quality: 类型注解风格统一、异常处理补全、mypy 配置修正
  - Tests: 新增 mailbox / session_storage 测试覆盖
