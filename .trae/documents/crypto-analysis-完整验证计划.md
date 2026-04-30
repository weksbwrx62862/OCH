# crypto-analysis 技能完整验证计划

## 目标
验证 crypto-analysis 技能的所有 API 端点是否能正常使用

## CoinGeckoProClient 端点列表 (约 60+ 端点)

### 1. Onchain DEX 数据 (12+ 端点)
- [ ] `get_simple_token_price()` - 链上代币价格
- [ ] `get_token_price_batch()` - 批量代币价格
- [ ] `get_dex_pairs()` - DEX 交易对
- [ ] `get_dex_token_trades()` - DEX 代币交易
- [ ] `get_pool_liquidity()` - 流动性池信息
- [ ] `get_network_info()` - 网络信息
- [ ] `get_supported_networks()` - 支持的网络列表
- [ ] `get_dex_aggregated_price()` - DEX 聚合价格
- [ ] `get_pool_token_reserves()` - 池子代币储备
- [ ] `get_pool_ohlcv()` - 池子 OHLCV 数据
- [ ] `get_top_traders()` - 交易者排行
- [ ] `get_pools_megafilter()` - 池子高级过滤

### 2. Coins 端点 (10+ 端点)
- [ ] `get_top_gainers_losers()` - 涨跌幅排行
- [ ] `get_recently_added()` - 最近添加的币种
- [ ] `get_ohlc()` - OHLC K线数据
- [ ] `get_coin_tickers()` - 币种交易对
- [ ] `get_coin_history()` - 币种历史数据
- [ ] `get_coin_market_chart()` - 币种市场图表
- [ ] `get_coin_market_chart_range()` - 币种市场图表范围
- [ ] `get_circulating_supply_chart()` - 流通供应量图表
- [ ] `get_total_supply_chart()` - 总供应量图表
- [ ] `get_ohlc_range()` - OHLC 范围查询
- [ ] `get_coin_by_contract()` - 合约查币种
- [ ] `get_contract_market_chart()` - 合约历史图表
- [ ] `get_contract_market_chart_range()` - 合约图表范围
- [ ] `get_coins_list()` - 币种列表
- [ ] `get_coin_by_id()` - 币种详情

### 3. NFTs 端点 (8+ 端点)
- [ ] `get_nft_markets()` - NFT 市场数据
- [ ] `get_nft_market_chart()` - NFT 市场图表
- [ ] `get_nft_tickers()` - NFT 交易对
- [ ] `get_nfts_list()` - NFT 列表
- [ ] `get_nft_by_contract()` - NFT 合约数据
- [ ] `get_nft_contract_chart()` - NFT 合约图表
- [ ] `get_nft_contract_tickers()` - NFT 合约交易对
- [ ] `get_nft_by_id()` - NFT 详情

### 4. Exchanges 端点 (4+ 端点)
- [ ] `get_exchange_volume_chart()` - 交易所成交量图表
- [ ] `get_exchange_tickers()` - 交易所交易对
- [ ] `get_exchange_by_id()` - 交易所详情
- [ ] `get_exchanges_list()` - 交易所列表

### 5. Derivatives 端点 (4+ 端点)
- [ ] `get_derivatives()` - 衍生品交易所
- [ ] `get_derivatives_list()` - 衍生品交易所列表
- [ ] `get_derivatives_exchanges()` - 衍生品交易所列表
- [ ] `get_derivatives_exchange_info()` - 衍生品交易所详情

### 6. Global 端点 (3+ 端点)
- [ ] `get_global_market_cap_chart()` - 全球市值图表
- [ ] `get_global_data()` - 全球市场数据
- [ ] `get_defi_data()` - DeFi 数据

### 7. Treasury 端点 (3+ 端点)
- [ ] `get_treasury_by_coin_id()` - Treasury 持仓
- [ ] `get_treasury_transactions()` - Treasury 交易历史
- [ ] `get_treasury_historical_chart()` - Treasury 历史图表

### 8. Events 端点 (3+ 端点)
- [ ] `get_events()` - 加密货币事件
- [ ] `get_events_countries()` - 事件国家
- [ ] `get_events_types()` - 事件类型

### 9. Status Updates 端点 (3+ 端点)
- [ ] `get_coin_status_updates()` - 币种状态更新
- [ ] `get_exchange_status_updates()` - 交易所状态更新
- [ ] `get_all_status_updates()` - 所有状态更新

### 10. Finance 端点 (2+ 端点)
- [ ] `get_finance()` - 金融平台
- [ ] `get_finance_products()` - 金融产品

### 11. Search/Trending 端点 (3+ 端点)
- [ ] `search()` - 搜索币种
- [ ] `get_trending()` - 热门币种
- [ ] `get_trending_pools()` - 热门池子

### 12. Categories 端点 (2+ 端点)
- [ ] `get_categories_list()` - 分类列表
- [ ] `get_categories()` - 分类市场数据

### 13. Asset Platforms 端点 (2+ 端点)
- [ ] `get_asset_platforms()` - 资产平台列表
- [ ] `get_asset_platform_tokens()` - 平台代币列表

### 14. Indexes 端点 (3+ 端点)
- [ ] `get_indexes()` - 指数列表
- [ ] `get_index()` - 特定指数
- [ ] `get_indexes_list()` - 指数列表
- [ ] `get_indexes_by_market_and_id()` - 按市场ID获取指数

### 15. Companies 端点 (1+ 端点)
- [ ] `get_companies()` - 上市公司持仓

### 16. Exchange Rates 端点 (1+ 端点)
- [ ] `get_exchange_rates()` - BTC 汇率

### 17. Simple API 端点 (3+ 端点)
- [ ] `get_simple_price()` - 增强价格查询
- [ ] `get_simple_token_price_by_address()` - 合约地址查价格
- [ ] `get_supported_currencies()` - 支持的货币

### 18. Coins Markets 端点 (1+ 端点)
- [ ] `get_coins_markets()` - 币种市场数据

### 19. Key/API 端点 (2+ 端点)
- [ ] `get_credits_info()` - 信用点信息
- [ ] `get_api_usage()` - API 使用统计

## 验证执行方式
1. 创建验证脚本
2. 逐个调用端点方法
3. 记录返回状态和数据
4. 统计成功/失败率

## 预期结果
- 端点调用成功率 > 90%
- 无异常错误导致程序崩溃
