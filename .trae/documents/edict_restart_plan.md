# Edict 项目重新运行计划

## [ ] 任务 1: 检查 OpenClaw 运行状态
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 检查 OpenClaw 网关服务是否正在运行
  - 验证 OpenClaw 配置是否正确
  - 确认所有 Agent 已正确注册
- **Success Criteria**:
  - OpenClaw 网关服务在端口 18789 运行
  - 所有 Edict Agent 已正确注册
- **Test Requirements**:
  - `programmatic` TR-1.1: 测试 OpenClaw 网关服务状态
  - `programmatic` TR-1.2: 验证 Agent 注册状态
- **Notes**: 参考 README 中的排查步骤

## [ ] 任务 2: 启动数据刷新循环
- **Priority**: P0
- **Depends On**: Task 1
- **Description**:
  - 启动 `scripts/run_loop.sh` 脚本
  - 验证数据刷新循环正常运行
- **Success Criteria**:
  - 数据刷新循环每 15 秒执行一次
  - 无错误日志
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证 run_loop.sh 脚本启动成功
  - `programmatic` TR-2.2: 检查数据刷新日志
- **Notes**: 这是后台进程，需要在单独的终端运行

## [ ] 任务 3: 启动看板服务器
- **Priority**: P0
- **Depends On**: Task 1
- **Description**:
  - 启动 `dashboard/server.py` 服务器
  - 验证服务器在端口 7891 运行
- **Success Criteria**:
  - 看板服务器在端口 7891 运行
  - 服务器启动无错误
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证 server.py 启动成功
  - `programmatic` TR-3.2: 测试看板服务器响应
- **Notes**: 这是后台进程，需要在单独的终端运行

## [ ] 任务 4: 验证系统功能
- **Priority**: P1
- **Depends On**: Task 2, Task 3
- **Description**:
  - 访问看板界面
  - 验证各功能面板正常显示
  - 测试任务创建功能
- **Success Criteria**:
  - 看板界面正常加载
  - 所有功能面板可访问
  - 任务创建功能正常
- **Test Requirements**:
  - `human-judgement` TR-4.1: 验证看板界面加载正常
  - `programmatic` TR-4.2: 测试任务创建 API
- **Notes**: 访问 http://localhost:7891

## [ ] 任务 5: 运行测试套件
- **Priority**: P1
- **Depends On**: Task 1
- **Description**:
  - 运行项目的测试套件
  - 验证系统功能正常
- **Success Criteria**:
  - 所有测试通过
- **Test Requirements**:
  - `programmatic` TR-5.1: 运行 pytest 测试套件
  - `programmatic` TR-5.2: 验证测试结果
- **Notes**: 确保测试环境正确配置
