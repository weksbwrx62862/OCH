# Tasks — DeerFlow & OpenHarness 深度学习分析

## 阶段 1: 文档与源码学习（已完成 ✅）

- [x] **T1: 读取增强指南文档** — deerflow_openharness_enhancement_guide.md (2791行)
- [x] **T2: 读取对比分析文档** — deerflow_vs_openharness_comparison.md (567行)
- [x] **T3: 探索 DeerFlow 源码目录结构** — backend/packages/harness/ 下 30+ 子目录
- [x] **T4: 深入分析核心源码文件** — 8 个关键文件（agent/executor/sandbox/security/updater/tools/thread_data/app）
- [x] **T5: 综合提炼形成初始报告** — spec.md 七大章节

## 阶段 2: OCH 功能缺口深度分析（已完成 ✅）

- [x] **T6: 发现 OCH 双层架构** — `app/` (Flask API) + `openharness/` (核心引擎) 仅 3 处引用
- [x] **T7: 逐模块功能对比** — 18 个功能点逐一验证（F01-F18）
- [x] **T8: 识别 OCH 独有优势** — 8 个超越 DeerFlow 的功能（E01-E08）
- [x] **T9: 评估优先级与 ROI** — P0(3项纯集成) / P1(4项增强) / P2(3项新开发)
- [x] **T10: 更新 spec.md 附录 A** — 完整缺口矩阵 + 路线图 + 投资回报率分析

### 缺口分析核心发现

| 类别 | 数量 | 关键结论 |
|------|------|---------|
| ⚠️ 已有未集成 | 10 个 | openharness/ 已实现但 app/ 未使用 |
| ❌ 完全缺失 | 8 个 | 需要参考 DeerFlow 新开发 |
| ✅ OCH 独有优势 | 8 个 | DAG/Cron/DenialTracker/12渠道等 |
| 🔴 P0 集成任务 | 3 个 | 总计 ~170 行，风险极低 |

---

## 阶段 3: 优化实施（全部完成 ✅）

### P0: 立即集成三件套 ✅
- [x] **P0-1**: DenialTracker → permissions.py (~50行) — SHA256指纹+TTL缓存
- [x] **P0-2**: HookExecutor → session_service.py (~80行) — PRE/POST_TOOL_USE
- [x] **P0-3**: CompactCache → chat 流程 (~40行) — LRU微压缩缓存

### P1: 架构增强 ✅
- [x] **P1-1**: 中间件管道模式 (~200行) — BaseMiddleware ABC + Pipeline + 4个内置中间件
- [x] **P1-2**: PermissionChecker 统一 (~100行修改) — 三重校验(DB+Checker+Tracker)
- [x] **P1-3**: AutonomousWorker 升级 coordinator.py (~150行) — Worker CRUD + 统计
- [x] **P1-4**: 结构化记忆系统升级 (~300行) — MemoryFact模型 + Facts API + 纠错/正反馈信号

### P2: 差异化功能 ✅
- [x] **P2-1**: IM 渠道集成框架 (~500行) — 12渠道类型支持 + ChannelManager
- [x] **P2-2**: 沙箱抽象层接入 (~200行) — srt适配器 + 命令包装 + 安全检查
- [x] **P2-3**: 子代理双线程池引擎 (~400行) — 调度池+执行池 + 并发限制

---

## 实施结果总览

| 指标 | 优化前 | 优化后 | 变化 |
|------|--------|--------|------|
| **API 路由数** | 89 | **127** | **+38 (+42.7%)** |
| **Blueprint 数量** | 11 | **14** | **+3** (memory/channels/sandbox) |
| **DB 模型数** | 14 | **15** | **+1** (MemoryFact) |
| **中间件数量** | 0 | **4** | Auth/RateLimit/Validation/Audit |
| **单元测试** | 34 passed | **34 passed** | ✅ 全部通过 |
| **新增文件** | - | **7** | middleware/__init__, memory.py, memory_fact.py, channels.py, sandbox.py, subagent_executor.py |

### 新增 API 端点清单

| Blueprint | 新增端点 | 说明 |
|-----------|---------|------|
| permissions | +3 | denials/tracker, tracker/clear, check(三重校验) |
| sessions | +3 | compact-cache, cache/lookup, cache/clear-expired |
| coordinator | +9 | workers(CRUD), subagents(CRUD/stats) |
| memory | +9 | facts(CRUD), stats, recall, signal/correction, signal/reinforcement |
| channels | +9 | types, registered, register(CRUD), send, test, stats |
| sandbox | +4 | status, execute, wrap, security-check |
| main | +1 | middleware (管道信息) |

# Task Dependencies
- T6-T10 depends on T1-T5 (需先完成基础学习) ✅
- P0-x depends on T6-T10 (需先完成缺口分析) ✅
- P1-x depends on P0-x (先做集成再做增强) ✅
- P2-x depends on P1-x (最后做差异化功能) ✅
