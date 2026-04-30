# 🗺️ OpenHarness 下一步发展路线图

**计划日期**: 2026-04-06
**基于版本**: OpenHarness v0.2.0（12/12 章节完整实现，~202 测试用例，14 子系统）
**目标**: 为项目从「功能完整」迈向「生产就绪」提供清晰的优先级路线图

---

## 📊 当前状态总览

| 维度 | 当前值 | 目标值 | 差距 |
|------|--------|--------|------|
| **章节完整性** | 12/12 (100%) ✅ | — | 已达成 |
| **测试数量** | ~202 | 300+ | +100 |
| **测试覆盖率** | 新增模块 ≥80%，整体未知 | 全量 ≥85% | 需验证 |
| **CI/CD** | 基础（test + lint） | 完整（coverage + release + benchmark） | 需增强 |
| **文档** | README + CHANGELOG | 架构文档 + API 文档 + 教程 | 需扩展 |
| **版本号** | 0.1.1 (pyproject.toml) | 0.2.0 | 未同步 |
| **代码质量** | Ruff 通过 | MyPy strict + coverage gate | 需强化 |

### 已完成的工作（Phase 1 + Phase 2）

```
✅ Phase 1a: 架构对比分析（文章理论 vs OpenHarness 代码，评分 90.8 vs 75.75）
✅ Phase 1b: 源码驱动的优化评估（发现 S06 压缩已完整实现）
✅ Phase 1c: 核心功能补全（A1 DAG + A2 协调协议 + A3 自治 Worker + B 类优化 6 项）
✅ Phase 2: 测试（88 新测试）、集成（DenialTracker → QueryEngine）、文档（README v0.2.0）
```

---

## 🎯 路线图总览：4 个阶段

```
Phase 0 ──────────→ Phase 1 ──────────→ Phase 2 ──────────→ Phase 3
  验证                功能增强              工程成熟               生态扩展
(立即执行)         (1-2 周)            (2-3 周)             (长期)
```

---

## 🔴 Phase 0: 验证与收尾（P0 — 立即执行，0.5 天）

> **目标**: 确保 Phase 1+2 的所有变更在当前环境中正确运行

### T0.1 运行全量测试套件

```bash
cd /home/xxh/claudecode源码(仅用于学习交流)/OpenHarness-main
uv run pytest tests/ -v --tb=short --cov=src/openharness --cov-report=term-missing
```

**预期结果**: ~202 测试全部通过，无回归

**验收标准**:
- [ ] 所有原有 114 测试通过（无回归）
- [ ] 所有新增 88 测试通过
- [ ] 覆盖率报告生成（了解基线）

### T0.2 运行 Lint 检查

```bash
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
```

**验收标准**:
- [ ] Ruff check 无 error/warning
- [ ] 格式化检查通过

### T0.3 版本号同步

**问题**: `pyproject.toml` 中 version 仍为 `0.1.1`，但 README 已标注 v0.2.0

