# NoFx API 功能完善计划

## 一、现状分析

### 已有功能 (正常工作)
- ✅ AI500 Index (list, coin, stats)
- ✅ OI Rankings (top-ranking, low-ranking, top)
- ✅ Netflow Rankings (inflow, outflow)
- ✅ Funding Rate (top, low, symbol)
- ✅ Long-Short Ratio (list, symbol)
- ✅ Heatmap (future, spot)
- ✅ Query Ranking

### 缺失功能 (需要添加)
1. **AI300 Quantitative Model** - 新增
2. **Market Data** - gainers/losers/coin
3. **Upbit Exchange** - 韩国交易所数据
4. **OI Market Cap Ranking** - 完善
5. **Heatmap List** - 汇总排行
6. **Enhanced Fund Flow** - 支持更多时间周期和类型

## 二、代码修改计划

### 文件: /home/xxh/金融技能/crypto-analysis/scripts/main.py

#### 1. 新增 AI300 量化模型方法 (约50行)

```python
# AI300 量化模型
def get_ai300_list(self, limit=40):
    """获取AI300量化模型排行榜"""
    data = self._call_nofx_api("/ai300/list", {"limit": limit})
    if data:
        return data
    return self._get_mock_ai300_list(limit)

def get_ai300_stats(self):
    """获取AI300统计数据"""
    data = self._call_nofx_api("/ai300/stats")
    if data:
        return data
    return self._get_mock_ai300_stats()

def _get_mock_ai300_list(self, limit):
    return {"data": [...], "limit": limit, "note": "mock"}

def _get_mock_ai300_stats(self):
    return {"total_coins": 300, "signal_counts": {...}, "note": "mock"}
```

#### 2. 新增 Market Data 方法 (约80行)

```python
# 市场数据
def get_market_gainers(self, duration="24h"):
    """获取涨幅榜"""
    data = self._call_nofx_api("/market/gainers", {"duration": duration})
    if data:
        return data
    return self._get_mock_market_movers("gainers", duration)

def get_market_losers(self, duration="24h"):
    """获取跌幅榜"""
    data = self._call_nofx_api("/market/losers", {"duration": duration})
    if data:
        return data
    return self._get_mock_market_movers("losers", duration)

def get_market_coin(self, symbol, include="price_change,netflow,oi,ai500"):
    """获取单币种聚合数据"""
    pair = self.pair_map.get(symbol.upper(), symbol.upper() + "USDT")
    data = self._call_nofx_api(f"/market/coin/{pair}", {"include": include})
    if data:
        return data
    return self._get_mock_coin_data(pair)

def _get_mock_market_movers(self, type_, duration):
    return {"data": [...], "type": type_, "duration": duration, "note": "mock"}

def _get_mock_coin_data(self, symbol):
    return {"symbol": symbol, "price": 0, "note": "mock"}
```

#### 3. 新增 Upbit 交易所方法 (约60行)

```python
# Upbit 交易所
def get_upbit_rank(self, limit=20):
    """获取Upbit热门币种排行"""
    data = self._call_nofx_api("/upbit/rank", {"limit": limit})
    if data:
        return data
    return self._get_mock_upbit_rank(limit)

def get_upbit_inflow(self, limit=20, duration="1h"):
    """获取Upbit资金净流入排行"""
    data = self._call_nofx_api("/upbit/inflow", {"limit": limit, "duration": duration})
    if data:
        return data
    return self._get_mock_upbit_flow("inflow", limit, duration)

def get_upbit_outflow(self, limit=20, duration="1h"):
    """获取Upbit资金净流出排行"""
    data = self._call_nofx_api("/upbit/outflow", {"limit": limit, "duration": duration})
    if data:
        return data
    return self._get_mock_upbit_flow("outflow", limit, duration)
```

#### 4. 完善 OI Market Cap 方法 (约30行)

```python
def get_oi_cap_ranking(self, limit=20):
    """获取OI市值排名 - 按OI值(USDT)排序"""
    data = self._call_nofx_api("/oi-cap/ranking", {"limit": limit})
    if data:
        return data
    return self._get_mock_oi_cap_ranking(limit)
```

#### 5. 增强 Fund Flow 方法 (约40行)

```python
# 增强版资金流向 - 支持更多参数
def get_netflow_inflow(self, limit=20, duration="1h", type_="institution", trade="future"):
    """获取资金净流入榜 - 增强版"""
    data = self._call_nofx_api("/netflow/top-ranking", {
        "limit": limit,
        "duration": duration,
        "type": type_,
        "trade": trade
    })
    if data:
        return data
    return self._get_mock_netflow("inflow", limit, duration, type_, trade)

def get_netflow_outflow(self, limit=20, duration="1h", type_="institution", trade="future"):
    """获取资金净流出榜 - 增强版"""
    data = self._call_nofx_api("/netflow/low-ranking", {
        "limit": limit,
        "duration": duration,
        "type": type_,
        "trade": trade
    })
    if data:
        return data
    return self._get_mock_netflow("outflow", limit, duration, type_, trade)
```

#### 6. 新增长空比详情方法 (约20行)

```python
def get_long_short_symbol(self, symbol):
    """获取特定币种多空比历史"""
    pair = self.pair_map.get(symbol.upper(), symbol.upper() + "USDT")
    data = self._call_nofx_api(f"/long-short/{pair}")
    if data:
        return data
    return self._get_mock_long_short(pair)
```

#### 7. 新增 Heatmap 汇总方法 (约20行)

```python
def get_heatmap_list(self, trade="future", limit=30):
    """获取热力图汇总排行"""
    data = self._call_nofx_api("/heatmap/list", {"trade": trade, "limit": limit})
    if data:
        return data
    return self._get_mock_heatmap_list(trade, limit)
```

## 三、预估工作量

| 功能 | 行数 | 复杂度 |
|------|------|--------|
| AI300 量化模型 | ~50 | 低 |
| Market Data | ~80 | 中 |
| Upbit 交易所 | ~60 | 中 |
| OI Market Cap 完善 | ~30 | 低 |
| 增强 Fund Flow | ~40 | 低 |
| 长期/短期详情 | ~20 | 低 |
| Heatmap 汇总 | ~20 | 低 |
| **总计** | **~300行** | - |

## 四、验证计划

1. 每个新增方法单独测试
2. 检查 API 返回数据格式
3. 验证模拟数据降级机制
4. 更新 SKILL.md 文档