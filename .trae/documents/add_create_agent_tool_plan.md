# 添加create_agent工具到agent_tools.py - 实施计划

## 问题分析

`create_agent`工具在`tool_seeder.py`中定义了（第522-550行），但在`agent_tools.py`的`AGENT_TOOLS`列表中没有实现，导致报错"Unknown tool: create_agent"。

## 实施计划

### [ ] 任务1：在agent_tools.py中添加create_agent工具定义
- **Priority**: P0
- **Depends On**: None
- **Description**: 在AGENT_TOOLS列表中添加create_agent工具的OpenAI函数格式定义
- **Success Criteria**: AGENT_TOOLS包含create_agent工具定义

### [ ] 任务2：实现create_agent工具的执行逻辑
- **Priority**: P0
- **Depends On**: 任务1
- **Description**: 实现create_agent工具的执行函数，调用backend/app/api/agents.py中的create_agent API
- **Success Criteria**: create_agent工具可以正常创建智能体

### [ ] 任务3：测试create_agent工具
- **Priority**: P0
- **Depends On**: 任务2
- **Description**: 测试create_agent工具是否能正常工作
- **Success Criteria**: create_agent工具可以成功创建智能体
