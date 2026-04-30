# 用 OpenClaw 搭建「多 Agent 协作系统」实现计划

## 项目概述

基于用户提供的架构设计文档，结合现有的 `.openclaw` 配置和 `Clawith` 平台，实现一个类脑协作的多 Agent 系统。

## 现状分析

### 已有的基础设施

1. **OpenClaw 配置** (`~/.openclaw/openclaw.json`)
   - 11 个部门/Agent 已配置
   - 多模型供应商：阿里云百炼、火山引擎、自定义端点
   - 可用模型：qwen3.5-plus、qwen3-max、glm-5、kimi-k2.5、MiniMax-M2.5 等
   - 飞书集成已启用

2. **Clawith 平台**
   - 前后端分离架构
   - Agent 消息传递系统
   - 广场(Plaza)功能
   - 督办任务系统
   - 企业知识库

3. **Obsidian PARA 系统**
   - 00-Inbox/：入口
   - 01-Daily/：晨间计划 + 晚间复盘
   - 02-Projects/：进行中的项目
   - 03-Areas/：持续关注的领域
   - 04-Resources/：参考资料
   - 05-Archive/：归档

### 目标架构

```
用户 → main(调度中心) → 8个专业脑区
                         ├─ planner(前额叶) - 规划
                         ├─ analyst(分析皮层) - 分析
                         ├─ writer(语言区) - 写作
                         ├─ builder(运动皮层) - 代码
                         ├─ review(制动器) - 审查
                         ├─ librarian(检索系统) - 资料
                         ├─ learner(海马体) - 学习
                         └─ [可选扩展]
```

## 实施阶段

### 阶段一：基础架构搭建 (P0)

#### 任务 1.1：创建 8 个专业 Agent
- [ ] 创建 planner workspace 和配置
  - SOUL.md：规划师性格定义
  - AGENTS.md：规划工作规则
  - MEMORY.md：规划相关的记忆
- [ ] 创建 analyst workspace 和配置
- [ ] 创建 writer workspace 和配置
- [ ] 创建 builder workspace 和配置
- [ ] 创建 review workspace 和配置
- [ ] 创建 librarian workspace 和配置
- [ ] 创建 learner workspace 和配置

#### 任务 1.2：配置 main 调度中心
- [ ] 修改现有 main Agent 配置
  - 更新 SOUL.md：统一大脑身份
  - 更新 AGENTS.md：调度规则和流程卡制度
  - 更新 MEMORY.md：全局记忆

### 阶段二：通信机制实现 (P0)

#### 任务 2.1：实现 Agent 间消息传递
- [ ] 定义消息协议格式
- [ ] 配置 subagents 允许列表
- [ ] 实现任务委派流程

#### 任务 2.2：实现流程卡制度
- [ ] 设计流程卡数据结构
- [ ] 实现用户审批界面
- [ ] 实现链路执行引擎

### 阶段三：Obsidian 集成 (P1)

#### 任务 3.1：集成现有 Obsidian Skill
- [ ] 确认 vault 路径（当前配置：`/media/xxh/APP/KN`）
- [ ] 验证 obsidian-helper.sh 可用性
- [ ] 测试基本操作：搜索、创建、读取笔记

#### 任务 3.2：开发 Inbox 自动分流 Agent
- [ ] 实现 PARA 分类逻辑
- [ ] 开发 Do/Note/Reference/Drop 决策引擎
- [ ] 实现每日复盘功能

### 阶段四：模型智能分配 (P1)

#### 任务 4.1：实现模型路由策略
- [ ] 配置按角色分配模型
  - main → MiniMax-M2.5（日常调度）
  - librarian → qwen3.5-plus（资料检索）
  - writer → qwen3.5-plus（写作）
  - analyst → glm-5（分析）
  - builder → glm-5（代码）
  - planner → qwen3-max（复杂规划）
  - review → qwen3-max（质量审查）
  - learner → qwen3-max（经验提炼）

### 阶段五：质量保障体系 (P2)

#### 任务 5.1：实现 Review 制动器
- [ ] 配置 review Agent 的严格标准
- [ ] 实现不确定时拒绝的机制
- [ ] 配置置信度报告

#### 任务 5.2：实现断路器机制
- [ ] 实现 3 轮反馈循环上限
- [ ] 实现自动终止和上报

### 阶段六：记忆系统优化 (P2)

#### 任务 6.1：实现分层记忆
- [ ] main MEMORY.md：全局记忆
- [ ] 各专业 Agent MEMORY.md：按需记忆
- [ ] 实现记忆同步机制

#### 任务 6.2：实现选择性学习（learner）
- [ ] 实现高价值变化检测
- [ ] 实现 lesson 沉淀机制
- [ ] 实现提案而非直接修改的规则

## 技术依赖

- OpenClaw 最新版本（已配置）
- Obsidian vault 访问
  - 现有 Skill：`/home/xxh/.openclaw/workspace/skills/obsidian/`
  - 现有脚本：`obsidian-helper.sh`
- LLM API 访问（已配置）
- 飞书 API（已配置）
- obsidian-cli 或 obsidian-helper.sh

## 风险评估

### 高风险
1. **跨 Agent 上下文丢失** - 需要实现持久化上下文传递
2. **模型能力差异** - 不同模型对复杂推理支持度不同
3. **循环依赖** - Agent 间可能形成死循环

### 中风险
1. **Token 预算控制** - 多 Agent 调用可能超出预算
2. **响应延迟** - 多 Agent 链路可能较慢
3. **Obsidian 文件冲突** - 多 Agent 同时写入可能冲突

### 低风险
1. **飞书消息积压** - 需要实现限流
2. **记忆同步不一致** - 需要实现版本控制

## 验证标准

### 功能验证
- [ ] 用户输入任务，main 能正确生成分任务链路
- [ ] 各 Agent 能正确接收和执行委派任务
- [ ] Review 能正确识别质量问题
- [ ] Obsidian Inbox 能正确分流

### 性能验证
- [ ] 单任务链路响应时间 < 30秒
- [ ] 日志记录完整可查
- [ ] Token 使用量可追踪

### 质量验证
- [ ] Review 通过率约 70%（初期）
- [ ] Learner 能沉淀有效 lesson
- [ ] 用户满意度 > 80%

## 实施顺序建议

1. **先跑通 main → planner → review 链路**（最核心）
2. **再扩展到 analyst → writer → review**
3. **然后添加 librarian 和 builder**
4. **最后实现 learner 和 Obsidian 集成**

## 资源估算

- **时间**：约 2-3 周（每天 2-3 小时）
- **Token 消耗**：初期约 $50/周（调试稳定后 $20/周）
- **开发工作量**：约 500-800 行配置 + 100-200 行代码

## 下一步行动

1. 确认是否已有 Clawith 平台账号和组织
2. 确定是否已有 Obsidian vault
3. 选择首先实现的 2-3 个核心 Agent
4. 确定用户审批流程的具体形式

---

**文档版本**：v1.0
**创建日期**：2026-03-23
**状态**：待用户确认