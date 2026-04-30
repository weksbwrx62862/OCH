# OpenClaw 多脑区架构 + Clawith 平台整合实现计划

## 整合思路

**核心发现**：Clawith 本身就是构建在 OpenClaw 之上的多 Agent 协作平台！两者天然互补：

- **Clawith**：提供 Web UI、管理界面、用户交互、Enterprise 功能
- **OpenClaw**：提供 Agent 运行时、多模型支持、工具调用、Soul/Memory 持久化
- **多脑区架构**：定义 Agent 之间的协作模式和角色分工

## 整合优势

### 1. Clawith 提供的开箱即用功能
- ✅ **Web 管理界面**：Agent 创建、配置、监控
- ✅ **Plaza 广场**：Agent 之间的社交动态
- ✅ **Tasks 督办**：任务分配和追踪
- ✅ **Skills 系统**：Agent 技能管理
- ✅ **Enterprise 功能**：多租户、配额、审批、审计日志
- ✅ **飞书集成**：消息推送（已配置）

### 2. 多脑区架构提供的协作模式
- ✅ **角色分离**：规划/执行/审查不再互相污染
- ✅ **流程卡制度**：用户始终在回路中
- ✅ **质量闸门**：Review Agent 专职审查
- ✅ **持久记忆**：每个 Agent 记住自己的上下文
- ✅ **模型智能分配**：按角色选择合适模型

## 实施阶段

### 阶段一：在 Clawith 中创建 Brain Region Agents (P0)

#### 任务 1.1：创建 8 个脑区 Agent
- [ ] main-dispatch - 调度中心（主入口）
- [ ] planner - 前额叶（规划）
- [ ] analyst - 分析皮层（分析）
- [ ] writer - 语言区（写作）
- [ ] builder - 运动皮层（代码）
- [ ] review - 制动器（审查）
- [ ] librarian - 检索系统（资料）
- [ ] learner - 海马体（学习）

#### 任务 1.2：配置 Brain Region 的 Soul.md
- [ ] 每个 Agent 在 Mind Tab 配置 Soul.md
- [ ] 参考文档中的大五人格配置
- [ ] 定义认知策略和失控风险提醒

#### 任务 1.3：配置 Agent 关系
- [ ] main-dispatch 是所有 Agent 的 Supervisor
- [ ] review 与执行 Agent 是 Colleague
- [ ] planner 与 main-dispatch 紧密协作

### 阶段二：配置 main-dispatch 调度逻辑 (P0)

#### 任务 2.1：配置 main 的 Skills
- [ ] dispatch-skill.md：任务分类和链路分配规则
- [ ] flow-card-skill.md：流程卡生成模板
- [ ] memory-skill.md：全局记忆读取规则

#### 任务 2.2：配置 main 的 Tools
- [ ] send_message_to_agent
- [ ] plaza_* 用于信息共享
- [ ] manage_tasks 用于任务派发

### 阶段三：配置专业 Agent 的 Skills (P1)

#### 任务 3.1：planner Skills
- [ ] planning-skill.md：复杂任务拆解原则

#### 任务 3.2：analyst Skills
- [ ] analysis-skill.md：先证据后结论

#### 任务 3.3：writer Skills
- [ ] writing-skill.md：不为流畅而编造事实

#### 任务 3.4：builder Skills
- [ ] coding-skill.md：最小可用优先

#### 任务 3.5：review Skills
- [ ] review-skill.md：质量闸门检查清单

#### 任务 3.6：librarian Skills
- [ ] search-skill.md：Obsidian PARA 分类

#### 任务 3.7：learner Skills
- [ ] learning-skill.md：高价值变化检测

### 阶段四：Obsidian PARA 集成 (P1)

#### 任务 4.1：配置 librarian 的 Obsidian 访问
- [ ] librarian agent 启用 Obsidian skill
- [ ] 配置 vault 路径：/media/xxh/APP/KN

#### 任务 4.2：实现 Inbox 自动分流
- [ ] inbox-skill.md：Do/Note/Reference/Drop 分类

### 阶段五：模型智能分配 (P1)

#### 任务 5.1：配置模型路由
- [ ] main-dispatch → MiniMax-M2.5
- [ ] librarian → qwen3.5-plus
- [ ] analyst → glm-5
- [ ] review → qwen3-max
- [ ] 其他 → 按需配置

### 阶段六：质量保障与断路器 (P2)

#### 任务 6.1：配置 Review 制动器
- [ ] review agent 的质量标准
- [ ] 不通过时给出具体原因

#### 任务 6.2：实现断路器机制
- [ ] 配置任务最大循环次数：3轮
- [ ] 超时自动终止并上报

## 验证标准

### 功能验证
- [ ] 8个脑区 Agent 都能正常创建和运行
- [ ] main 能正确生成分任务链路
- [ ] 流程卡审批流程正常

### 性能验证
- [ ] 单任务链路响应时间 < 60秒
- [ ] Token 使用量可追踪

## 下一步行动

1. **确认环境**：Clawith 是否已部署并可访问？
2. **选择起点**：先实现 main + planner + review
3. **配置 Obsidian**：确认 vault 路径是否正确

---

**文档版本**：v2.0（整合 Clawith）
**创建日期**：2026-03-23
**状态**：待用户确认