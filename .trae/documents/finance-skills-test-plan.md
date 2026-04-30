# Finance Skills 技能测试计划

## 测试目标

验证 clawith 中已创建的 Finance Skills 各技能是否能够正常执行。

## 测试对象

已创建的 7 个技能：
1. `stock-analyzer` - 股票分析
2. `fund-tracker` - 基金追踪
3. `portfolio-manager` - 组合管理
4. `macro-economy` - 宏观经济
5. `risk-assessor` - 风险评估
6. `news-sentiment` - 舆情分析
7. `finance-news-pro` - 财经新闻深度分析

## 测试步骤

### 步骤 1: 验证目录结构

检查所有技能的目录和文件是否完整：

```bash
ls -la ~/.clawith/data/agents/594e34f8-cdef-4774-811b-026f4a61bdeb/skills/
```

### 步骤 2: 安装依赖

```bash
# 安装 Python 依赖
pip install requests yfinance pandas numpy

# 设置脚本执行权限
chmod +x ~/.clawith/data/agents/594e34f8-cdef-4774-811b-026f4a61bdeb/skills/finance-news-pro/scripts/fetch_news.py
```

### 步骤 3: 测试 finance-news-pro（已有完整脚本）

```bash
# 测试新闻抓取脚本
python3 ~/.clawith/data/agents/594e34f8-cdef-4774-811b-026f4a61bdeb/skills/finance-news-pro/scripts/fetch_news.py --brief
```

预期：能正常抓取并输出新闻简报

### 步骤 4: 测试 fund-tracker

```bash
# 测试基金净值查询
python3 ~/.clawith/data/agents/594e34f8-cdef-4774-811b-026f4a61bdeb/skills/fund-tracker/scripts/fund_tracker.py query 510300
```

预期：返回基金净值信息

### 步骤 5: 测试 risk-assessor

```bash
# 测试风险评估问卷
python3 ~/.clawith/data/agents/594e34f8-cdef-4774-811b-026f4a61bdeb/skills/risk-assessor/scripts/risk_assessor.py test
```

预期：输出风险评估问卷题目

### 步骤 6: 测试 AI 助手触发

在 clawith AI 助手中输入：

```
"帮我查询沪深300ETF的最新净值"
"我想做风险评估"
"分析一下今天的财经新闻"
```

## 预期结果

- 所有技能能被 clawith 识别
- 命令行脚本能正常执行
- AI 助手能正确触发对应技能

## 注意事项

- 部分技能（如 stock-analyzer、portfolio-manager 等）只创建了 SKILL.md，脚本需要额外实现
- 实时行情查询需要网络连接
- API 密钥功能需要用户自行配置
