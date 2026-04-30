# CoinGecko Pro API 功能扩展计划 (第二轮)

## 目标
基于 CoinGecko API 文档深度学习，扩展现有功能并添加遗漏的 API 端点

## 当前已实现功能

### Onchain DEX 数据
- ✅ 链上代币价格
- ✅ DEX 交易对
- ✅ DEX 交易记录
- ✅ 流动性池信息
- ✅ 网络信息/支持的网络列表

### Coins 高级端点
- ✅ 涨跌幅排行 (top_gainers_losers)
- ✅ 最近添加的币种 (recently_added)
- ✅ OHLC K线数据

### NFTs 端点
- ✅ NFT 市场数据
- ✅ NFT 价格图表
- ✅ NFT 交易对

### Exchanges 端点
- ✅ 交易所成交量图表

### Global 端点
- ✅ 全球市值图表

### Treasury 端点
- ✅ Treasury 持仓
- ✅ Treasury 交易历史

## 计划新增功能

### 1. Onchain DEX 增强端点

#### 1.1 获取 DEX 聚合价格
```
GET /onchain/dex/v1/tokens/{network}/{token_address}/aggregated_price
```
- 功能：获取代币在所有 DEX 的聚合价格
- 用途：比较不同 DEX 价格，发现最佳交易路径

#### 1.2 获取流动性池的代币储备
```
GET /onchain/dex/v1/pools/{network}/{pool_address}/token_reserves
```
- 功能：获取流动性池中各代币的储备量和比例
- 用途：分析池子健康度、 impermanent loss 风险

#### 1.3 获取 OHLCV 数据 (K线)
```
GET /onchain/dex/v1/pools/{network}/{pool_address}/ohlcv
```
- 参数： timeframe (1m, 5m, 15m, 1h, 4h, 1d), days
- 功能：获取流动性池的 K线数据
- 用途：技术分析、交易策略

#### 1.4 获取交易者排行
```
GET /onchain/traders/{network}/{token_address}/top
```
- 功能：获取特定代币的最大交易者/聪明钱
- 用途：跟踪大户动向

### 2. Treasury 增强端点

#### 2.1 Treasury 历史图表
```
GET /public_treasury/{coin_id}/historical_chart
```
- 功能：获取 Treasury 持仓的历史变化
- 用途：分析机构持仓趋势

### 3. Pool Megafilter 高级过滤

#### 3.1 池子高级过滤
```
GET /onchain/pools/megafilter
```
- 功能：支持多维度过滤（价格变化、流动性、交易量等）
- 排序选项：volume_desc, volume_asc, price_change_desc, price_change_asc, liquidity_desc, liquidity_asc
- 用途：发现潜力池子

### 4. Asset Platforms (Enterprise)

#### 4.1 获取代币列表
```
GET /token_lists/{asset_platform_id}/all.json
```
- 功能：获取特定平台的所有代币列表
- 用途：完整代币生态分析

## 实施步骤

### Step 1: 更新 CoinGeckoProClient 类
在 `main.py` 的 `CoinGeckoProClient` 类中添加：
1. `get_dex_aggregated_price()` - DEX 聚合价格
2. `get_pool_token_reserves()` - 池子代币储备
3. `get_pool_ohlcv()` - 池子 K线数据
4. `get_top_traders()` - 交易者排行
5. `get_treasury_historical_chart()` - Treasury 历史
6. `get_pools_megafilter()` - 池子高级过滤
7. `get_asset_platform_tokens()` - 平台代币列表

### Step 2: 在 CryptoAnalyzer 类中添加便捷方法
添加高层封装方法，简化用户调用

### Step 3: 更新 SKILL.md
添加新命令说明

### Step 4: 更新 API 参考文档
添加新的端点文档

## 新增 SKILL.md 命令

```bash
crypto dex aggregate <network> <token_address>   # DEX 聚合价格
crypto pool reserves <network> <pool_address>   # 池子代币储备
crypto pool ohlcv <network> <pool_address> <timeframe> # K线数据
crypto top traders <network> <token_address>     # 大户排行
crypto treasury history <coin_id> <days>         # Treasury 历史
crypto pool filter <criteria>                    # 池子高级过滤
crypto token list <platform>                    # 平台代币列表
```

## 预估工作量

1. 更新 CoinGeckoProClient 类：约 50 行代码
2. 更新 CryptoAnalyzer 类：约 80 行代码
3. 更新 SKILL.md：约 20 行
4. 更新 API 参考文档：约 60 行
5. 验证测试：约 10 分钟
