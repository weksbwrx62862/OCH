# crypto-analysis 技能验证计划

## 目标
验证 crypto-analysis 技能是否能正常使用 CoinGecko Pro API

## 验证步骤

### Step 1: 测试 API 连接
测试 CoinGecko Pro API 是否能正常连接
- 调用 `ping_coingecko_api()` 方法
- 验证返回状态

### Step 2: 测试基本价格查询
测试基本的市场数据查询功能
- 测试 `get_market_chart()` 获取币种市场图表
- 测试 `get_coin_info()` 获取币种详情

### Step 3: 测试 Onchain DEX 功能
测试新增的 Onchain DEX 数据功能
- 测试 `get_token_price()` 获取链上代币价格
- 测试 `get_dex_pairs()` 获取 DEX 交易对

### Step 4: 测试 Global 功能
测试新增的 Global 数据功能
- 测试 `get_global_market_data()` 获取全球市场数据

### Step 5: 测试 NFT 功能
测试 NFT 数据查询
- 测试 `get_nft_markets()` 获取 NFT 市场数据

## 验证方法
使用 Python 脚本调用各个方法，验证返回值

## 预期结果
- API 连接正常
- 各个方法能返回数据
- 无异常错误
