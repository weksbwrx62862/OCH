# CoinGecko Pro API 功能扩展计划 (第五轮)

## 目标
继续深度分析 CoinGecko API，添加企业级端点和遗漏功能

## 当前已实现功能概览

### REST API (已实现: 约 60 个端点)
- ✅ Onchain DEX、NFT、Exchanges、Global、Treasury、Categories、Derivatives、Companies、Search/Trending、Indexes、Asset Platforms、Contract API、Exchange Rates、Events、Status Updates、Finance、DeFi 等

## 计划新增功能

### 1. Supply Charts (Enterprise - 企业级)

#### 1.1 流通供应量图表
```
GET /coins/{id}/circulating_supply_chart
```
- 功能：获取币种的流通供应量历史数据

#### 1.2 流通供应量图表(指定范围)
```
GET /coins/{id}/circulating_supply_chart/range
```
- 支持指定时间戳范围

#### 1.3 总供应量图表
```
GET /coins/{id}/total_supply_chart
```
- 功能：获取币种的总供应量历史数据

#### 1.4 总供应量图表(指定范围)
```
GET /coins/{id}/total_supply_chart/range
```
- 支持指定时间戳范围

### 2. OHLC Range Endpoint

#### 2.1 OHLC 范围查询
```
GET /coins/{id}/ohlc/range
```
- 参数：vs_currency, from_timestamp, to_timestamp
- 功能：获取指定时间范围的 OHLC 数据

### 3. NFT Enhanced Endpoints

#### 3.1 NFT 市场图表(通过合约)
```
GET /nfts/{asset_platform_id}/contract/{contract_address}/market_chart
```
- 功能：通过合约地址获取 NFT 历史价格图表

### 4. Indexes List Endpoints

#### 4.1 指数列表
```
GET /indexes/list
```
- 功能：获取所有指数 ID 和名称

#### 4.2 按市场和ID获取指数
```
GET /indexes/list_by_market_and_id/{market_id}/{id}
```
- 功能：获取特定市场和ID的指数

### 5. Status Updates Global

#### 5.1 所有状态更新
```
GET /status_updates
```
- 功能：获取所有加密货币/交易所的状态更新

### 6. Additional NFT Endpoint

#### 6.1 NFT 合约交易对
```
GET /nfts/{asset_platform_id}/contract/{contract_address}/tickers
```
- 功能：获取 NFT 合约的交易对信息

## 实施步骤

### Step 1: 更新 CoinGeckoProClient
添加以下方法：
1. `get_circulating_supply_chart()` - 流通供应量图表
2. `get_circulating_supply_chart_range()` - 流通供应量图表(范围)
3. `get_total_supply_chart()` - 总供应量图表
4. `get_total_supply_chart_range()` - 总供应量图表(范围)
5. `get_ohlc_range()` - OHLC 范围查询
6. `get_nft_contract_chart()` - NFT 合约图表
7. `get_indexes_list()` - 指数列表
8. `get_indexes_by_market_and_id()` - 按市场和ID获取指数
9. `get_all_status_updates()` - 所有状态更新
10. `get_nft_contract_tickers()` - NFT 合约交易对

### Step 2: 更新 CryptoAnalyzer
添加便捷封装方法

### Step 3: 更新 SKILL.md
添加新命令

### Step 4: 更新 API 参考文档

## 新增 SKILL.md 命令

```bash
# Supply Charts (Enterprise)
crypto circulating supply <coin_id> <days>       # 流通供应量图表
crypto total supply <coin_id> <days>              # 总供应量图表
crypto supply range <coin_id> <from> <to>         # 供应量范围查询

# OHLC
crypto ohlc range <coin_id> <vs_currency> <from> <to> # OHLC 范围

# NFT Enhanced
crypto nft contract chart <platform> <contract> <days> # NFT 合约图表
crypto nft contract tickers <platform> <contract>      # NFT 合约交易对

# Indexes
crypto indexes list                                # 指数列表
crypto indexes list <market> <id>                 # 按市场ID获取指数

# Status
crypto status updates                             # 所有状态更新
```

## 预估工作量

1. CoinGeckoProClient: ~60 行代码
2. CryptoAnalyzer: ~80 行代码
3. SKILL.md: ~20 行
4. API 参考文档: ~60 行
