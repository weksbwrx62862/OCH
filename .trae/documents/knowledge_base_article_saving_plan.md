# 微信公众号文章知识库沉淀解决方案计划

## 问题分析

### 当前问题
1. **微信公众号链接无法直接访问**：直接访问微信公众号链接会返回"参数错误"，微信有反爬虫机制
2. **情报中心抓取失败**：之前使用 `wechat-article-reader` 技能时失败，因为缺少 Playwright 浏览器依赖
3. **obsidian_integration.py 不存在**：系统中缺少这个外部脚本文件

### 好消息
✅ 系统已经通过 Web Search 成功获取到了文章内容！

## 解决方案

### 方案概述
既然系统已经获取到了文章内容，我们可以直接将其保存到知识库中，而不需要再次尝试抓取微信链接。

### 知识库存储位置
根据代码分析，知识库有两个存储位置：
1. **企业级知识库**：`WORKSPACE_ROOT / "enterprise_info" / "knowledge_base"`（所有智能体共享）
2. **代理级知识库**：`WORKSPACE_ROOT / {agent_id} / "workspace" / "knowledge_base"`（单个智能体专用）

### 实施步骤

#### [ ] 任务 1：整理并格式化文章内容
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 从 Web Search 获取的内容中提取文章标题和正文
  - 将内容格式化为 Markdown 格式
  - 添加合适的标题层级和结构
- **Success Criteria**:
  - 文章内容完整提取
  - Markdown 格式正确
  - 包含文章标题、正文和必要的元数据
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证文章内容完整性
  - `human-judgement` TR-1.2: 检查 Markdown 格式是否易读
- **Notes**: 使用系统已经获取到的文章内容

#### [ ] 任务 2：创建知识库保存脚本
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**: 
  - 创建一个 Python 脚本来保存文章到知识库
  - 支持保存到企业级知识库
  - 支持自动生成文件名（基于文章标题）
  - 添加 Front Matter（标题、标签、创建时间等）
- **Success Criteria**:
  - 脚本可以正常运行
  - 文章成功保存到知识库目录
  - 文件格式正确（Markdown + Front Matter）
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证脚本执行成功
  - `programmatic` TR-2.2: 验证文件已创建
  - `human-judgement` TR-2.3: 检查文件内容格式
- **Notes**: 使用 `_write_file` 函数的逻辑作为参考

#### [ ] 任务 3：执行保存操作
- **Priority**: P0
- **Depends On**: 任务 2
- **Description**: 
  - 运行保存脚本
  - 将格式化后的文章保存到企业级知识库
  - 验证保存结果
- **Success Criteria**:
  - 文章成功保存到知识库
  - 可以通过知识库搜索工具找到文章
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证文件存在于知识库目录
  - `human-judgement` TR-3.2: 验证文章内容完整
- **Notes**: 保存到 `enterprise_info/knowledge_base` 目录

#### [ ] 任务 4：（可选）修复调度中心问题
- **Priority**: P1
- **Depends On**: None
- **Description**: 
  - 分析调度中心分配任务失败的原因
  - 检查调度中心的 LLM 额度和配置
  - 修复可能存在的问题
- **Success Criteria**:
  - 调度中心可以正常分配任务
  - 情报中心可以正常执行任务
- **Test Requirements**:
  - `programmatic` TR-4.1: 验证调度中心状态正常
  - `programmatic` TR-4.2: 验证 LLM 额度充足
- **Notes**: 参考 `fix_quota_issues.py` 脚本

## 技术细节

### 文章信息
- **标题**: 不用API，为你的OpenClaw装上"超级记忆大脑"，自动防错、多技能协同工作，SkillHub一行命令安装
- **URL**: https://mp.weixin.qq.com/s/ZMpPZm21YEJ4CMifqwslMQ
- **来源**: 微信公众号

### 知识库文件结构
```
enterprise_info/
└── knowledge_base/
    └── 不用API-为你的OpenClaw装上超级记忆大脑.md
```

### Front Matter 格式
```markdown
---
title: 不用API，为你的OpenClaw装上"超级记忆大脑"
tags: [OpenClaw, SkillHub, Ontology, AI, 知识库]
created: 2026-04-04
source: https://mp.weixin.qq.com/s/ZMpPZm21YEJ4CMifqwslMQ
---

[文章内容]
```

## 预期结果

完成本计划后，您将获得：
1. ✅ 文章内容已完整保存到知识库
2. ✅ 文章可以通过知识库搜索工具检索
3. ✅ 文章格式良好，易于阅读和管理
4. ✅ （可选）调度中心问题得到修复
