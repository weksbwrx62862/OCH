# 添加市场分析助手到数据库 - 实施计划

## 问题分析

智能体在前端不显示的原因：
- 我们只在文件系统中创建了智能体目录
- 但前端显示的智能体是从数据库中读取的
- 需要在数据库中创建Agent记录

## 解决方案

创建一个Python脚本来：
1. 连接数据库
2. 查询platform_admin用户
3. 创建Agent记录
4. 创建Participant记录
5. 创建AgentPermission记录
6. 将文件系统的目录重命名为正确的UUID

## 实施计划

### [ ] 任务1：创建数据库添加脚本
- **Priority**: P0
- **Depends On**: None
- **Description**: 创建Python脚本，将市场分析助手添加到数据库
- **Success Criteria**: 脚本创建成功

### [ ] 任务2：执行脚本添加到数据库
- **Priority**: P0
- **Depends On**: 任务1
- **Description**: 执行脚本，在数据库中创建Agent记录
- **Success Criteria**: Agent记录成功创建

### [ ] 任务3：验证前端显示
- **Priority**: P0
- **Depends On**: 任务2
- **Description**: 验证智能体在前端显示
- **Success Criteria**: 前端可以看到"市场分析助手"
