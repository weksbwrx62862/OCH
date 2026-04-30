# CoinGecko Pro API 功能扩展计划 (第三轮)

## 目标
继续深度分析 CoinGecko API，添加更多实用端点

## 当前已实现功能概览

### REST API (已实现)
- ✅ Onchain DEX 数据 (价格、交易对、流动性池、交易记录)
- ✅ Coins 高级端点 (涨跌幅、新币、OHLC)
- ✅ NFTs 端点 (市场、图表、交易对)
- ✅ Exchanges 端点 (成交量图表)
- ✅ Global 端点 (市值图表)
- ✅ Treasury 端点 (持仓、交易历史)
- ✅ 高级 DEX/Pool 端点 (聚合价格、储备、K线、交易者排行、Megafilter)
- ✅ Asset Platforms (Enterprise)

## 计划新增功能

### 1. Simple API 增强

#### 1.1 通过合约地址查询代币价格
```
GET /simple/token_price/{id}
```
- 通过资产平台 ID 和合约地址查询代币价格
- 支持批量查询多个合约地址
- 比 Onchain API 更简单的接口

#### 1.2 支持的计价货币列表
```
GET /simple/supported_vs_currencies
```
- 获取所有支持的计价货币

### 2. Contract API (合约代币数据)

#### 2.1 通过合约地址获取币种信息
```
GET /coins/{id}/contract/{contract_address}
```
- 通过合约地址获取币种的完整信息

#### 2.2 合约代币历史图表
```
GET /coins/{id}/contract/{contract_address}/market_chart
```
- 获取合约代币的历史价格、市场cap、交易量

#### 2.3 合约代币历史图表 (指定时间范围)
```
GET /coins/{id}/contract/{contract_address}/market_chart/range
```
- 支持指定开始和结束时间戳

### 3. Categories API (币种分类)

#### 3.1 币种分类列表
```
GET /coins/categories/list
```
- 获取所有币种分类

#### 3.2 带市场数据的分类
```
GET /coins/categories
```
- 获取分类及每个分类的市场数据（总市值、交易量等）

### 4. Exchanges 增强

#### 4.1 交易所列表
```
GET /exchanges/list
```
- 获取所有交易所 ID 和名称

### 5. Derivatives API (衍生品)

#### 5.1 衍生品交易所列表
```
GET /derivatives
```
- 获取所有衍生品交易所

#### 5.2 衍生品交易所列表 (简化)
```
GET /derivatives/list
```
- 获取衍生品交易所 ID 和名称

### 6. Companies API (公司持仓)

#### 6.1 上市公司加密持仓
```
GET /companies/public_treasury/{coin_id}
```
- 获取持有特定加密货币的上市公司列表

### 7. Search API (搜索)

#### 7.1 搜索币种
```
GET /search
```
- 搜索币种、类别、市场

### 8. Trending API (热门)

#### 8.1 热门币种
```
GET /search/trending
```
- 获取当前热门币种

### 9. Asset Platforms API (资产平台)

#### 9.1 资产平台列表
```
GET /asset_platforms
```
- 获取所有支持的资产平台

### 10. Indexes API (指数)

#### 10.1 指数列表
```
GET /indexes
```
- 获取所有指数

#### 10.2 特定指数
```
GET /indexes/{market_id}/{index_id}
```
- 获取特定指数详情

## 实施步骤

### Step 1: 更新 CoinGeckoProClient
添加以下方法：
1. `get_simple_token_price_by_address()` - 合约地址查价格
2. `get_supported_currencies()` - 支持的货币
3. `get_coin_by_contract()` - 合约查币种信息
4. `get_contract_market_chart()` - 合约历史图表
5. `get_contract_market_chart_range()` - 合约历史图表(范围)
6. `get_categories_list()` - 分类列表
7. `get_categories()` - 分类市场数据
8. `get_exchanges_list()` - 交易所列表
9. `get_derivatives()` - 衍生品交易所
10. `get_derivatives_list()` - 衍生品列表
11. `get_companies()` - 公司持仓
12. `search()` - 搜索
13. `get_trending()` - 热门
14. `get_asset_platforms()` - 资产平台
15. `get_indexes()` - 指数
16. `get_index()` - 特定指数

### Step 2: 更新 CryptoAnalyzer
添加便捷封装方法

### Step 3: 更新 SKILL.md
添加新命令

### Step 4: 更新 API 参考文档

## 新增 SKILL.md 命令

```bash
# Simple API
crypto token price <platform> <contract>        # 合约地址查价格
crypto supported currencies                    # 支持的计价货币

# Contract API
crypto contract info <coin_id> <contract>     # 合约查币种信息
crypto contract chart <coin_id> <contract> <days> # 合约历史图表

# Categories
crypto categories list                         # 币种分类列表
crypto categories                             # 分类市场数据

# Exchanges
crypto exchanges list                         # 交易所列表

# Derivatives
crypto derivatives                            # 衍生品交易所
crypto derivatives list                       # 衍生品交易所列表

# Companies
crypto companies <coin_id>                   # 持有某币种的公司

# Search & Trending
crypto search <query>                         # 搜索币种
crypto trending                               # 热门币种

# Asset Platforms
crypto platforms                             # 资产平台列表

# Indexes
crypto indexes                               # 指数列表
crypto index <market> <index>                # 特定指数
```

## 预估工作量

1. CoinGeckoProClient: ~120 行代码
2. CryptoAnalyzer: ~150 行代码
3. SKILL.md: ~30 行
4. API 参考文档: ~100 行
