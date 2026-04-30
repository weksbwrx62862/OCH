# 解决 yfinance 限流问题方案

## 问题分析

yfinance 免费 API 有以下限制：
- 每分钟请求次数限制
- 频繁请求会被临时封禁
- 缓存机制不完善

## 解决方案

### 方案1：强化缓存机制（推荐）

**原理**：将获取的数据缓存到本地文件，减少重复请求

```python
# 缓存策略
CACHE_TTL = {
    "quote": 300,      # 报价缓存5分钟
    "history": 3600,  # 历史数据缓存1小时
    "info": 1800,     # 基本面缓存30分钟
}
```

**实现**：
1. 数据获取前先检查缓存
2. 缓存命中则直接返回
3. 缓存过期才重新请求
4. 请求失败自动降级到缓存数据

### 方案2：添加请求延迟

**原理**：控制请求频率，避免触发限流

```python
import time
from functools import wraps

def rate_limit(max_calls=10, period=60):
    """每分钟最多10次请求"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 检查是否超过限制
            # 如果超过，等待一段时间
            time.sleep(0.5)  # 每次请求间隔0.5秒
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### 方案3：多数据源备份

**原理**：当 yfinance 限流时，自动切换到其他免费数据源

| 数据源 | 限制 | 适用场景 |
|--------|------|----------|
| yfinance | 有严格限流 | 主要数据源 |
| Alpha Vantage | 25次/天免费 | 美股备份 |
| Finnhub | 60次/分钟 | 美股备份 |
| ExchangeRate-API | 无明确限制 | 外汇 |
| AkShare | 无明确限制 | A股 |

### 方案4：使用代理/轮换IP

**原理**：通过不同的网络出口分散请求

```python
# 使用不同的 User-Agent
HEADERS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
]
```

## 推荐实施方案

### 综合方案：缓存 + 延迟 + 多源备份

```
请求 → 检查缓存 → 缓存命中 → 返回数据
         ↓
      缓存未命中
         ↓
      检查限流状态 → 限流中 → 使用备份源
         ↓
      未限流 → 延迟请求 → 获取数据 → 更新缓存
```

## 具体实施步骤

### 步骤1：更新 yfinance_wrapper.py

创建统一的 yfinance 封装，增加：
- 缓存机制
- 请求延迟
- 错误重试
- 多数据源备份

```python
# scripts/yfinance_wrapper.py
import yfinance as yf
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

class YfinanceWrapper:
    def __init__(self, cache_dir=".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 0.5秒间隔

    def _rate_limit(self):
        """请求频率控制"""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _get_cache(self, key, ttl):
        """获取缓存"""
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                data = json.load(f)
                cache_time = datetime.fromisoformat(data['timestamp'])
                if datetime.now() - cache_time < timedelta(seconds=ttl):
                    return data['value']
        return None

    def _set_cache(self, key, value):
        """设置缓存"""
        cache_file = self.cache_dir / f"{key}.json"
        with open(cache_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'value': value
            }, f)

    def get_quote(self, symbol):
        """获取报价（带缓存）"""
        cache_key = f"quote_{symbol}"
        cached = self._get_cache(cache_key, ttl=300)  # 5分钟缓存
        if cached:
            return cached

        self._rate_limit()
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            self._set_cache(cache_key, info)
            return info
        except Exception as e:
            # 限流时返回缓存
            return cached or {}
```

### 步骤2：添加备份数据源

当 yfinance 失败时，自动切换到备份源

```python
def get_quote_with_fallback(symbol):
    """带备份的报价获取"""
    # 尝试 yfinance
    try:
        return yfinance_wrapper.get_quote(symbol)
    except Exception as e:
        print(f"yfinance失败: {e}")

    # 尝试 Alpha Vantage
    try:
        return alpha_vantage.get_quote(symbol)
    except Exception as e:
        print(f"AlphaVantage失败: {e}")

    # 返回缓存（如果有）
    cached = yfinance_wrapper._get_cache(f"quote_{symbol}", ttl=86400)
    if cached:
        return cached

    return {}
```

### 步骤3：更新所有脚本使用新的封装

修改 `global.py`、`commodities.py`、`crypto.py` 等脚本，使用封装好的 wrapper

## 预期效果

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| API请求次数 | 每次都请求 | 减少80%+ |
| 限流频率 | 频繁触发 | 几乎不触发 |
| 数据可用性 | 限流时无数据 | 限流时用缓存 |
| 响应速度 | 受网络影响 | 缓存命中即返回 |

## 实施优先级

1. **高优先级**：实现 yfinance_wrapper 缓存封装
2. **中优先级**：添加请求延迟控制
3. **低优先级**：实现多数据源备份
