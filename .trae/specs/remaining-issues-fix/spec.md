# 遗留问题专项修复 Spec

## Why
在全面测试优化完成后，发现三个需要后续处理的技术债务：
1. **Next.js 4 个高危安全漏洞** - 当前版本 14.2.0 存在已知 CVE，需升级至 16.x
2. **集成测试 6 个用例被跳过** - `run_async()` 异步执行机制导致 Flask 请求上下文丢失，影响端到端测试完整性
3. **覆盖率工具追踪受限** - pytest-cov 无法正确追踪使用 sys.modules mock 的 Service 层模块，导致覆盖率数据不准确

这些问题影响项目的安全性、测试完整性和质量门禁能力，需要在虚拟环境中系统性修复。

## What Changes

### 1. Next.js 安全升级 (14.2.0 → 15.x/16.x)
- 升级 Next.js 及相关依赖（eslint-config-next, react 等）
- 处理 Breaking Changes（App Router API 变更、Server Components 行为变化）
- 确保所有现有页面和组件兼容新版本
- 验证构建、测试、运行时无回归

### 2. 集成测试修复 (启用 6 个跳过的测试)
- 重构 `run_async()` 或替换为 Flask TestClient 原生异步支持
- 修复请求上下文丢失问题
- 启用并验证以下集成测试：
  - 完整对话生命周期（Agent→Session→Chat→Message）
  - 多轮对话暂停/恢复
  - 消息统计准确性
  - 团队创建与任务委派
  - Session Token 统计一致性

### 3. 覆盖率工具改进
- 评估 sys.modules mock 对 pytest-cov 的影响范围
- 提供替代方案：条件导入、conftest 级别 mock、或 CI 环境真实依赖安装
- 确保覆盖率报告准确反映 Service 层测试覆盖情况
- 设置覆盖率阈值门禁（目标 ≥70%）

## Impact

### 受影响的代码文件
**前端：**
- `frontend/package.json` (依赖版本更新)
- `frontend/next.config.*` (可能需要配置变更)
- `frontend/app/**/*.tsx` (可能的 API 兼容性调整)
- `frontend/tsconfig.json` (TypeScript 配置)

**后端：**
- `backend/app/core/async_utils.py` (run_async 机制重构)
- `backend/app/api/sessions.py` (集成测试涉及)
- `backend/app/api/chat.py` (集成测试涉及)
- `backend/tests/test_integration.py` (启用跳过的测试)
- `backend/tests/conftest.py` (mock 策略调整)
- 各 Service 测试文件的 mock 方式

### 受影响的规范
- 安全合规：消除 4 个高危 CVE
- 测试完整性：从 531 passed + 6 skipped → 目标 537+ all passed
- 质量门禁：准确的覆盖率数据支持 CI/CD 决策

---

## ADDED Requirements

### Requirement: Next.js 安全升级
系统 SHALL 升级至无已知高危漏洞的 Next.js 版本，同时保持功能完全兼容。

#### Scenario: 成功升级到 Next.js 15.x
- **WHEN** 执行 `npm install next@latest`
- **THEN** 所有依赖解析成功，无 peer dependency 冲突
- **AND** `npm run build` 成功编译所有 13 个页面
- **AND** `npm run test` 所有 35 个前端测试通过
- **AND** `npm audit` 无 high/critical 级别漏洞

#### Scenario: Breaking Changes 处理
- **WHEN** 升级后发现 API 不兼容
- **THEN** 按照官方迁移指南逐项修复
- **AND** 记录所有修改及其原因

### Requirement: 集成测试完整性
系统 SHALL 支持完整的端到端集成测试，所有测试用例均可正常执行。

#### Scenario: 修复 run_async 上下文问题
- **WHEN** 运行 `pytest tests/test_integration.py -v`
- **THEN** 所有 11 个测试通过（无 skipped）
- **AND** 完整对话流程测试验证 Agent→Session→Chat→Message 数据一致性
- **AND** Token 统计准确反映消息记录

#### Scenario: 替代方案（如重构成本过高）
- **WHEN** run_async 重构风险过大
- **THEN** 采用 Flask async TestClient 或 httpx.AsyncClient 直接调用
- **OR** 将集成测试改为直接调用 service 层（绕过 HTTP 层）

### Requirement: 准确的覆盖率报告
系统 SHALL 提供可信的代码覆盖率数据，用于 CI/CD 质量门禁。

#### Scenario: Service 层覆盖率可见
- **WHEN** 运行 `pytest tests/ --cov=app/services --cov-report=term-missing`
- **THEN** 显示各 service 模块的真实覆盖率百分比
- **AND** 未覆盖行数准确列出
- **AND** 总体覆盖率 ≥70%

#### Scenario: CI 环境覆盖率
- **WHEN** 在 CI 管道中运行完整测试套件
- **THEN** 覆盖率报告生成并可归档
- **AND** 低于阈值时构建失败

---

## MODIFIED Requirements

### Requirement: 安全基线
原要求：审计并记录漏洞
**修改后**：审计 → 修复 → 验证零高危漏洞

### Requirement: 测试通过率
原要求：531 passed, 6 skipped
**修改后**：537+ passed, 0 skipped（所有集成测试启用）

### Requirement: 覆盖率准确性
原要求：预估 70%+（基于测试设计）
**修改后**：实测 70%+（基于工具报告）

---

## REMOVED Requirements
无

---

## 技术约束与风险评估

### Next.js 升级风险矩阵

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Breaking Changes | 高 | 高 | 先升 15.x（LTS），暂缓 16.x |
| 依赖冲突 | 中 | 中 | 使用 npm resolve 冲突 |
| 构建失败 | 低 | 高 | 保留当前版本备份 |
| 性能回归 | 低 | 中 | Lighthouse 对比测试 |

### 推荐升级路径
```
Current:  Next.js 14.2.35
    ↓ (推荐)
Target:   Next.js 15.x (LTS, 稳定版)
    ↓ (可选，高风险)
Future:   Next.js 16.x (最新版)
```

### 集成测试修复方案选项

**方案 A：重构 run_async（推荐）**
- 优点：根本解决，架构更清晰
- 缺点：可能影响其他使用 run_async 的地方
- 工作量：中等

**方案 B：改用 AsyncClient**
- 优点：绕开问题，改动局部化
- 缺点：不测试真实的 HTTP 层
- 工作量：较小

**方案 C：Service 层直接调用**
- 优点：最简单，测试速度最快
- 缺点：不覆盖 API 路由和中间件
- 工作量：最小

### 覆盖率改进方案

**方案 A：CI 安装完整依赖（推荐）**
- 移除 sys.modules mock
- CI 环境 pip install openharness
- 真实导入，准确追踪

**方案 B：条件 Mock**
- 仅 mock 网络/外部调用
- 保持真实模块导入路径
- 本地开发也可获得覆盖率

**方案 C：coverage.py 替代 pytest-cov**
- 使用底层 coverage 库
- 更灵活的配置选项
- 可能解决追踪问题

---

## 成功标准

1. **安全**: `npm audit` 返回 0 high/critical
2. **测试**: `pytest tests/ -v` 显示 537+ passed, 0 failed, 0 skipped, 0 errors
3. **覆盖率**: `--cov=app/services` 显示总体 ≥70%，各模块 ≥60%
4. **构建**: `npm run build` 成功，所有页面编译通过
5. **前端测试**: `npm run test` 35 个全部通过
6. **性能**: Lighthouse Performance Score 无明显下降（≥90）
7. **兼容性**: 所有现有功能手动验证通过
