# 删除无用文件 - 实施计划

## 当前状态分析

### 可以删除的文件/目录：

1. **`test_agent.py`**
   - 位置：`/home/xxh/.clawith/data/agents/market_analysis_agent/test_agent.py`
   - 原因：临时创建的测试文件，现在不需要了

2. **`market-analysis-agent/` 目录**
   - 位置：`/home/xxh/.clawith/data/agents/market_analysis_agent/skills/market-analysis-agent/`
   - 原因：功能已整合到finance-assistant中，不再需要独立的技能

3. **`OpenClaw全功能使用指南.md`**（保留）
   - 位置：`/home/xxh/.clawith/data/agents/market_analysis_agent/skills/OpenClaw全功能使用指南.md`
   - 原因：用户要求保留

### 需要保留的文件/目录：

- `state.json` - 智能体状态文件
- `soul.md` - 智能体灵魂文件
- `HEARTBEAT.md` - 智能体心跳文件
- `skills/` 目录下的其他技能（finance-assistant、stock、crypto等）
- `memory/` - 内存目录
- `workspace/` - 工作区目录

## 实施计划

### [ ] 任务1：删除test_agent.py
- **Priority**: P0
- **Depends On**: None
- **Description**: 删除临时测试文件
- **Success Criteria**: test_agent.py已删除

### [ ] 任务2：删除market-analysis-agent目录
- **Priority**: P0
- **Depends On**: None
- **Description**: 删除已整合的技能目录
- **Success Criteria**: market-analysis-agent目录已删除



## 预期成果

- 目录结构更清晰
- 删除了无用文件
- 保留了所有必要的功能
