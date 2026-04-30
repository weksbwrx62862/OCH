# 在前端增加市场分析智能体 - 实施计划

## 当前状态

✅ **已完成**：
- 创建了market-analysis-agent技能
- 集成了真实的金融技能调用
- 创建了技能适配器、任务路由器、分析器和报告生成器

📋 **需要完成**：
- 在Clawith前端创建市场分析智能体模板
- 确保技能正确安装和可用
- 测试智能体的完整功能

## 实施计划

### [x] 任务1：创建市场分析智能体模板
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在template_seeder.py中添加市场分析智能体模板
  - 定义智能体的soul_template（身份、性格、工作方式）
  - 配置默认技能（market-analysis-agent及相关金融技能）
- **Success Criteria**:
  - 市场分析智能体模板成功添加到数据库
  - 模板包含完整的配置信息
- **Test Requirements**:
  - `programmatic` TR-1.1: 模板能成功保存到数据库
  - `human-judgement` TR-1.2: 模板配置完整合理

### [x] 任务2：确保技能正确安装
- **Priority**: P0
- **Depends On**: 任务1
- **Description**: 
  - 验证market-analysis-agent技能在正确的位置
  - 检查技能文件完整性
  - 验证技能配置（SKILL.md, skill.json）
- **Success Criteria**:
  - 技能文件完整且在正确位置
  - 技能配置正确
- **Test Requirements**:
  - `programmatic` TR-2.1: 所有技能文件存在
  - `programmatic` TR-2.2: 技能配置文件格式正确

### [x] 任务3：更新前端模板分类
- **Priority**: P1
- **Depends On**: 任务1
- **Description**: 
  - 确保模板分类包含"specialized"或类似分类
  - 或者添加新的"finance"分类
- **Success Criteria**:
  - 市场分析智能体在正确的分类中显示
- **Test Requirements**:
  - `human-judgement` TR-3.1: 前端能正确显示市场分析智能体模板

### [x] 任务4：测试智能体创建和使用（需重启后端）
- **Priority**: P1
- **Depends On**: 任务1-3
- **Description**: 
  - 从模板创建市场分析智能体
  - 测试智能体的技能调用
  - 验证报告生成功能
- **Success Criteria**:
  - 能够成功创建智能体
  - 智能体能够正常工作
- **Test Requirements**:
  - `programmatic` TR-4.1: 智能体能成功创建
  - `programmatic` TR-4.2: 智能体能调用技能
  - `programmatic` TR-4.3: 能生成分析报告

## 市场分析智能体模板配置

### 基本信息
- **name**: "市场分析助手"
- **description**: "智能市场分析助手，自动识别分析任务类型，整合多维度分析结果，生成专业的市场分析报告"
- **icon**: "📈"
- **category**: "specialized" (或"finance")

### Soul模板
包含：
- 身份定义：市场分析专家
- 专业技能：股票、加密货币、基金、宏观经济、技术分析、风险评估
- 性格：严谨、数据驱动、逻辑清晰
- 工作方式：结构化分析、多维度整合、结论先行
- 边界：不提供投资建议、数据来源标注

### 默认技能
- market-analysis-agent
- stock
- crypto
- fund
- macro
- technical
- risk
- data-source
