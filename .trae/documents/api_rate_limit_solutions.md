# yfinance & akshare API 限流解决方案

## 问题现状

### 问题描述
- **yfinance API**：完全被限流，无法获取股票、大宗商品、ETF、债券、技术指标等数据
- **akshare API**：部分功能受限，无法获取A股数据
- **错误信息**：`Too Many Requests. Rate limited. Try after a while.`

### 影响范围
受影响的功能模块：
1. finance（基础金融市场追踪）
2. market-data（综合市场数据）
3. technical（技术分析）
4. portfolio（投资组合管理）
5. analysis（分析报告）
6. data-source（数据源管理）

---

## 替代数据源方案

我在 `/home/xxh/金融技能` 目录下发现了多个优质的替代数据源：

### 方案一：东方财富数据源（推荐）

#### 1. mx-finance-data（基于东方财富数据库）
- **位置**：`/home/xxh/金融技能/MX/mx-finance-data-1.0.10`
- **功能**：
  - 支持A港美股、基金、债券等多种资产
  - 实时行情、公司信息、估值、财务报表等
  - 自然语言查询金融数据
  - 返回结果包含数据说明及xlsx文件
- **支持查询**：
  - 股票（A股、港股、美股）
  - 板块、指数、股东
  - 企业发行人、债券、非上市公司
  - 股票市场、基金市场、债券市场
- **限制**：单次查询最多5个实体
- **要求**：需要 `EM_API_KEY`（东方财富妙想服务）

#### 2. stock-earnings-review（上市公司业绩点评）
- **位置**：`/home/xxh/金融技能/MX/stock-earnings-review-1.0.1`
- **功能**：
  - 沪深京港美五大市场的上市公司/股票业绩点评
  - 财报分析、业绩解读
  - 生成PDF/Word附件
- **要求**：需要 `EM_API_KEY`

---

### 方案二：Tushare Pro数据源

#### tushare-finance-2.0.6
- **位置**：`/home/xxh/金融技能/tushare-finance-2.0.6 (1)`
- **功能**：
  - 220+个Tushare Pro接口
  - 股票行情、财务报表、宏观经济指标
  - A股、港股、美股、基金、期货、债券
- **支持接口**：
  - 股票数据（39个接口）
  - 指数数据（18个接口）
  - 基金数据（11个接口）
  - 期货期权（16个接口）
  - 宏观经济（10个接口）
  - 港股美股（23个接口）
  - 债券数据（16个接口）
- **要求**：需要 `TUSHARE_TOKEN`

---

### 方案三：多数据源支持（finance-1.1.2）

#### finance-1.1.2
- **位置**：`/home/xxh/金融技能/finance-1.1.2`
- **功能**：
  - 支持多个数据源提供商
  - 自带缓存机制和降级策略
  - 支持股票、ETF、指数、加密货币、外汇
- **数据源**：
  - **默认**：yfinance（无密钥，但有限流）
  - **付费选项**：TwelveData、AlphaVantage
  - **外汇**：ExchangeRate-API（免费）
- **要求**：可选配置 `TWELVEDATA_API_KEY`、`ALPHAVANTAGE_API_KEY`

---

### 方案四：其他可用技能

#### 已验证的功能（无需额外API密钥）
1. **crypto-analysis**：加密货币AI分析（AI500、OI排行）- 无需密钥
2. **finance-assistant**：统一金融助手 - 无需密钥
3. **risk-assessor**：风险评估系统 - 无需密钥
4. **portfolio（本地功能）**：持仓管理、绩效分析、再平衡 - 无需密钥
5. **news（情感分析）**：财经新闻情感分析 - 无需密钥
6. **technical（纯逻辑）**：技术指标计算、K线形态识别 - 无需密钥
7. **fund-tracker（定投计算）**：定投收益计算 - 无需密钥

---

## 具体解决方案

### 短期方案（立即可用）

