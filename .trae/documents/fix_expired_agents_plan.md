# 修复仪表盘显示过期数字员工问题 - 实施计划

## [ ] 任务 1: 修复后端 agents API 不过滤已过期数字员工的问题
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在 `list_agents` 函数中添加 `is_expired == False` 的过滤条件
  - 需要在两个查询分支中都添加这个过滤（管理员和普通用户）
- **Success Criteria**:
  - 过期的数字员工不再出现在 API 响应中
  - 未过期的数字员工正常显示
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证 API 返回的 agents 列表中 `is_expired` 字段均为 `False`
  - `human-judgement` TR-1.2: 检查仪表盘是否不再显示已过期的数字员工
- **Notes**: 需要在 `backend/app/api/agents.py` 文件中修改