**修改文件**: [pyproject.toml](pyproject.toml#L7)
```toml
version = "0.2.0"  # 从 0.1.1 升级
```

### T0.4 更新 CHANGELOG.md

**修改文件**: `CHANGELOG.md`
- 添加 v0.2.0 条目（日期 2026-04-06）
- 列出所有 Phase 1+2 的变更

---

## 🟡 Phase 1: 功能增强（P1 — 推荐，1-2 周）

> **目标**: 补齐 v2.0 计划中推迟的高价值功能项

### 1.1 必须做（影响功能完整性）

#### T1.1 缓存微压缩（Cached Microcompact）— 1.5 天

**来源**: v2.0 计划 B1.1（推迟项）
**参考**: Claude Code `src/services/compact/cachedMicrocompact.ts`

**核心思想**:
```
传统微压缩：删除旧工具输出 → 信息丢失
缓存微压缩：删除旧工具输出 → 记录被删内容 → API 支持 cache editing 时恢复
```

**为什么现在做**:
- Anthropic prompt caching 已广泛可用
- 对长对话场景 token 消耗降低 20-30%
- 是压缩系统的自然演进

**交付物**:
- `services/compact/cached_microcompact.py`（新文件，~150 行）
- 修改 `services/compact/__init__.py` 集成缓存逻辑
- 测试文件 `tests/test_services/test_cached_compact.py`（~10 用例）

**验收标准**:
- [ ] 支持记录被清除的工具输出摘要
- [ ] 在 Anthropic API 上可减少重复 token
- [ ] 向后兼容（无缓存 API 时退化为普通模式）

---

#### T1.2 Agent 内存管理系统 — 1 天

**来源**: v2.0 计划 B2.1
**参考**: Claude Code `src/tools/AgentTool/agentMemory.ts`

**核心功能**:
```python
@dataclass
class AgentMemory:
    agent_id: str
    memories: list[MemoryEntry]  # 持久化的记忆条目
    
    async def remember(self, content: str, category: str = "general") -> None:
        """记录一条记忆"""
        
    async def recall(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """根据查询检索相关记忆"""
        
    async def forget(self, memory_id: str) -> bool:
        """删除特定记忆"""
```

**为什么重要**:
- 子 Agent 目前没有跨会话记忆能力
- 让 Worker 能记住之前的工作上下文
- 是多 Agent 协作的基础设施

**交付物**:
- `coordinator/agent_memory.py`（新文件，~200 行）
- 测试文件 `tests/test_coordinator/test_agent_memory.py`（~12 用例）
- 集成到 `AutonomousWorker` 的初始化流程

**验收标准**:
- [ ] Agent 可读写持久化记忆
- [ ] 支持按关键词检索记忆
- [ ] 记忆数据可序列化到 JSON 文件

---

#### T1.3 团队文件增强（TeamFile v2）— 1 天

**来源**: v2.0 计划 B4.1
**参考**: Claude Code `teamHelpers.ts` TeamFile 类型定义

**增强内容**:

```python
@dataclass
class TeamMemberV2:
    agent_id: str
    name: str
    color: str = "blue"              # UI 显示颜色
    worktree_path: Optional[str] = None  # 成员专属 worktree
    permission_mode: str = "default"     # 权限模式
    is_active: bool = True               # idle/active 状态

@dataclass
class TeamFileV2:
    name: str
    description: str = ""
    created_at: float
    lead_agent_id: str
    members: list[TeamMemberV2]
    allowed_paths: list[AllowedPath] = field(default_factory=list)  # 路径白名单
```

**收益**:
- UI 可显示成员颜色和状态
- 权限控制粒度到成员级别
- 支持团队共享路径白名单

**交付物**:
- 修改 `swarm/types.py` 扩展 TeamRecord
- 修改 `swarm/team_lifecycle.py` 支持新字段
- 测试文件 `tests/test_swarm/test_team_file_v2.py`（~8 用例）

**验收标准**:
- [ ] TeamRecord 包含成员详细信息
- [ ] 序列化/反序列化兼容新旧格式
- [ ] 路径白名单功能可用

---

### 1.2 推荐做（提升工程质量）

#### T1.4 YOLO 权限分类器 — 2-3 天 ⚠️ 高复杂度

**来源**: v2.0 计划 B5.1
**参考**: Claude Code `src/utils/permissions/yoloClassifier.ts`

**功能**: 使用规则引擎自动判断 Bash 命令是否安全，减少用户确认次数

```python
class YoloClassifier:
    """You Only Live Once — 自动判断命令安全性"""
    
    SAFE_PATTERNS = [
        re.compile(r'^git\s+(status|log|diff|branch|tag)\b'),
        re.compile(r'^ls\b'),
        re.compile(r'^cat\s'),
        re.compile(r'^npm\s+(test|lint|build)\b'),
        re.compile(r'^pytest\b'),
        re.compile(r'^python\s+-m\s+pytest\b'),
    ]
    
    DANGEROUS_PATTERNS = [
        re.compile(r'rm\s+-rf\s+/'),
        re.compile(r'DROP\s+TABLE'),
        re.compile(r'chmod\s+777'),
        re.compile(r'>\s*/dev/sd[a-z]'),  # 磁盘写入
        re.compile(r'curl.*\|\s*(ba)?sh'),  # 远程脚本执行
    ]
    
    def classify(self, tool_name: str, tool_input: dict) -> YoloResult:
        """返回 ALLOW / ASK / DENY 三级判定"""
```

**⚠️ 决策点**: 这是一个高投入高回报的功能
- **投入**: 2-3 天（含规则库构建 + 测试）
- **回报**: 减少 50%+ 的权限确认弹窗
- **风险**: 安全分类错误可能导致安全问题
- **建议**: 先实现规则引擎版（不依赖 ML），后续可升级为 ML 分类器

**交付物**:
- `permissions/yolo_classifier.py`（新文件，~250 行）
- 测试文件 `tests/test_permissions/test_yolo_classifier.py`（~20 用例）
- 集成到 PermissionChecker 的 check 流程

**验收标准**:
- [ ] 安全命令自动放行（git status, ls, cat 等）
- [ ] 危险命令自动拒绝或强制确认
- [ ] 不确定命令保持默认行为（询问用户）
- [ ] 规则库可通过配置文件扩展

---

#### T1.5 Agent 定义系统 — 1.5 天

**来源**: v2.0 计划 B2.2
**参考**: Claude Code `loadAgentsDir.ts` + `builtInAgents.ts`

**功能**: 从 `agents/` 目录加载自定义 Agent 定义

```
~/.openharness/agents/
├── worker.md          # 通用 Worker 定义
├── researcher.md      # 研究型 Agent
├── test-runner.md     # 测试执行者
├── reviewer.md        # 代码审查员
└── custom/            # 用户自定义
    └── my-agent.md
```

**每个定义包含**:
```markdown
---
name: code-reviewer
model: sonnet
description: 专业代码审查 Agent
permissions:
  mode: plan
system_prompt: |
  你是一个专业的代码审查专家...
---
```

**交付物**:
- `coordinator/agent_definitions.py` 增强（已存在基础版本，需扩展）
- `coordinator/agent_loader.py`（新文件，目录扫描加载）
- 测试文件 `tests/test_coordinator/test_agent_loader.py`（~8 用例）

**验收标准**:
- [ ] 从 agents/ 目录加载 .md 定义
- [ ] 每个 Agent 有独立的 system_prompt、model、permissions
- [ ] 内置通用 Agent 类型可用

---

### 1.3 可选做（锦上添花）

| # | 功能 | 工作量 | 收益 | 备注 |
|---|------|--------|------|------|
| **T1.6** | Todo V2 统一集成 | 1 天 | 低 | 用 Task 替代 Todo，单一数据源 |
| **T1.7** | 路径白名单系统 | 0.5 天 | 中 | 团队成员不经确认编辑特定路径 |
| **T1.8** | 压缩警告 Hook | 0.5 天 | 低 | 接近上下文限制时显示警告 |

---

## 🟢 Phase 2: 工程成熟度（P2 — 2-3 周）

> **目标**: 达到生产级工程质量标准

### 2.1 CI/CD 增强

#### T2.1 覆盖率门禁

**当前 CI**: 仅运行 `pytest -q`（无覆盖率报告）

**增强方案**:

```yaml
# .github/workflows/ci.yml 新增 job
coverage:
  name: Coverage report
  runs-on: ubuntu-latest
  steps:
    - name: Run tests with coverage
      run: uv run pytest --cov=src/openharness --cov-report=xml --cov-fail-under=80
    - name: Upload coverage
      uses: codecov/codecov-action@v4
```

**验收标准**:
- [ ] 覆盖率低于 80% 时 CI 失败
- [ ] Codecov 报告自动上传
- [ ] PR 可查看覆盖率变化

---

#### T2.2 发布自动化

**当前**: 手动发版

**增强方案**:

```yaml
# .github/workflows/release.yml（新建）
release:
  on:
    push:
      tags: ['v*']
  jobs:
    build-and-publish:
      steps:
        - name: Build package
          run: uv build
        - name: Publish to PyPI
          uses: pypa/gh-action-pypi-publish@release/v1
```

**验收标准**:
- [ ] 打 tag 触发自动构建
- [ ] 自动发布到 PyPI
- [ ] 自动生成 GitHub Release

---

#### T2.3 性能基准测试

**新建文件**: `benchmarks/` 目录

```
benchmarks/
├── bench_dag_operations.py       # DAG 创建/解锁性能
├── bench_compression.py          # 压缩系统吞吐量
├── bench_permission_check.py     # 权限检查延迟
└── bench_tool_execution.py       # 工具执行开销
```

**使用 pytest-benchmark**:
```bash
uv run pytest benchmarks/ --benchmark-json=results.json
```

**验收标准**:
- [ ] DAG 1000 节点操作 < 100ms
- [ ] 压缩 100 条消息 < 50ms
- [ ] 权限检查 < 1ms
- [ ] 基准结果可追踪回归

---

### 2.2 代码质量强化

#### T2.4 MyPy 类型检查加入 CI

**当前**: 仅本地有 mypy 配置，CI 未运行

**增强**: 在 `ci.yml` 的 `python-quality` job 中添加

```yaml
- name: MyPy type checking
  run: uv run mypy src/openharness
```

**注意**: 当前 `mypy strict=true` 可能有很多现有类型问题，建议先放宽为：
```toml
[tool.mypy]
python_version = "3.11"
strict = false
check_untyped_defs = true
disallow_incomplete_defs = true
warn_return_any = true
```

逐步收紧到 full strict。

---

#### T2.5 Pre-commit Hook 配置

**新建文件**: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
```

**验收标准**:
- [ ] `pre-commit run` 可一次完成所有质量检查
- [ ] 提交前自动格式化和 lint

---

### 2.3 文档体系完善

#### T2.6 架构设计文档

**新建文件**: `docs/ARCHITECTURE.md`

内容大纲:
```
# OpenHarness 架构设计文档

## 1. 设计哲学
   - Model = Driver, Harness = Car
   - 12 章节渐进式架构

## 2. 核心组件
   - Engine（Agent Loop）
   - Tool Registry
   - Permission System
   - Memory System

## 3. 数据流
   - 用户输入 → CLI → QueryEngine → API → Tool Execution → Result
   - 多 Agent 场景的数据流

## 4. 子系统详解（14 个子系统各一节）
   - 每个子系统的职责、接口、关键类

## 5. 扩展机制
   - 如何添加自定义工具
   - 如何添加自定义技能
   - 如何添加插件
```

---

#### T2.7 API 参考文档

**方式**: 使用 Sphinx 或 MkDocs 从 docstring 生成

**最低要求**: 确保所有公共 API 有完整的中文 docstring（含参数说明、返回值、示例）

---

## 🔵 Phase 3: 生态扩展（P3 — 长期规划）

> **目标**: 让 OpenHarness 成为社区驱动的 Agent 工程平台

### 3.1 社区建设

| 行动 | 优先级 | 说明 |
|------|--------|------|
| CONTRIBUTING.md 完善 | 高 | 添加详细的 PR 流程、代码规范、测试要求 |
| Issue 模板优化 | 高 | 已有 bug_report / feature_request，可增加 architecture-proposal |
| 讨论区指南 | 中 | 引导高质量的技术讨论 |
| Roadmap 公开 | 中 | 让社区了解发展方向 |

### 3.2 示例与教程

| 内容 | 形式 | 说明 |
|------|------|------|
| 12 章节对应教程系列 | Markdown | 每章一个实战示例，对齐文章风格 |
| 自定义工具开发指南 | Tutorial | 从零创建一个领域工具 |
| 多 Agent 协作案例 | Showcase | 团队开发、代码审查等场景 |
| Provider 接入指南 | How-to | 添加新的 LLM 后端 |

### 3.3 高级特性探索

| 特性 | 复杂度 | 价值 | 说明 |
|------|--------|------|------|
| **Worktree 隔离增强** | 中 | 高 | Git worktree 与 Agent 会话深度绑定 |
| **流式工具输出** | 中 | 高 | 工具执行过程中的实时进度反馈 |
| **会话迁移** | 高 | 高 | 在不同设备间恢复 Agent 会话 |
| **多模态支持** | 高 | 中 | 图片/音频输入的处理 |
| **分布式 Agent** | 很高 | 中 | 跨机器的 Agent 协作 |

---

## 📋 推荐实施顺序

### 立即可做（今天）

```
T0.1 运行全量测试套件 ← 最重要！验证一切正常
T0.2 运行 Lint 检查
T0.3 版本号同步 (0.1.1 → 0.2.0)
T0.4 更新 CHANGELOG
```

### 本周推荐（Phase 1 核心）

```
Day 1-2: T1.1 缓存微压缩（压缩系统自然演进）
Day 3:   T1.2 Agent 内存管理（多 Agent 基础设施）
Day 4:   T1.3 团队文件增强（协作能力提升）
Day 5:   T2.4-T2.5 CI 增强 + pre-commit
```

### 下周可选（Phase 1 进阶）

```
Day 1-3: T1.4 YOLO 分类器（UX 大幅提升，但复杂度高）
Day 4-5: T1.5 Agent 定义系统（高级定制）
```

### 长期规划（Phase 2-3）

```
Week 3-4: T2.1-T2.3 CI/CD 完善 + 性能基准
Week 5-6: T2.6-T2.7 文档体系
Month 2+: Phase 3 生态扩展
```

---

## 💡 关键决策建议

### 决策 1: 是否现在实现 YOLO 分类器？

| 选项 | 投入 | 收益 | 建议 |
|------|------|------|------|
| **A) 现在做** | 2-3 天 | UX 提升 50%+ | 如果追求极致体验 → 选 A |
| **B) Phase 1 后再做** | 同上 | 同上 | 如果先求稳 → 选 B |
| **C) 只做规则引擎版** | 1 天 | UX 提升 30% | **推荐** ✅ — 平衡投入产出 |

**我的建议**: 选择 C — 先用纯规则引擎实现（无需 ML），覆盖 80% 的常见场景，后续再考虑 ML 增强。

---

### 决策 2: 文档优先还是功能优先？

| 策略 | 适用场景 |
|------|----------|
| **功能优先** | 个人项目 / 内部工具 / 快速迭代 |
| **文档优先** | 开源项目 / 教学目的 / 吸引贡献者 |

**建议**: OpenHarness 定位是开源教学项目 → **功能先行但文档同步更新**。每完成一个功能模块，立即补充对应的 README 章节和测试。

---

### 决策 3: 是否追求 100% 类型安全？

**当前状态**: `mypy strict=true` 但 CI 未运行

**建议**: 分三步走
1. **短期**: CI 加入 mypy（非 strict），修复关键类型错误
2. **中期**: 逐步收紧到 `check_untyped_defs + disallow_incomplete_defs`
3. **长期**: 目标 strict，但对第三方库交互处使用 `type: ignore`

---

## ✅ 总结

### OpenHarness 当前定位

```
🏆 已达成: 首个完整实现 Harness 工程 12 章节的 Python 开源框架
📈 成长方向: 从「功能完整」→「工程成熟」→「生态繁荣」

核心优势:
✅ 架构完整（12/12 章节）
✅ 代码质量高（Ruff + Pydantic + async/await）
✅ 测试充分（~200 用例）
✅ 兼容性好（Claude Code 插件/技能格式）
✅ 多后端支持（Anthropic/OpenAI/Copilot）

待提升:
⚠️ 测试覆盖率未量化
⚠️ CI/CD 可进一步增强
⚠️ 文档可更系统化
⚠️ 版本号需同步
```

### 一句话总结

> **OpenHarness 已经完成了从 0 到 1 的核心架构搭建，下一步应聚焦于「验证稳定性 → 增强高价值功能 → 提升工程成熟度 → 构建社区生态」的渐进式成长路径。**

---

**计划版本**: v1.0
**最后更新**: 2026-04-06
**适用范围**: OpenHarness v0.2.0 及之后的版本规划
