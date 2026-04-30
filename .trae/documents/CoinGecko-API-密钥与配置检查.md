# CoinGecko API 密钥与配置检查

## 问题分析

### API 密钥
密钥：`CG-wfikqg8tRikdLj2dGg9TprAF`

根据文档分析：
- **Demo API** 密钥格式：以 `CG-` 开头
- **Header**: `x-cg-demo-api-key`
- **URL**: `https://api.coingecko.com/api/v3`

### 已确认的代码修改

代码已支持两种模式：
```python
# Demo API (默认)
CoinGeckoProClient(api_key)  # 使用 x-cg-demo-api-key

# Pro API
CoinGeckoProClient(api_key, api_type="pro")  # 使用 x-cg-pro-api-key
```

## Demo API 端点列表

根据 v3.0.1 文档，Demo API 支持的端点：

### 1. Ping
```
GET /api/v3/ping
```

### 2. Simple Endpoints
```
GET /api/v3/simple/price
GET /api/v3/simple/token_price/{id}
GET /api/v3/simple/supported_vs_currencies
```

### 3. Coins Endpoints
```
GET /api/v3/coins/{id}
GET /api/v3/coins/{id}/market_chart
GET /api/v3/coins/{id}/tickers
GET /api/v3/coins/{id}/historical_chart
GET /api/v3/coins/{id}/market_data
GET /api/v3/coins/{id}/coingecko_chart
GET /api/v3/coins/list
```

### 4. Contract Endpoints
```
GET /api/v3/coins/{id}/contract/{contract_address}
GET /api/v3/coins/{id}/contract/{contract_address}/market_chart
```

### 5. Asset Platforms
```
GET /api/v3/asset_platforms
```

### 6. Categories
```
GET /api/v3/coins/categories
GET /api/v3/coins/categories/list
```

### 7. Exchanges
```
GET /api/v3/exchanges
GET /api/v3/exchanges/{id}
GET /api/v3/exchanges/list
```

### 8. Derivatives
```
GET /api/v3/derivatives
GET /api/v3/derivatives/list
```

### 9. ETFs
```
GET /api/v3/etfs
GET /api/v3/etfs/{id}
```

### 10. Global
```
GET /api/v3/global
```

### 11. Exchange Rates
```
GET /api/v3/exchange_rates
```

### 12. Search
```
GET /api/v3/search
```

### 13. Trending
```
GET /api/v3/search/trending
```

### 14. NFTs
```
GET /api/v3/nfts/{id}
GET /api/v3/nfts/{id}/market_chart
GET /api/v3/nfts/list
GET /api/v3/nfts/{id}/tickers
```

## 当前网络状态

| 测试 | 结果 |
|------|------|
| `api.coingecko.com` | ❌ 连接失败 |
| `pro-api.coingecko.com` | ❌ 连接超时 |

**结论**：网络不可达，但代码配置正确。

## 验证方法

### 验证 API 密钥是否有效

用户可以在本地环境执行：
```bash
curl -X GET "https://api.coingecko.com/api/v3/ping" -H "x-cg-demo-api-key: CG-wfikqg8tRikdLj2dGg9TprAF"
```

如果返回 `{"gecko_says":"(V3) To the Moon!"}` 则密钥有效。

## 配置文件路径
- `/home/xxh/金融技能/crypto-analysis/scripts/main.py` - 已修改支持 Demo API
- `/home/xxh/金融技能/crypto-analysis/scripts/quick_verify.py` - 快速验证脚本
