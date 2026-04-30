# Anton Roos Finance Skill (Market Tracker) 安装计划

## 信息来源

- **ClawHub**: https://clawhub.ai/anton-roos/finance
- **功能**: 股票/ETF/指数/加密货币/外汇追踪，带缓存和提供者回退

## 技能功能

| 功能 | 说明 |
|------|------|
| 实时报价 | 股票、ETF、指数最新价格 |
| 历史数据 | 30天历史走势 |
| 外汇汇率 | 美元/南非兰特、欧美等 |
| 监控列表 | 本地自选股管理 |
| 缓存机制 | 避免API限流 |

## 数据提供者

| 类型 | 默认提供者 | 说明 |
|------|----------|------|
| 股票/ETF/指数 | Yahoo Finance (yfinance) | 免费，无需Key |
| 外汇 | ExchangeRate-API | 免费，每日更新 |

## 目录结构

```
finance/
├── SKILL.md                    # 主技能文件
├── requirements.txt            # Python依赖
├── scripts/
│   ├── market_quote.py        # 实时报价
│   ├── market_series.py       # 历史数据
│   └── market_watchlist.py    # 自选股管理
├── providers.md               # 提供商配置
└── .cache/                    # 缓存目录
```

## 安装步骤

### 步骤 1: 创建技能目录

```bash
mkdir -p ~/.clawith/data/agents/594e34f8-cdef-4774-811b-026f4a61bdeb/skills/finance/scripts
mkdir -p ~/.clawith/data/agents/594e34f8-cdef-4774-811b-026f4a61bdeb/skills/finance/.cache
```

### 步骤 2: 创建 SKILL.md

```yaml
---
name: finance
description: 追踪股票、ETF、指数、加密货币和外汇的实时价格与历史走势。支持自选股监控列表、本地缓存避免限流。
author: Anton Roos
version: 1.0.0
tags:
  - 股票
  - ETF
  - 外汇
  - 加密货币
  - 市场数据
  - 价格查询
  - 自选股
---
```

### 步骤 3: 创建 requirements.txt

```
yfinance
pandas
requests
```

### 步骤 4: 创建 market_quote.py

```python
#!/usr/bin/env python3
"""
市场报价脚本 - 获取股票/ETF/指数/外汇实时价格
"""

import sys
import json
from datetime import datetime

try:
    import yfinance as yf
    import requests
except ImportError:
    print("请先安装依赖: pip install -r requirements.txt")
    sys.exit(1)


def get_stock_quote(symbol: str):
    """获取股票/ETF/指数报价"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        previous_close = info.get('previousClose')
        change = current_price - previous_close if current_price and previous_close else 0
        change_pct = (change / previous_close * 100) if previous_close else 0

        print("=" * 50)
        print(f"📈 {symbol}")
        print("=" * 50)
        print(f"当前价格: ${current_price:.2f}" if current_price else "价格: N/A")
        print(f"涨跌额: {change:+.2f}")
        print(f"涨跌幅: {change_pct:+.2f}%")
        print(f"昨日收盘: ${previous_close:.2f}" if previous_close else "")
        print(f"市场: {info.get('market', 'N/A')}")
        print(f"时间: {info.get('marketTime', 'N/A')}")
        print("-" * 50)

    except Exception as e:
        print(f"❌ 获取 {symbol} 报价失败: {e}")


def get_fx_rate(pair: str):
    """获取外汇汇率"""
    try:
        base, quote = pair.replace("/", "-").split("-")
        url = f"https://open.er-api.com/v6/latest/{base}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('result') == 'success':
            rate = data['rates'].get(quote)
            print("=" * 50)
            print(f"💱 {pair}")
            print("=" * 50)
            print(f"汇率: {rate:.4f}")
            print(f"更新时间: {data.get('time_last_update_utc', 'N/A')}")
            print("-" * 50)
        else:
            print(f"❌ 获取 {pair} 汇率失败")

    except Exception as e:
        print(f"❌ 获取 {pair} 汇率失败: {e}")


def main():
    if len(sys.argv) < 2:
        print("用法: python market_quote.py <股票代码|外汇对>")
        print("示例: python market_quote.py AAPL")
        print("示例: python market_quote.py USD/ZAR")
        sys.exit(1)

    symbol = sys.argv[1]

    if "/" in symbol or "-" in symbol:
        get_fx_rate(symbol)
    else:
        get_stock_quote(symbol)


if __name__ == "__main__":
    main()
```

### 步骤 5: 创建 market_series.py

