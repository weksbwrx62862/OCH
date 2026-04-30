# 整合market-analysis-agent到finance-assistant - 实施计划

## 整合背景

**现状**：
- finance-assistant：快速查询，简单输出
- market-analysis-agent：深度分析，结构化报告

**问题**：
- 两个技能功能有重叠（意图识别、任务路由）
- 用户需要选择使用哪个技能，体验不统一

**目标**：
- 整合两个技能，提供统一入口
- 支持快速查询和深度分析两种模式
- 保留各自优势
- **不使用模拟模式，只使用真实技能**

## 实施计划

### [ ] 任务1：分析现有代码结构
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 详细分析两个技能的代码结构
  - 找出可复用的模块
  - 确定整合架构
- **Success Criteria**:
  - 完成代码结构分析
  - 确定整合方案
- **Test Requirements**:
  - `human-judgement` TR-1.1: 整合方案清晰可行

### [ ] 任务2：创建统一的assistant.py
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 在finance-assistant中创建新的assistant.py
  - 整合market-analysis-agent的功能
  - 支持两种模式：
    - 快速查询模式（原finance-assistant）
    - 深度分析模式（原market-analysis-agent）
  - 自动识别用户意图，选择合适模式
  - **不使用模拟模式，直接调用真实技能**
- **Success Criteria**:
  - 新的assistant.py能正常工作
  - 支持两种模式
- **Test Requirements**:
  - `programmatic` TR-2.1: 快速查询功能正常
  - `programmatic` TR-2.2: 深度分析功能正常
  - `programmatic` TR-2.3: 模式自动识别正常

### [ ] 任务3：整合任务路由器
- **Priority**: P1
- **Depends On**: 任务2
- **Description**:
  - 将task_router.py整合到finance-assistant
  - 统一意图识别逻辑
  - 优化关键词匹配
- **Success Criteria**:
  - 意图识别准确
  - 路由逻辑清晰
- **Test Requirements**:
  - `programmatic` TR-3.1: 股票分析识别准确
  - `programmatic` TR-3.2: 加密货币分析识别准确
  - `programmatic` TR-3.3: 深度分析识别准确

### [ ] 任务4：整合报告生成器
- **Priority**: P1
- **Depends On**: 任务3
- **Description**:
  - 将report_generator.py整合到finance-assistant
  - 支持Markdown格式输出
  - 优化报告结构
- **Success Criteria**:
  - 能生成结构化报告
  - 报告格式美观
- **Test Requirements**:
  - `programmatic` TR-4.1: 报告包含所有必要部分
  - `human-judgement` TR-4.2: 报告格式清晰易读

### [ ] 任务5：整合技能适配器（去掉模拟模式）
- **Priority**: P1
- **Depends On**: 任务4
- **Description**:
  - 将skill_adapter.py整合到finance-assistant
  - **只保留真实技能调用，移除模拟模式**
  - 保留多技能协同功能
- **Success Criteria**:
  - 技能调用正常
  - 不使用模拟模式
- **Test Requirements**:
  - `programmatic` TR-5.1: 技能调用成功
  - `programmatic` TR-5.2: 无模拟模式代码

### [ ] 任务6：更新SKILL.md和配置文件
- **Priority**: P2
- **Depends On**: 任务5
- **Description**:
  - 更新finance-assistant的SKILL.md
  - 更新skill.json
  - 添加使用说明
- **Success Criteria**:
  - 文档完整准确
  - 配置正确
- **Test Requirements**:
  - `human-judgement` TR-6.1: 文档清晰易读
  - `human-judgement` TR-6.2: 配置正确

### [ ] 任务7：全面测试和验证
- **Priority**: P2
- **Depends On**: 任务6
- **Description**:
  - 测试快速查询功能
  - 测试深度分析功能
  - 测试两种模式自动切换
  - 性能测试
- **Success Criteria**:
  - 所有测试通过
  - 性能满足要求
- **Test Requirements**:
  - `programmatic` TR-7.1: 快速查询测试通过
  - `programmatic` TR-7.2: 深度分析测试通过
  - `programmatic` TR-7.3: 模式切换测试通过

## 整合架构设计

### 统一入口
```
finance-assistant/
├── assistant.py (统一入口)
├── task_router.py (任务路由器)
├── report_generator.py (报告生成器)
├── skill_adapter.py (技能适配器 - 无模拟模式)
└── scripts/ (原有脚本保留)
```

### 使用模式

**快速查询模式**（触发词：查、价格、多少钱、报价、行情、股价、走势）
- "贵州茅台现在多少钱"
- "比特币价格"
- "最近CPI数据"

**深度分析模式**（触发词：分析、投资价值、策略、风险评估、投资建议）
- "分析贵州茅台的投资价值"
- "2024年A股投资策略"
- "比特币风险评估"

## 预期成果

- 统一的金融助手入口
- 支持快速查询和深度分析两种模式
- 自动识别用户意图，选择合适模式
- 保留所有原有功能
- **只使用真实技能，不使用模拟模式**
- 更好的用户体验
