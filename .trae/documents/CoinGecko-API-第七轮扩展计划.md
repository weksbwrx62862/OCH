# CoinGecko Pro API 功能扩展计划 (第七轮 - 最终完善版)

## 目标
检查并添加遗漏的端点，完善 API 覆盖

## 当前已实现: 约 60 个端点

## 深度对比 pycoingecko 官方库发现的遗漏

### 核心 Coins 端点遗漏

| 端点 | 说明 | 状态 |
|------|------|------|
| `/coins/list` | 所有币种 ID、名称、符号列表 | ❌ 未实现 |
| `/coins/{id}` | 币种完整信息 (非详情) | ❌ 未实现 |
| `/coins/{id}/market_chart` | 市场图表 (非范围版本) | ❌ 只有 range 版本 |

### Exchanges 端点遗漏

| 端点 | 说明 | 状态 |
|------|------|------|
| `/exchanges/{id}` | 交易所详情 | ❌ 未实现 |

### NFTs 端点遗漏

| 端点 | 说明 | 状态 |
|------|------|------|
| `/nfts/{id}` | NFT 详情 (by ID) | ❌ 未实现 |

### Global 端点遗漏

| 端点 | 说明 | 状态 |
|------|------|------|
| `/global` | 全球市场数据 | ❌ 未实现 (只有 market_cap_chart) |

## 计划新增功能

### 1. Coins 基础端点

#### 1.1 获取所有币种列表
```
GET /coins/list
```
- 功能：获取所有支持的币种 ID、名称、符号列表
- 用于后续查询获取币种 ID

#### 1.2 获取币种详情
```
GET /coins/{id}
```
- 功能：获取币种的完整信息（价格、市场数据、开发者数据、社区数据等）

#### 1.3 获取币种市场图表
```
GET /coins/{id}/market_chart
```
- 功能：获取币种历史市场数据（自动粒度）

### 2. Exchanges 端点

#### 2.1 获取交易所详情
```
GET /exchanges/{id}
```

### 3. NFTs 端点

#### 3.1 获取 NFT 详情
```
GET /nfts/{id}
```

### 4. Global 端点

#### 4.1 获取全球市场数据
```
GET /global
```

## 实施步骤

### Step 1: 更新 CoinGeckoProClient
添加以下方法：
1. `get_coins_list()` - 币种列表
2. `get_coin_by_id()` - 币种详情
3. `get_coin_market_chart()` - 币种市场图表 (非范围)
4. `get_exchange_by_id()` - 交易所详情
5. `get_nft_by_id()` - NFT 详情
6. `get_global_data()` - 全球市场数据

### Step 2: 更新 CryptoAnalyzer
添加便捷封装方法

### Step 3: 更新 SKILL.md
添加新命令

### Step 4: 更新 API 参考文档

## 新增 SKILL.md 命令

```bash
crypto coins list                            # 所有币种列表 (12000+ 币种)
crypto coin <coin_id>                       # 币种完整信息
crypto chart <coin_id> <days>              # 币种市场图表
crypto exchange <exchange_id>               # 交易所详情
crypto nft <nft_id>                        # NFT 详情
crypto global data                          # 全球市场数据
```

## 预估工作量

1. CoinGeckoProClient: ~40 行代码
2. CryptoAnalyzer: ~50 行代码
3. SKILL.md: ~12 行
4. API 参考文档: ~35 行
