# CoinGecko API 端点兼容性检查与修复计划

## 问题确认

您的密钥 `CG-wfikqg8tRikdLj2dGg9TprAF` 是 **Demo API** 密钥。

### Demo API 不支持的端点（代码中有使用）

代码中以下端点是 **Pro API 专属**，Demo API 用户无法使用：

#### 1. Onchain DEX 数据 (全部不支持)
```
/onchain/simple/networks/{network}/token_price/{address}
/onchain/dex/v1/pairs/{network}
/onchain/dex/v1/tokens/{network}/{token}/trades
/onchain/dex/v1/pools/{network}/{pool}
/onchain/networks/{network}
/onchain/networks
/onchain/dex/v1/tokens/{network}/{token}/aggregated_price
/onchain/dex/v1/pools/{network}/{pool}/token_reserves
/onchain/dex/v1/pools/{network}/{pool}/ohlcv
/onchain/traders/{network}/{token}/top
/onchain/pools/megafilter
```

#### 2. Pro API 专属端点
```
/coins/top_gainers_losers          # 需要 Pro
/coins/list/new                     # 需要 Pro
/coins/{id}/circulating_supply_chart  # 需要 Enterprise
/coins/{id}/total_supply_chart        # 需要 Enterprise
/coins/{id}/ohlc/range                 # 需要 Pro
/exchanges/{id}/volume_chart/range     # 需要 Pro
/nfts/markets                          # 需要 Pro
/nfts/{id}/market_chart                 # 需要 Pro
/nfts/{id}/tickers                      # 需要 Pro
/public_treasury/*                      # 需要 Pro
/global/market_cap_chart                 # 需要 Pro
/global/decentralized_finance_defi       # 需要 Pro
/finance, /finance_products             # 需要 Pro
/events, /events/countries, /events/types  # 需要 Pro
/status_updates                          # 需要 Pro
/coins/{id}/status_updates               # 需要 Pro
/indexes/*                               # 需要 Pro
/derivatives/exchanges                   # 需要 Pro
/search/pools                           # 需要 Pro
/key                                     # 需要 Pro
```

## 修复方案

### 方案 1: 仅使用 Demo API 支持的端点
移除/禁用 Pro 专属端点的方法调用

### 方案 2: 添加 API 类型检测
在调用前检测是否为 Pro API，自动跳过不支持的端点

### 方案 3: 分离客户端
创建 `CoinGeckoDemoClient` 和 `CoinGeckoProClient` 两个类

## 推荐方案

采用**方案 2**：添加 API 类型检测，在调用前提示用户哪些端点需要 Pro API

## 实施步骤

### Step 1: 添加 API 类型检测装饰器
创建装饰器标记端点所需的 API 类型

### Step 2: 修改 CoinGeckoProClient 类
添加 `is_pro` 属性，自动跳过 Pro 专属端点

### Step 3: 添加提示信息
当用户调用不支持的端点时，提示需要升级到 Pro API

## 需要修改的方法

以下 23+ 个方法需要标记为 "Pro API only"：

Onchain DEX 相关 (12个):
- get_simple_token_price
- get_token_price_batch
- get_dex_pairs
- get_dex_token_trades
- get_pool_liquidity
- get_network_info
- get_supported_networks
- get_dex_aggregated_price
- get_pool_token_reserves
- get_pool_ohlcv
- get_top_traders
- get_pools_megafilter

其他 Pro 专属 (11个):
- get_top_gainers_losers
- get_recently_added
- get_ohlc_range
- get_circulating_supply_chart
- get_total_supply_chart
- get_exchange_volume_chart
- get_nft_markets
- get_nft_market_chart
- get_nft_tickers
- get_treasury_by_coin_id
- get_treasury_transactions
- get_treasury_historical_chart
- get_events
- get_finance
- get_finance_products
- get_defi_data
- get_global_market_cap_chart
- get_coin_status_updates
- get_exchange_status_updates
- get_all_status_updates
- get_derivatives_exchanges
- get_derivatives_exchange_info
- get_trending_pools
- get_search_pools
- get_indexes_list
- get_indexes_by_market_and_id
- get_api_usage
