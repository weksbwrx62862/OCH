# Edict 系统全面逻辑验证 - The Implementation Plan (Decomposed and Prioritized Task List)

## [x] 任务 1: 任务创建功能测试
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 测试任务创建功能的各种场景
  - 验证任务ID生成规则的正确性
  - 验证标题验证逻辑（长度、内容清洗等）
  - 测试有效和无效参数的处理
- **Acceptance Criteria Addressed**: [AC-1]
- **Test Requirements**:
  - `programmatic` TR-1.1: 测试正常任务创建，验证所有字段正确设置
  - `programmatic` TR-1.2: 测试空标题，验证被正确拒绝
  - `programmatic` TR-1.3: 测试过短标题（<6字），验证被正确拒绝
  - `programmatic` TR-1.4: 测试过长标题（>80字），验证被正确截断
  - `programmatic` TR-1.5: 测试包含文件路径、URL的标题，验证被正确清洗
  - `programmatic` TR-1.6: 测试包含特殊字符的标题，验证被正确处理
  - `programmatic` TR-1.7: 测试任务ID生成规则，验证格式正确（JJC-YYYYMMDD-NNN）
- **Notes**: 使用临时测试目录，避免影响生产数据

## [x] 任务 2: 消息分拣逻辑测试
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 测试消息分拣逻辑的正确性
  - 验证闲聊/问答 vs 指令的判断规则
  - 测试各种边界条件
- **Acceptance Criteria Addressed**: [AC-2]
- **Test Requirements**:
  - `programmatic` TR-2.1: 测试简短回复（"好"、"否"等），验证不创建任务
  - `programmatic` TR-2.2: 测试闲聊/问答消息，验证不创建任务
  - `programmatic` TR-2.3: 测试信息查询消息，验证不创建任务
  - `programmatic` TR-2.4: 测试刚好 10 字的消息，验证正确判断
  - `programmatic` TR-2.5: 测试 >10 字且包含动作词的消息，验证创建任务
  - `programmatic` TR-2.6: 测试以"传旨"、"下旨"开头的消息，验证创建任务
  - `programmatic` TR-2.7: 测试对已有话题的追问，验证不创建新任务
  - `programmatic` TR-2.8: 测试包含具体目标或交付物的消息，验证创建任务
- **Notes**: 测试各种真实场景的消息内容

## [x] 任务 3: 状态流转功能测试
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 测试状态流转的所有可能路径
  - 验证状态变更规则的正确性
  - 测试流转记录的更新
- **Acceptance Criteria Addressed**: [AC-3]
- **Test Requirements**:
  - `programmatic` TR-3.1: 测试 Dispatch → Planning 的状态流转
  - `programmatic` TR-3.2: 测试 Planning → Review 的状态流转
  - `programmatic` TR-3.3: 测试 Review → Assigned 的状态流转
  - `programmatic` TR-3.4: 测试 Assigned → Doing 的状态流转
  - `programmatic` TR-3.5: 测试 Doing → Done 的状态流转
  - `programmatic` TR-3.6: 测试状态流转时的流转记录正确更新
  - `programmatic` TR-3.7: 测试状态流转时的时间戳正确更新
  - `programmatic` TR-3.8: 测试无效的状态变更，验证被正确拒绝
- **Notes**: 确保覆盖所有可能的状态转换路径

## [x] 任务 4: 条件判断逻辑测试
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 测试各种条件判断逻辑
  - 验证组织映射的正确性
  - 测试文本清洗功能
- **Acceptance Criteria Addressed**: [AC-4]
- **Test Requirements**:
  - `programmatic` TR-4.1: 测试组织到Agent ID的映射，验证正确
  - `programmatic` TR-4.2: 测试状态到Agent ID的映射，验证正确
  - `programmatic` TR-4.3: 测试文本清洗功能，验证文件路径被正确移除
  - `programmatic` TR-4.4: 测试文本清洗功能，验证URL被正确移除
  - `programmatic` TR-4.5: 测试文本清洗功能，验证Conversation元数据被正确移除
  - `programmatic` TR-4.6: 测试文本清洗功能，验证前缀被正确移除
  - `programmatic` TR-4.7: 测试文本清洗功能，验证过长文本被正确截断
  - `programmatic` TR-4.8: 测试Agent ID推断逻辑，验证环境变量优先级
  - `programmatic` TR-4.9: 测试Agent ID推断逻辑，验证从工作目录推断
- **Notes**: 测试各种条件判断的边界条件

## [x] 任务 5: 子任务管理功能测试
- **Priority**: P1
- **Depends On**: None
- **Description**: 
  - 测试子任务的创建、更新和删除
  - 验证子任务状态管理
  - 测试子任务与父任务的关联
- **Acceptance Criteria Addressed**: [AC-5]
- **Test Requirements**:
  - `programmatic` TR-5.1: 测试子任务创建，验证正确关联到父任务
  - `programmatic` TR-5.2: 测试子任务状态更新，验证正确反映在父任务上
  - `programmatic` TR-5.3: 测试子任务标记为完成，验证正确处理
  - `programmatic` TR-5.4: 测试多个子任务的管理，验证正确处理
  - `programmatic` TR-5.5: 测试子任务描述的更新，验证正确保存
- **Notes**: 测试子任务的各种操作场景

## [x] 任务 6: 进度汇报功能测试
- **Priority**: P1
- **Depends On**: None
- **Description**: 
  - 测试进度汇报功能
  - 验证实时状态更新
  - 测试计划清单管理
  - 测试历史记录
