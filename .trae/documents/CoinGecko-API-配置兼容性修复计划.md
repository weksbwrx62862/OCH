# CoinGecko API 配置兼容性修复计划

## 目标
根据 API 类型自动启用/禁用对应的端点功能

## 设计方案

### API 类型与功能映射

#### Demo API (免费) - 启用以下功能
| 类别 | 端点 |
|------|------|
| Ping | /ping |
| Simple | /simple/price, /simple/token_price/{id}, /simple/supported_vs_currencies |
| Coins | /coins/list, /coins/markets, /coins/{id} |
| | /coins/{id}/tickers, /coins/{id}/history |
| | /coins/{id}/market_chart, /coins/{id}/market_chart/range |
| | /coins/{id}/ohlc |
| Exchanges | /exchanges, /exchanges/list, /exchanges/{id} |
| Derivatives | /derivatives, /derivatives/list |
| Global | /global, /exchange_rates |
| Search | /search, /search/trending |
| NFTs | /nfts/{id}, /nfts/list |
| Asset Platforms | /asset_platforms |

#### Pro API (付费) - 在 Demo 基础上增加
| 类别 | 端点 |
|------|------|
| Onchain DEX | /onchain/* (全部) |
| Top Gainers | /coins/top_gainers_losers |
| New Coins | /coins/list/new |
| OHLC Range | /coins/{id}/ohlc/range |
| Supply Charts | /coins/{id}/circulating_supply_chart, /total_supply_chart |
| Exchange Volume | /exchanges/{id}/volume_chart/range |
| NFT Markets | /nfts/markets, /nfts/{id}/market_chart, /nfts/{id}/tickers |
| Treasury | /public_treasury/* |
| Global Charts | /global/market_cap_chart, /global/decentralized_finance_defi |
| Finance | /finance, /finance_products |
| Events | /events, /events/countries, /events/types |
| Status Updates | /status_updates, /coins/{id}/status_updates |
| Indexes | /indexes/* |
| Derivatives Ex | /derivatives/exchanges/* |
| Search Pools | /search/pools |
| Key | /key |

## 实施步骤

### Step 1: 修改 CoinGeckoClient 类
- 添加 `api_type` 属性 ('demo' 或 'pro')
- 添加 `PRO_ONLY_ENDPOINTS` 常量列表
- 在 `_make_request` 前检测是否为 Pro 专属端点
- 如果是 Demo API 调用 Pro 端点，抛出友好提示或跳过

### Step 2: 添加端点类型装饰器
使用装饰器标记端点所需的 API 类型

### Step 3: 更新 SKILL.md
添加 API 类型说明

## 核心代码逻辑

```python
PRO_ONLY_ENDPOINTS = [
    'onchain', 'top_gainers', 'list/new',
    'ohlc/range', 'circulating_supply', 'total_supply',
    'volume_chart/range', 'nfts/markets', 'public_treasury',
    'market_cap_chart', 'decentralized_finance',
    'finance', 'events', 'status_updates',
    'indexes', 'derivatives/exchanges', 'search/pools', 'key'
]

def _make_request(self, endpoint, ...):
    if self.api_type == 'demo':
        for pro_endpoint in PRO_ONLY_ENDPOINTS:
            if pro_endpoint in endpoint:
                raise Exception(f"端点 {endpoint} 需要 Pro API")
    # 正常请求...
```

## 预估工作量

1. 修改 CoinGeckoClient 类：约 30 行
2. 添加端点类型检测：约 20 行
3. 更新 SKILL.md：约 15 行
4. 测试验证：约 10 分钟
