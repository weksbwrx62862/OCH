# EDICT任务流程异常检查与修复计划

## [ ] 任务1：检查Gateway服务状态
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 检查Gateway服务是否正常启动
  - 验证Gateway服务的运行状态和端口
  - 确认Gateway服务与EDICT系统的连接
- **Success Criteria**:
  - Gateway服务正常运行
  - EDICT系统能够成功连接到Gateway
  - 任务能够正常派发
- **Test Requirements**:
  - `programmatic` TR-1.1: Gateway服务进程存在且监听指定端口
  - `programmatic` TR-1.2: EDICT系统能够成功调用Gateway API
- **Notes**: 从日志中看到"自动派发跳过: Gateway 未启动"的警告，这是任务无法执行的主要原因

## [ ] 任务2：检查任务状态流转配置
- **Priority**: P1
- **Depends On**: 任务1
- **Description**:
  - 验证TaskState枚举和状态流转配置
  - 检查STATE_TRANSITIONS和STATE_AGENT_MAP配置
  - 确认调度中心到规划部的状态流转路径
- **Success Criteria**:
  - 状态流转配置正确
  - 任务能够按照预定流程从Dispatch状态流转到Planning状态
  - 每个状态都正确映射到对应的Agent
- **Test Requirements**:
  - `programmatic` TR-2.1: 状态流转路径符合预期
  - `programmatic` TR-2.2: 状态到Agent的映射正确
- **Notes**: 确保状态流转配置与实际业务流程一致

## [ ] 任务3：检查调度工作器运行状态
- **Priority**: P1
- **Depends On**: 任务1
- **Description**:
  - 检查DispatchWorker是否正常运行
  - 验证Redis Streams连接和事件消费
  - 确认OpenClaw CLI调用配置
- **Success Criteria**:
  - DispatchWorker正常运行
  - 能够从Redis Streams消费task.dispatch事件
  - 能够成功调用OpenClaw CLI执行agent任务
- **Test Requirements**:
  - `programmatic` TR-3.1: DispatchWorker进程存在且运行
  - `programmatic` TR-3.2: 能够成功消费和处理dispatch事件
- **Notes**: 检查Redis连接配置和OpenClaw CLI路径

## [ ] 任务4：检查任务JJC-20260311-001的具体状态
- **Priority**: P2
- **Depends On**: 任务1, 任务2, 任务3
- **Description**:
  - 查看任务JJC-20260311-001的详细状态
  - 检查任务的flow_log和progress_log
  - 分析任务卡在分拣状态的原因
- **Success Criteria**:
  - 任务状态信息完整
  - 能够识别任务卡住的具体原因
  - 能够手动触发任务继续流转
- **Test Requirements**:
  - `programmatic` TR-4.1: 任务状态信息可访问
  - `human-judgement` TR-4.2: 任务卡住原因分析准确
- **Notes**: 重点关注任务的当前状态和流转历史

## [ ] 任务5：修复任务流程异常并验证
- **Priority**: P0
- **Depends On**: 任务1, 任务2, 任务3, 任务4
- **Description**:
  - 根据前面的分析结果，修复任务流程中的异常
  - 重启相关服务确保修复生效
  - 验证任务能够正常从Dispatch状态流转到后续状态
- **Success Criteria**:
  - 任务JJC-20260311-001能够正常继续执行
  - 新创建的任务能够正常流转
  - 整个任务流程恢复正常
- **Test Requirements**:
  - `programmatic` TR-5.1: 任务状态能够正常流转
  - `programmatic` TR-5.2: 新任务能够正常创建和执行
- **Notes**: 确保修复后系统能够稳定运行

## [ ] 任务6：建立任务流程监控机制
- **Priority**: P2
- **Depends On**: 任务5
- **Description**:
  - 建立任务流程监控机制
  - 设置关键节点的监控告警
  - 完善日志记录，便于问题排查
- **Success Criteria**:
  - 监控机制能够及时发现任务流程异常
  - 告警机制能够在任务卡住时及时通知
  - 日志记录足够详细，便于问题定位
- **Test Requirements**:
  - `programmatic` TR-6.1: 监控机制能够检测到任务流程异常
  - `human-judgement` TR-6.2: 日志记录清晰完整
- **Notes**: 建立长期的监控和维护机制，防止类似问题再次发生