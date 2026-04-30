# 移动金融技能到市场分析智能体 - 实施计划

## 当前状态

**源技能目录**：`/home/xxh/.clawith/data/agents/594e34f8-cdef-4774-811b-026f4a61bdeb/skills/`
**目标技能目录**：`/home/xxh/.clawith/data/agents/market_analysis_agent/skills/`

**金融相关技能**：
- stock (股票分析)
- crypto (加密货币分析)
- fund (基金分析)
- macro (宏观经济分析)
- technical (技术分析)
- risk (风险评估)
- data-source (数据源管理)
- finance-assistant (金融助手)
- analysis (分析报告)
- portfolio (组合管理)
- sentiment (舆情分析)

## 实施计划

### [x] 任务1：移动金融技能到目标目录
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 将所有金融相关技能从源目录移动到目标目录
  - 保持技能目录结构完整
  - 复制requirements.txt文件
- **Success Criteria**:
  - 所有金融技能都已移动到目标目录
  - 目录结构保持完整
- **Test Requirements**:
  - `programmatic` TR-1.1: 所有金融技能目录存在于目标位置
  - `programmatic` TR-1.2: requirements.txt文件已复制

### [x] 任务2：重新创建market-analysis-agent技能
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 在目标技能目录中重新创建market-analysis-agent技能
  - 包含完整的技能文件：SKILL.md、skill.json、scripts目录
- **Success Criteria**:
  - market-analysis-agent技能完整存在于目标目录
  - 所有技能文件都已创建
- **Test Requirements**:
  - `programmatic` TR-2.1: market-analysis-agent目录及其文件存在
  - `programmatic` TR-2.2: 技能文件内容完整

### [x] 任务3：更新skill_adapter.py中的技能路径
- **Priority**: P0
- **Depends On**: 任务2
- **Description**:
  - 更新skill_adapter.py中的技能脚本路径
  - 确保技能调用正确指向新的技能位置
- **Success Criteria**:
  - skill_adapter.py中的技能路径已更新
  - 技能调用能够正确找到目标技能
- **Test Requirements**:
  - `programmatic` TR-3.1: skill_adapter.py中的路径已更新
  - `programmatic` TR-3.2: 技能调用测试通过

### [/] 任务4：验证智能体功能
- **Priority**: P1
- **Depends On**: 任务3
- **Description**:
  - 运行测试脚本验证智能体功能
  - 测试各种分析类型
  - 验证技能调用是否正常
- **Success Criteria**:
  - 智能体能够正常启动
  - 各种分析类型测试通过
  - 技能调用正常工作
- **Test Requirements**:
  - `programmatic` TR-4.1: 智能体启动测试通过
  - `programmatic` TR-4.2: 股票分析测试通过
  - `programmatic` TR-4.3: 加密货币分析测试通过
  - `programmatic` TR-4.4: 综合分析测试通过

## 预期成果

- 所有金融技能已成功移动到市场分析智能体目录
- market-analysis-agent技能重新创建完成
- 智能体能够正常调用所有金融技能
- 各种分析类型测试通过
- 智能体功能完整可用