#### 1. 使用已有功能（无需API）
✅ **完全可用**：
- 外汇汇率查询（ExchangeRate-API）
- 加密货币AI分析（NoFx API）
- 自选股管理（本地存储）
- 风险评估（纯逻辑）
- 投资组合再平衡建议（纯逻辑）
- 技术指标计算（纯逻辑）
- K线形态识别（纯逻辑）
- 基金定投计算（纯逻辑）
- 财经新闻情感分析（纯逻辑）

#### 2. 避开高峰期使用
- 建议在非高峰期（如凌晨、周末）使用yfinance功能
- 每次请求间隔至少30秒

#### 3. 使用本地缓存
- 已验证的data-source技能有缓存机制
- 建议增加更长的缓存TTL（24小时或更长）

---

### 中期方案（配置API密钥）

#### 1. 东方财富数据源（推荐，功能最全）
**注册步骤**：
1. 访问 https://ai.eastmoney.com/mxClaw 注册账号
2. 获取API_KEY
3. 配置环境变量：
```bash
export EM_API_KEY="your_api_key_here"
```

**使用方式**：
```bash
# 查询金融数据
cd /home/xxh/金融技能/MX/mx-finance-data-1.0.10
python3 scripts/get_data.py --query "贵州茅台近期走势如何"

# 业绩点评
cd /home/xxh/金融技能/MX/stock-earnings-review-1.0.1
python3 scripts/validate_entity.py --query "东方财富 业绩点评"
```

#### 2. Tushare Pro数据源
**注册步骤**：
1. 访问 https://tushare.pro 注册
2. 获取Token
3. 配置环境变量：
```bash
export TUSHARE_TOKEN="your_token"
```

**使用方式**：
```python
import tushare as ts
pro = ts.pro_api()
df = pro.daily(ts_code='000001.SZ', start_date='20241201', end_date='20241231')
```

#### 3. TwelveData/AlphaVantage（付费选项）
**优势**：
- 数据质量高
- 限流宽松
- 支持高频数据

**配置**：
```bash
export TWELVEDATA_API_KEY="your_key"
export ALPHAVANTAGE_API_KEY="your_key"
```

---

### 长期方案（架构优化）

#### 1. 多数据源路由
实现数据源路由器，自动选择可用的数据源：
- 优先使用免费数据源
- 限流时自动降级
- 支持数据源优先级配置

#### 2. 请求队列和重试
- 实现请求队列
- 指数退避重试
- 并发控制

#### 3. 本地数据缓存
- 增加Redis缓存
- 更长的缓存TTL
- 定期更新缓存

#### 4. 数据聚合
- 聚合多个数据源的数据
- 数据校验和去重
- 统一数据格式

---

## 推荐配置方案

### 推荐组合（免费为主）

```
主要数据源：
├── 东方财富 mx-finance-data（EM_API_KEY）→ 主要A股/港股/美股数据
├── Tushare Pro（TUSHARE_TOKEN）→ 备用数据源
├── ExchangeRate-API（免费）→ 外汇数据
└── NoFx API（免费）→ 加密货币AI分析

本地功能：
├── 自选股管理
├── 风险评估
├── 投资组合再平衡
├── 技术指标计算
├── K线形态识别
├── 基金定投计算
└── 财经新闻情感分析
```

---

## 下一步行动建议

1. **立即**：使用已验证的纯逻辑功能
2. **本周**：注册东方财富妙想服务，获取EM_API_KEY
3. **本月**：配置Tushare Pro作为备用数据源
4. **长期**：实现多数据源路由和优化缓存机制

---

## 相关文档

- `/home/xxh/金融技能/MX/mx-finance-data-1.0.10/SKILL.md` - 东方财富数据源使用说明
- `/home/xxh/金融技能/MX/stock-earnings-review-1.0.1/SKILL.md` - 业绩点评使用说明
- `/home/xxh/金融技能/tushare-finance-2.0.6 (1)/SKILL.md` - Tushare使用说明
- `/home/xxh/.trae/documents/complete_finance_skills_validation_plan.md` - 完整技能验证计划
