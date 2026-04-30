# CoinGecko Pro API 功能扩展计划 (第六轮 - 完善版)

## 目标
继续深度分析 CoinGecko API，添加所有遗漏的端点

## 当前已实现功能概览

### REST API (已实现: 约 70+ 个端点)
- ✅ Onchain DEX、NFT、Exchanges、Global、Treasury、Categories、Derivatives、Companies、Search/Trending、Indexes、Asset Platforms、Contract API、Exchange Rates、Events、Status Updates、Finance、DeFi、Supply Charts 等

## 计划新增/完善功能

### 1. Coins 端点完善

#### 1.1 币种市场图表范围 (完善)
```
GET /coins/{id}/market_chart/range
```
- 功能：获取指定时间范围的币种市场图表

#### 1.2 币种交易对 (完善)
```
GET /coins/{id}/tickers
```
- 功能：获取币种在所有交易所的交易对信息

#### 1.3 币种历史数据 (完善)
```
GET /coins/{id}/history
```
- 功能：获取币种在特定日期的历史数据

### 2. Exchanges 端点完善

#### 2.1 交易所交易对 (完善)
```
GET /exchanges/{id}/tickers
```
- 功能：获取交易所所有交易对信息

### 3. Derivatives 端点完善

#### 3.1 衍生品交易所列表
```
GET /derivatives/exchanges
```

#### 3.2 衍生品交易所详情
```
GET /derivatives/exchanges/{id}
```

### 4. Trending 端点新增

#### 4.1 热门池子搜索 (NEW! 2025.6)
```
GET /search/pools
```
- 功能：获取热门的 DEX 池子

### 5. Status Updates 端点

#### 5.1 全局状态更新列表
```
GET /status_updates
```

### 6. NFT 端点完善

#### 6.1 NFT 列表
```
GET /nfts/list
```
- 功能：获取所有支持的 NFT (id, contract address, name, platform, symbol)

## 实施步骤

### Step 1: 更新 CoinGeckoProClient
添加以下方法：
1. `get_coin_tickers()` - 币种交易对
2. `get_coin_history()` - 币种历史数据
3. `get_coin_market_chart_range()` - 币种市场图表范围
4. `get_exchange_tickers()` - 交易所交易对
5. `get_derivatives_exchanges()` - 衍生品交易所列表
6. `get_derivatives_exchange_info()` - 衍生品交易所详情
7. `get_trending_pools()` - 热门池子搜索
8. `get_all_status_updates()` - 全局状态更新
9. `get_nfts_list()` - NFT 列表 (已添加)

### Step 2: 更新 CryptoAnalyzer
添加便捷封装方法

### Step 3: 更新 SKILL.md
添加新命令

### Step 4: 更新 API 参考文档

## 新增 SKILL.md 命令

```bash
# Coins 完善
crypto tickers <coin_id>                      # 币种交易对
crypto history <coin_id> <date>              # 币种历史数据
crypto market range <coin_id> <vs> <from> <to> # 市场图表范围

# Exchanges 完善
crypto exchange tickers <exchange_id>          # 交易所交易对

# Derivatives 完善
crypto derivatives exchanges                  # 衍生品交易所列表
crypto derivatives info <exchange_id>          # 衍生品交易所详情

# Trending 新增
crypto trending pools                        # 热门池子搜索

# Status 新增
crypto status updates                        # 全局状态更新
```

## 预估工作量

1. CoinGeckoProClient: ~60 行代码
2. CryptoAnalyzer: ~80 行代码
3. SKILL.md: ~20 行
4. API 参考文档: ~60 行