- **Acceptance Criteria Addressed**: [AC-6]
- **Test Requirements**:
  - `programmatic` TR-6.1: 测试进度汇报，验证当前动态被正确更新
  - `programmatic` TR-6.2: 测试计划清单管理，验证正确保存
  - `programmatic` TR-6.3: 测试进度更新的频率限制，验证正确处理
  - `programmatic` TR-6.4: 测试历史记录管理，验证正确保存
  - `programmatic` TR-6.5: 测试进度汇报不改变任务状态，验证只更新当前动态
  - `programmatic` TR-6.6: 测试进度汇报超过最大条数，验证正确处理
- **Notes**: 测试进度汇报的各种使用场景

## [x] 任务 7: 任务取消/暂停/恢复功能测试
- **Priority**: P1
- **Depends On**: None
- **Description**: 
  - 测试任务取消功能
  - 测试任务暂停功能
  - 测试任务恢复功能
  - 验证状态回滚逻辑
- **Acceptance Criteria Addressed**: [AC-7]
- **Test Requirements**:
  - `programmatic` TR-7.1: 测试任务取消，验证状态正确变更为 Cancelled
  - `programmatic` TR-7.2: 测试任务暂停，验证状态正确变更为 Blocked
  - `programmatic` TR-7.3: 测试任务从 Blocked 恢复，验证状态正确恢复
  - `programmatic` TR-7.4: 测试取消/暂停时的备注，验证正确保存
  - `programmatic` TR-7.5: 测试取消/暂停时的流转记录，验证正确记录
  - `programmatic` TR-7.6: 测试从终端状态恢复，验证被正确拒绝
- **Notes**: 测试各种状态下的取消/暂停/恢复操作

## [x] 任务 8: 文件锁机制测试
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 测试文件锁机制
  - 验证并发操作的数据一致性
  - 测试锁的正确释放
- **Acceptance Criteria Addressed**: [AC-8]
- **Test Requirements**:
  - `programmatic` TR-8.1: 测试原子读取，验证数据一致性
  - `programmatic` TR-8.2: 测试原子写入，验证数据一致性
  - `programmatic` TR-8.3: 测试原子更新，验证数据一致性
  - `programmatic` TR-8.4: 测试多线程并发写入，验证数据不损坏
  - `programmatic` TR-8.5: 测试异常情况下锁的释放，验证不会死锁
  - `programmatic` TR-8.6: 测试锁的超时机制，验证正确处理
- **Notes**: 使用多线程/多进程测试并发场景

## [x] 任务 9: 看板更新功能测试
- **Priority**: P1
- **Depends On**: None
- **Description**: 
  - 测试看板更新功能
  - 验证任务源同步
  - 测试实时数据刷新
- **Acceptance Criteria Addressed**: [AC-9]
- **Test Requirements**:
  - `programmatic` TR-9.1: 测试任务变更后看板更新，验证正确同步
  - `programmatic` TR-9.2: 测试实时数据刷新，验证正确执行
  - `programmatic` TR-9.3: 测试刷新脚本调用，验证不阻塞
  - `programmatic` TR-9.4: 测试刷新失败处理，验证不影响主流程
  - `programmatic` TR-9.5: 测试数据文件不存在，验证正确处理
- **Notes**: 测试看板更新的各种场景

## [x] 任务 10: 错误处理和异常情况测试
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 测试各种错误处理逻辑
  - 验证异常情况的处理
  - 测试系统在异常输入下的稳定性
- **Acceptance Criteria Addressed**: [AC-10]
- **Test Requirements**:
  - `programmatic` TR-10.1: 测试数据文件不存在，验证正确处理
  - `programmatic` TR-10.2: 测试数据文件格式错误，验证正确处理
  - `programmatic` TR-10.3: 测试权限问题，验证正确处理
  - `programmatic` TR-10.4: 测试任务不存在，验证正确返回错误
  - `programmatic` TR-10.5: 测试无效的状态，验证正确拒绝
  - `programmatic` TR-10.6: 测试无效的组织，验证正确拒绝
  - `programmatic` TR-10.7: 测试系统在异常输入下不崩溃，验证稳定性
- **Notes**: 测试各种异常场景

## [x] 任务 11: 运行现有测试套件
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 运行项目现有的 pytest 测试套件
  - 验证现有测试用例的执行结果
  - 记录发现的问题
- **Acceptance Criteria Addressed**: [AC-1, AC-3, AC-8, AC-9]
- **Test Requirements**:
  - `programmatic` TR-11.1: 运行 test_kanban.py，验证所有测试通过
  - `programmatic` TR-11.2: 运行 test_file_lock.py，验证所有测试通过
  - `programmatic` TR-11.3: 运行 test_server.py，验证所有测试通过
  - `programmatic` TR-11.4: 运行 test_e2e_kanban.py，验证所有测试通过
  - `human-judgement` TR-11.5: 记录现有测试用例的覆盖率
- **Notes**: 在执行新测试前先运行现有测试

## [x] 任务 12: 生成测试报告
- **Priority**: P2
- **Depends On**: [Task 1, Task 2, Task 3, Task 4, Task 5, Task 6, Task 7, Task 8, Task 9, Task 10, Task 11]
- **Description**: 
  - 汇总所有测试结果
  - 生成详细的测试报告
  - 包含测试用例、执行结果、发现的问题及修复建议
- **Acceptance Criteria Addressed**: [AC-11]
- **Test Requirements**:
  - `human-judgement` TR-12.1: 测试报告包含所有测试用例的执行结果
  - `human-judgement` TR-12.2: 测试报告包含发现的问题列表
  - `human-judgement` TR-12.3: 测试报告包含修复建议
  - `human-judgement` TR-12.4: 测试报告格式规范、内容完整
- **Notes**: 测试报告应清晰、详细、易于理解
