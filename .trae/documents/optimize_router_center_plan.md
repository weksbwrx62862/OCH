# 优化finance-assistant路由中心 - 实施计划

## 当前问题分析

### 1. 代码重复
- `quick_query_mode()` 中有自己的意图识别逻辑
- `task_router.py` 中也有意图识别逻辑
- 两处逻辑不一致，可能导致识别结果不同

### 2. 没有参数提取
- 当前不能从查询中提取具体参数（如股票代码、基金代码等）
- 所有技能都使用默认参数，不够灵活

### 3. 技能调用不够智能
- 没有根据查询内容动态传递参数
- 技能调用失败时没有降级策略

### 4. 代码结构可以优化
- 可以将两个模式的公共逻辑提取出来
- 减少代码重复

## 优化目标

1. **统一意图识别**：使用 `task_router.py` 作为唯一的意图识别器
2. **参数提取**：从查询中智能提取参数（股票代码、基金代码等）
3. **智能技能调用**：根据查询内容动态传递参数给技能
4. **降级策略**：技能调用失败时自动尝试替代方案
5. **代码结构优化**：提取公共逻辑，减少重复

## 实施计划

### [ ] 任务1：优化task_router.py，添加参数提取功能
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 在task_router.py中添加参数提取功能
  - 支持提取股票代码、基金代码、加密货币代码等
  - 添加更智能的意图识别逻辑
- **Success Criteria**:
  - 能从查询中提取参数
  - 意图识别更准确
- **Test Requirements**:
  - `programmatic` TR-1.1: 能从"贵州茅台"中提取股票代码
  - `programmatic` TR-1.2: 能从"BTC"中提取加密货币代码
  - `programmatic` TR-1.3: 能从"沪深300ETF"中提取基金代码

### [ ] 任务2：优化quick_query_mode，统一使用task_router
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 移除quick_query_mode中的重复意图识别逻辑
  - 统一使用task_router进行意图识别
  - 使用提取的参数调用技能
- **Success Criteria**:
  - quick_query_mode使用统一的意图识别
  - 能正确传递参数给技能
- **Test Requirements**:
  - `programmatic` TR-2.1: quick_query_mode使用task_router
  - `programmatic` TR-2.2: 能正确传递参数

### [ ] 任务3：优化skill_adapter.py，支持动态参数
- **Priority**: P0
- **Depends On**: 任务2
- **Description**:
  - 修改skill_adapter.py支持动态参数
  - 根据查询内容智能选择技能参数
  - 添加技能调用降级策略
- **Success Criteria**:
  - 技能能接收动态参数
  - 技能调用失败时有降级策略
- **Test Requirements**:
  - `programmatic` TR-3.1: 技能能接收动态参数
  - `programmatic` TR-3.2: 降级策略正常工作

### [ ] 任务4：优化deep_analysis_mode，使用提取的参数
- **Priority**: P1
- **Depends On**: 任务3
- **Description**:
  - 让deep_analysis_mode也使用提取的参数
  - 优化多技能协同调用逻辑
  - 改进报告生成，包含更多细节
- **Success Criteria**:
  - deep_analysis_mode使用提取的参数
  - 报告更详细
- **Test Requirements**:
  - `programmatic` TR-4.1: deep_analysis_mode使用提取的参数
  - `human-judgement` TR-4.2: 报告更详细

### [ ] 任务5：添加配置文件，支持技能配置
- **Priority**: P1
- **Depends On**: 任务4
- **Description**:
  - 添加config.py配置文件
  - 支持技能参数配置
  - 支持意图识别关键词配置
- **Success Criteria**:
  - 配置文件存在
  - 配置能正常加载
- **Test Requirements**:
  - `programmatic` TR-5.1: 配置文件能正常加载
  - `programmatic` TR-5.2: 配置能正确应用

### [ ] 任务6：全面测试和验证
- **Priority**: P2
- **Depends On**: 任务5
- **Description**:
  - 测试快速查询模式
  - 测试深度分析模式
  - 测试参数提取
  - 测试降级策略
- **Success Criteria**:
  - 所有测试通过
- **Test Requirements**:
  - `programmatic` TR-6.1: 快速查询模式测试通过
  - `programmatic` TR-6.2: 深度分析模式测试通过
  - `programmatic` TR-6.3: 参数提取测试通过
  - `programmatic` TR-6.4: 降级策略测试通过

## 预期成果

- 统一的意图识别逻辑
- 智能参数提取
- 更灵活的技能调用
- 更好的降级策略
- 更清晰的代码结构
