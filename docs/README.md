# OpenClaw-Harness 调试文档总索引

> 生成时间：2026-04-12
> 基于架构文档 `architecture.md` 对照实际代码的诊断结果

## 文档概览

本文档集包含四轮深度审查发现的 **74 个问题**，按问题类型分类整理如下：

## 问题统计汇总

| 严重度 | Round 1 | Round 2 | Round 3 | Round 4 | 总计 |
|--------|---------|---------|---------|---------|------|
| **P0 - 运行时崩溃** | 3 | 8 | 6 | 4 | **21** |
| **P1 - 功能失效** | 2 | 12 | 5 | 4 | **23** |
| **P2 - 安全/数据风险** | 1 | 5 | 5 | 2 | **13** |
| **P3 - 配置/一致性** | 2 | 6 | 7 | 2 | **17** |
| **合计** | 8 | 31 | 23 | 12 | **74** |

## 文档导航

| 文档 | 说明 | 问题数量 |
|------|------|---------|
| [01-global-config-issues.md](./01-global-config-issues.md) | 全局配置与环境问题 | 技术栈版本、环境变量等 |
| [02-backend-core-issues.md](./02-backend-core-issues.md) | 后端核心问题 | 应用、配置、数据库、API |
| [03-frontend-issues.md](./03-frontend-issues.md) | 前端问题 | 依赖、组件、类型定义 |
| [04-openharness-integration.md](./04-openharness-integration.md) | OpenHarness 集成问题 | API 不匹配、配置冲突 |
| [05-security-issues.md](./05-security-issues.md) | 安全问题 | 漏洞、权限、沙箱安全 |
| [06-infrastructure-deployment.md](./06-infrastructure-deployment.md) | 基础设施与部署问题 | Docker、迁移、部署 |
| [07-debugging-reference.md](./07-debugging-reference.md) | 调试参考手册 | 各模块调试命令速查 |

## 核心结论

经过四轮验证，共发现 74 个问题。核心矛盾集中在三个方面：

1. **OCH-OpenHarness 集成层系统性 API 不匹配**（P0）：`OpenHarnessConfig` 不存在、`QueryEngine` 构造签名错误、`ToolRegistry` API 错误、SandboxAvailability 属性缺失、`Settings.load()` 方法不存在——这些意味着 OCH 的核心功能（AI 对话、工具执行、沙箱、权限）在运行时全部会崩溃

2. **Mock/Stub 占位而非真实实现**（P1）：`_simulate_stream()`、`_mock_agent_stream()`、`spawn_subagent()` 返回内存 dict——整个 AI Agent Loop 是模拟的

3. **配置系统双重体系冲突**（P3）：OCH `app/config.py` 和 OpenHarness `openharness/config/settings.py` 各自独立，通过环境变量隐式耦合，默认值冲突导致 OCH 的低值覆盖 OpenHarness 的高值

## 建议优先级

1. 先修复 P0 的 21 个运行时崩溃问题
2. 再替换 Mock 实现真实集成
3. 最后统一配置体系
