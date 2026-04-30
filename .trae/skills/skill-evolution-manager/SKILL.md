---
name: skill-evolution-manager
description: 专门用于在对话结束时，根据用户反馈和对话内容总结优化并迭代现有 Skills 的核心工具。它通过吸取对话中的"精华"（如成功的解决方案、失败的教训、特定的代码规范）来持续演进 Skills 库。
license: MIT
---

# Skill Evolution Manager

这是整个 AI 技能系统的"进化中枢"。

## 核心职责

1. **复盘诊断 (Session Review)**：在对话结束时，分析所有被调用的 Skill 的表现。
2. **经验提取 (Experience Extraction)**：将非结构化的用户反馈转化为结构化的 JSON 数据。
3. **智能缝合 (Smart Stitching)**：将沉淀的经验自动写入 `SKILL.md`。

## 使用场景

**Trigger**: 
- `/evolve`
- "复盘一下刚才的对话"
- "把这个经验保存到 Skill 里"

## 工作流 (The Evolution Workflow)

### 1. 经验复盘 (Review & Extract)
当用户触发复盘时，Agent 必须执行：
1. **扫描上下文**：找出用户不满意的点或满意的点
2. **定位 Skill**：确定是哪个 Skill 需要进化
3. **生成 JSON**

### 2. 经验持久化 (Persist)
Agent 调用 `scripts/merge_evolution.py`

### 3. 文档缝合 (Stitch)
Agent 调用 `scripts/smart_stitch.py`

## 最佳实践

- **不要直接修改 SKILL.md 的正文**：所有的经验修正应通过 `evolution.json` 通道进行
- **多 Skill 协同**：如果一次对话涉及多个 Skill，请依次为每个 Skill 执行上述流程
