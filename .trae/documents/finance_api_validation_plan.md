# 金融统一接口验证计划

## 验证总结

已完成验证任务：
- ✅ 任务1：依赖环境检查通过
- ✅ 任务3：外汇汇率功能正常
- ✅ 任务5：自选股管理功能正常

待验证（受API速率限制）：
- ⏸️ 任务2：股票实时报价功能（yfinance API限流）
- ⏸️ 任务4：历史走势功能（yfinance API限流）

说明：股票相关功能代码结构正确，但由于yfinance API的速率限制，暂时无法完成实际数据获取验证。

## [x] 任务 1: 检查依赖环境
- **Priority**: P0
- **Depends On**: None
- **Description**: 验证Python环境和所需依赖包是否已正确安装
- **Success Criteria**: 所有依赖包（yfinance, pandas, requests）都能正常导入
- **Test Requirements**:
  - `programmatic` TR-1.1: 运行 `python -c "import yfinance, pandas, requests"` 成功
- **Notes**: 如果依赖缺失，需要先安装

## [ ] 任务 2: 验证实时报价功能 - 股票
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**: 测试获取股票实时报价功能
- **Success Criteria**: 能够成功获取AAPL（苹果公司）的实时价格信息
- **Test Requirements**:
  - `programmatic` TR-2.1: 运行 `python scripts/market_quote.py AAPL` 成功返回价格数据
  - `human-judgement` TR-2.2: 输出包含当前价格、涨跌幅等关键信息
- **Notes**: 使用AAPL作为测试标的

## [x] 任务 3: 验证实时报价功能 - 外汇
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**: 测试获取外汇汇率功能
- **Success Criteria**: 能够成功获取USD/CNY的汇率信息
- **Test Requirements**:
  - `programmatic` TR-3.1: 运行 `python scripts/market_quote.py USD/CNY` 成功返回汇率数据
  - `human-judgement` TR-3.2: 输出包含汇率和更新时间
- **Notes**: 使用USD/CNY作为测试标的

## [ ] 任务 4: 验证历史走势功能
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**: 测试获取股票历史数据功能
- **Success Criteria**: 能够成功获取AAPL最近7天的历史数据
- **Test Requirements**:
  - `programmatic` TR-4.1: 运行 `python scripts/market_series.py AAPL --days 7` 成功返回历史数据
  - `human-judgement` TR-4.2: 输出包含日期范围和最近数据点
- **Notes**: 使用7天较短时间周期进行快速测试

## [x] 任务 5: 验证自选股管理功能
- **Priority**: P1
- **Depends On**: 任务 1
- **Description**: 测试自选股的添加、查看和删除功能
- **Success Criteria**: 自选股管理的所有功能正常工作
- **Test Requirements**:
  - `programmatic` TR-5.1: 运行 `python scripts/market_watchlist.py add MSFT` 成功添加
  - `programmatic` TR-5.2: 运行 `python scripts/market_watchlist.py summary` 成功显示自选股
  - `programmatic` TR-5.3: 运行 `python scripts/market_watchlist.py remove MSFT` 成功删除
- **Notes**: 使用MSFT作为测试标的，测试后清理
