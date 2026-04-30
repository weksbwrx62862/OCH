# Finance Skills 安装到 Clawith 计划

## 概述

将微信公众号文章介绍的 Finance Skills 金融投资分析技能集安装到 clawith 平台。

## 信息来源

- **介绍文章**: 微信公众号 "打造你的 AI 投资助手：Finance Skills 技能集完全指南"
- **开源地址**: https://github.com/openclaw/skills/finance-skills

## 项目特点

- 专为个人投资者设计的 AI 技能集
- 六大核心技能覆盖股票、基金、组合、舆情、宏观、风险
- 适用于 OpenClaw 平台

## 六大核心技能

| 模块 | 功能 | 使用场景 |
|------|------|----------|
| stock-analyzer | 股票技术面/基本面分析 | 选股、择时 |
| fund-tracker | 基金净值追踪、定投计算 | 基金投资 |
| portfolio-manager | 投资组合分析、再平衡 | 资产管理 |
| news-sentiment | 财经新闻聚合、舆情分析 | 市场研判 |
| macro-economy | 宏观经济指标跟踪 | 大势判断 |
| risk-assessor | 风险评估、压力测试 | 风险控制 |

## 目录结构

```
finance-skills/
├── SKILL.md                          # 主技能说明文件
├── scripts/
│   ├── stock-analyzer.js            # 股票分析包装器
│   ├── fund-tracker.js              # 基金追踪包装器
│   ├── portfolio-manager.js         # 组合管理包装器
│   ├── news-sentiment.js            # 舆情分析包装器
│   ├── macro-economy.js             # 宏观经济包装器
│   └── risk-assessor.js             # 风险评估包装器
└── references/
    └── README.md                    # 详细使用文档
```

## 安装步骤

### 步骤 1: 创建技能目录

```bash
mkdir -p ~/.clawith/data/agents/<agent-id>/skills/finance-skills
```

### 步骤 2: 创建 SKILL.md

创建主技能说明文件，包含：
- `name`: finance-skills
- `description`: 金融投资分析技能集
- `version`: 1.0.0
- `tags`: 投资、股票、基金、组合管理、风险评估

### 步骤 3: 创建包装器脚本

为每个模块创建 JavaScript 包装器，提供命令行接口：

**fund-tracker.js**:
```bash
node fund-tracker.js query <基金代码>           # 查询基金净值
node fund-tracker.js 定投 <基金代码> <金额> <月数>  # 计算定投收益
```

**risk-assessor.js**:
```bash
node risk-assessor.js test    # 风险评估问卷
```

**portfolio-manager.js**:
```bash
node portfolio-manager.js analyze     # 组合分析
node portfolio-manager.js rebalance  # 再平衡建议
```

### 步骤 4: 编写使用文档

创建 `references/README.md`，包含详细使用说明。

## 技能触发场景

当用户描述以下场景时触发此技能：
- "分析股票走势"
- "查询基金净值"
- "计算定投收益"
- "评估我的投资组合"
- "进行风险评估"
- "分析宏观经济"
- "追踪财经新闻"
- "再平衡投资组合"

## 依赖项

- Node.js 18+
- axios（用于 HTTP 请求）
- cheerio（用于网页抓取）
- yfinance（用于获取市场数据）

## 示例输出

### 基金查询
```bash
node fund-tracker.js query 510300
# 输出：沪深300ETF最新净值
```

### 定投计算
```bash
node fund-tracker.js 定投 510300 1000 12
# 输出：12个月定投预期收益约8.3%
```

### 风险评估
```bash
node risk-assessor.js test
# 输出：风险等级（保守型/稳健型/平衡型/进取型）
```

### 组合分析
```bash
node portfolio-manager.js analyze
# 输出：资产配置比例、优化建议
```
