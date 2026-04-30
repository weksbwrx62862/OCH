# CoinGecko Pro API 功能扩展计划 (第四轮)

## 目标
继续深度分析 CoinGecko API，添加遗漏的实用端点

## 当前已实现功能概览

### REST API (已实现: 约 45 个端点)
- ✅ Onchain DEX 数据 (价格、交易对、流动性池、交易记录、聚合价格、储备、K线、交易者排行、Megafilter)
- ✅ Coins 高级端点 (涨跌幅、新币、OHLC、市场数据、历史)
- ✅ NFTs 端点 (市场、图表、交易对)
- ✅ Exchanges 端点 (列表、成交量图表)
- ✅ Global 端点 (市值图表)
- ✅ Treasury 端点 (持仓、交易历史、历史图表)
- ✅ Asset Platforms
- ✅ Categories (分类、分类列表)
- ✅ Derivatives (衍生品交易所)
- ✅ Companies (公司持仓)
- ✅ Search/Trending
- ✅ Indexes
- ✅ Contract API (代币信息、历史图表)

## 计划新增功能

### 1. Exchange Rates API (汇率)

#### 1.1 获取 BTC 汇率
```
GET /exchange_rates
```
- 功能：获取 BTC 到所有支持货币的汇率
- 用途：获取加密货币相对于 BTC 的汇率，用于汇率转换

### 2. Events API (事件)

#### 2.1 获取加密货币事件
```
GET /events
```
- 功能：获取加密货币相关活动/事件

#### 2.2 获取事件国家列表
```
GET /events/countries
```

#### 2.3 获取事件类型列表
```
GET /events/types
```

### 3. Status Updates API (状态更新)

#### 3.1 获取币种状态更新
```
GET /coins/{id}/status_updates
```

#### 3.2 获取交易所状态更新
```
GET /exchanges/{id}/status_updates
```

### 4. Finance API (金融)

#### 4.1 获取金融平台列表
```
GET /finance
```

#### 4.2 获取金融产品列表
```
GET /finance_products
```

### 5. NFT 增强端点

#### 5.1 获取所有 NFT 列表
```
GET /nfts/list
```
- 功能：获取所有支持的 NFT (id, contract address, name, platform, symbol)

#### 5.2 通过合约地址获取 NFT 数据
```
GET /nfts/{asset_platform_id}/contract/{contract_address}
```

### 6. DeFi API

#### 6.1 获取 DeFi 数据
```
GET /global/decentralized_finance_defi
```
- 功能：获取全球 DeFi 统计数据 (总锁仓量、DeFi 市值等)

### 7. Coins Markets API

#### 7.1 获取币种市场数据
```
GET /coins/markets
```
- 参数：vs_currency, order, per_page, page, sparkline 等
- 功能：获取币种的行情数据（比 simple API 更丰富）

### 8. Additional Contract Endpoint

#### 8.1 合约历史图表(指定范围)
```
GET /coins/{id}/contract/{contract_address}/market_chart/range
```
- 支持指定开始和结束时间戳

### 9. Simple API 增强

#### 9.1 批量获取币种价格 (带更多参数)
```
GET /simple/price
```
- 支持 include_market_cap, include_24hr_vol, include_24hr_change

## 实施步骤

### Step 1: 更新 CoinGeckoProClient
添加以下方法：
1. `get_exchange_rates()` - BTC 汇率
2. `get_events()` - 加密事件
3. `get_events_countries()` - 事件国家
4. `get_events_types()` - 事件类型
5. `get_coin_status_updates()` - 币种状态更新
6. `get_exchange_status_updates()` - 交易所状态更新
7. `get_finance()` - 金融平台
8. `get_finance_products()` - 金融产品
9. `get_nfts_list()` - NFT 列表
10. `get_nft_by_contract()` - NFT 合约数据
11. `get_defi_data()` - DeFi 数据
12. `get_coins_markets()` - 币种市场数据
13. `get_simple_price()` - 增强价格查询

### Step 2: 更新 CryptoAnalyzer
添加便捷封装方法

### Step 3: 更新 SKILL.md
添加新命令

### Step 4: 更新 API 参考文档

## 新增 SKILL.md 命令

```bash
# Exchange Rates
crypto exchange rates                    # BTC 汇率

# Events
crypto events                          # 加密货币事件
crypto events countries                 # 事件国家
crypto events types                    # 事件类型

# Status Updates
crypto status <coin_id>                # 币种状态更新
crypto exchange status <exchange_id>   # 交易所状态更新

# Finance
crypto finance                        # 金融平台
crypto finance products               # 金融产品

# NFTs
crypto nfts list                      # NFT 列表
crypto nft contract <platform> <contract> # NFT 合约数据

# DeFi
crypto defi                           # DeFi 全局数据

# Markets
crypto markets <vs_currency> <order>   # 币种市场数据

# Simple
crypto price <coin_id>                # 价格(带更多信息)
```

## 预估工作量

1. CoinGeckoProClient: ~80 行代码
2. CryptoAnalyzer: ~100 行代码
3. SKILL.md: ~25 行
4. API 参考文档: ~80 行
