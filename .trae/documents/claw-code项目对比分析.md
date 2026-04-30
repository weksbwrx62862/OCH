# Claw Code 两个项目对比分析报告

## 1. 项目概述

### 1.1 claw-code-main
- **定位**: 官方的 Claw Code 公共 Rust 实现
- **主要特点**: 是 `claw` CLI 代理工具的标准实现
- **仓库**: ultraworkers/claw-code

### 1.2 claw-code-parity-main
- **定位**: 重写项目（Rewriting Project）
- **主要特点**: 强调由 "lobsters/claws"（AI）自主维护，而非传统人工开发团队
- **社区关注度**: 历史上最快达到 50K stars 的仓库（仅用 2 小时）

---

## 2. 主要文档差异

### 2.1 README.md 差异

#### claw-code-main
- 简洁的技术文档风格
- 明确说明 `rust/` 目录是规范的 Rust 工作空间
- 重点介绍快速入门指南和文档地图
- 没有关于 "AI 自主维护" 的叙事

#### claw-code-parity-main
- 更注重项目的故事性和社区宣传
- 开篇强调 "50K stars 里程碑"
- 详细描述 "Backstory"（背景故事），解释项目如何由 AI 自主维护
- 提到 "Python 移植工作" 作为重点
- 包含更多社交媒体和社区链接

### 2.2 ROADMAP.md 差异

两个项目的 roadmap 基本框架相同，但 **claw-code-main** 的完成度更高：

#### claw-code-main 的已完成项目（P0 级别）
- ✅ 隔离 `render_diff_report` 测试到 tmpdir
- ✅ 扩展 GitHub CI 到工作空间级别的验证
- ✅ 添加发布级别的二进制工作流
- ✅ 添加容器优先的测试/运行文档
- ✅ 在入门文档中突出 `doctor` / 预检查诊断
- ✅ 自动化 CI 中的品牌/源残留检查
- ✅ 消除首次运行帮助/构建路径中的警告垃圾信息
- ✅ 将 `doctor` 从斜杠命令提升为顶级 CLI 入口点
- ✅ 使机器可读的状态命令真正机器可读
- ✅ 统一用户输出中的旧版 config/skill 命名空间
- ✅ 在 inventory 命令上尊重 JSON 输出
- ✅ 审计整个 CLI 表面的 `--output-format` 契约

#### claw-code-parity-main 的 P0 项目
- 大部分项目仍处于待完成状态（flaky、needs、current 等状态）
- 进度明显落后于 claw-code-main

---

## 3. 代码实现差异

### 3.1 目录结构差异

#### claw-code-main 独有文件
- `Containerfile` - 容器化支持文件
- `docs/` - 完整的文档目录
- `.github/scripts/` - GitHub Actions 脚本
- `.github/workflows/release.yml` - 发布工作流
- `rust/.claw/` - Claw 特定配置目录
- `rust/crates/runtime/src/branch_lock.rs` - 分支锁功能

#### claw-code-parity-main 独有文件
- 新增测试文件：
  - `rust/crates/runtime/tests/reliability_integration.rs`
  - `rust/crates/runtime/tests/runtime_workflows.rs`
  - `rust/crates/runtime/tests/worker_lane_hook_task_config_integration.rs`
- 新增 CLI 模块：
  - `rust/crates/rusty-claude-cli/src/app.rs`
  - `rust/crates/rusty-claude-cli/src/args.rs`

### 3.2 Rust 代码差异

#### main.rs 差异
- **claw-code-main**: 更完整的输出格式支持，包括 `output_format` 参数
- **claw-code-parity-main**: 简化了一些接口，移除了部分 JSON 输出处理函数
- 导入语句的组织方式不同，代码结构略有调整

#### 其他关键差异
- API 模块（`api/`）有多处实现差异
- Runtime 模块的多个文件存在差异（`lane_events.rs`、`lib.rs`、`lsp_client.rs` 等）
- CLI 命令处理逻辑有不同程度的简化

---

## 4. 项目定位与目标差异总结

### 4.1 claw-code-main
**技术优先，功能完整**
- 作为官方规范实现，注重代码质量和功能完整性
- CI/CD 流程完善，有发布工作流
- 文档齐全，包含容器化支持
- Roadmap 完成度高，是更成熟的版本

### 4.2 claw-code-parity-main
**社区优先，故事驱动**
- 强调 AI 自主开发的叙事
- 社区关注度高，star 增长快
- 代码实现相对简化
- 有额外的测试文件，可能在进行某些特定方向的探索

---

## 5. 建议

### 对于开发者
- **如果需要稳定、功能完整的版本**: 使用 `claw-code-main`
- **如果对 AI 自主开发实验感兴趣**: 可以关注 `claw-code-parity-main` 的进展

### 对于贡献者
- 两个项目有不同的侧重点，选择符合自己兴趣方向的仓库进行贡献
- `claw-code-main` 更适合传统的代码贡献
- `claw-code-parity-main` 可能更适合实验性和探索性的工作