```python
#!/usr/bin/env python3
"""
历史走势脚本 - 获取股票历史数据
"""

import sys
import csv
from datetime import datetime

try:
    import yfinance as yf
except ImportError:
    print("请先安装依赖: pip install -r requirements.txt")
    sys.exit(1)


def get_historical_series(symbol: str, days: int = 30):
    """获取历史走势"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=f"{days}d")

        print("=" * 50)
        print(f"📊 {symbol} 历史数据 ({days}天)")
        print("=" * 50)
        print(f"数据点数: {len(hist)}")
        print(f"日期范围: {hist.index[0].strftime('%Y-%m-%d')} 至 {hist.index[-1].strftime('%Y-%m-%d')}")
        print("\n最近5条数据:")
        print("-" * 50)

        for i, (date, row) in enumerate(hist.tail(5).iterrows()):
            print(f"{date.strftime('%Y-%m-%d')}: 开${row['Open']:.2f} 高${row['High']:.2f} 低${row['Low']:.2f} 收${row['Close']:.2f}")

        return hist

    except Exception as e:
        print(f"❌ 获取 {symbol} 历史数据失败: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("用法: python market_series.py <股票代码> [--days <天数>]")
        print("示例: python market_series.py AAPL --days 30")
        sys.exit(1)

    symbol = sys.argv[1]
    days = 30

    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        days = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 30

    get_historical_series(symbol, days)


if __name__ == "__main__":
    main()
```

### 步骤 6: 创建 market_watchlist.py

```python
#!/usr/bin/env python3
"""
自选股管理脚本 - 添加、删除、查看自选股
"""

import sys
import json
import os
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("请先安装依赖: pip install -r requirements.txt")
    sys.exit(1)

CACHE_DIR = Path(__file__).parent.parent / ".cache"
WATCHLIST_FILE = CACHE_DIR / "watchlist.json"


def load_watchlist():
    """加载自选股列表"""
    CACHE_DIR.mkdir(exist_ok=True)
    if WATCHLIST_FILE.exists():
        with open(WATCHLIST_FILE, 'r') as f:
            return json.load(f)
    return []


def save_watchlist(watchlist):
    """保存自选股列表"""
    CACHE_DIR.mkdir(exist_ok=True)
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump(watchlist, f, indent=2)


def add_ticker(symbol):
    """添加自选股"""
    watchlist = load_watchlist()
    if symbol not in watchlist:
        watchlist.append(symbol)
        save_watchlist(watchlist)
        print(f"✅ 已添加 {symbol} 到自选股")
    else:
        print(f"ℹ️ {symbol} 已在自选股中")


def remove_ticker(symbol):
    """删除自选股"""
    watchlist = load_watchlist()
    if symbol in watchlist:
        watchlist.remove(symbol)
        save_watchlist(watchlist)
        print(f"✅ 已从自选股删除 {symbol}")
    else:
        print(f"ℹ️ {symbol} 不在自选股中")


def show_summary():
    """显示自选股汇总"""
    watchlist = load_watchlist()
    if not watchlist:
        print("📋 自选股为空")
        return

    print("=" * 60)
    print("📋 自选股汇总")
    print("=" * 60)

    total_change = 0
    for symbol in watchlist:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            prev_close = info.get('previousClose')
            change = ((price - prev_close) / prev_close * 100) if prev_close and price else 0
            total_change += change

            arrow = "🟢" if change >= 0 else "🔴"
            print(f"{arrow} {symbol}: ${price:.2f} ({change:+.2f}%)")
        except Exception as e:
            print(f"⚠️ {symbol}: 获取失败")

    avg_change = total_change / len(watchlist) if watchlist else 0
    print("-" * 60)
    print(f"平均涨跌幅: {avg_change:+.2f}%")
    print(f"自选股数量: {len(watchlist)}")


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python market_watchlist.py add <股票代码>")
        print("  python market_watchlist.py remove <股票代码>")
        print("  python market_watchlist.py summary")
        sys.exit(1)

    action = sys.argv[1]

    if action == "add" and len(sys.argv) >= 3:
        add_ticker(sys.argv[2].upper())
    elif action == "remove" and len(sys.argv) >= 3:
        remove_ticker(sys.argv[2].upper())
    elif action == "summary":
        show_summary()
    else:
        print("无效命令")


if __name__ == "__main__":
    main()
```

### 步骤 7: 安装依赖并测试

```bash
cd ~/.clawith/data/agents/594e34f8-cdef-4774-811b-026f4a61bdeb/skills/finance
pip install -r requirements.txt
chmod +x scripts/*.py

# 测试
python scripts/market_quote.py AAPL
python scripts/market_series.py AAPL --days 7
python scripts/market_watchlist.py add AAPL
python scripts/market_watchlist.py summary
```

## 触发场景

- "查询苹果股票价格"
- "AAPL 现在多少钱"
- "给我看看苹果最近一个月的走势"
- "帮我添加茅台到自选股"
- "显示我的自选股"
- "美元兑人民币汇率"
