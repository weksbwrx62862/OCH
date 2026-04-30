# 测试计划：crypto-analysis 技能功能验证

## 一、测试目标

验证 crypto-analysis 技能的各项功能是否正常工作，包括数据获取和API调用。

## 二、测试环境

- Python 3.7+
- 依赖：requests, numpy
- 数据源：CoinGecko API, NoFx API

## 三、测试步骤

### 1. 基础价格查询测试
```bash
cd /home/xxh/金融技能/crypto-analysis
python3 scripts/main.py
```
**预期：** 显示BTC, ETH, BNB, SOL的实时价格

### 2. 单币种价格查询测试
```bash
python3 scripts/main.py price BTC
python3 scripts/main.py price ETH
python3 scripts/main.py price SOL
```
**预期：** 显示各币种的详细价格信息

### 3. 历史数据查询测试
```bash
python3 scripts/main.py history BTC 2026-03-01 2026-03-05
```
**预期：** 返回BTC在指定日期范围内的价格数据

### 4. 市场概览测试
```bash
python3 scripts/main.py market
```
**预期：** 显示加密货币市场整体数据（总市值、24h交易量、BTC占比）

### 5. NoFx API 功能测试
- AI500 列表查询
- OI 排行查询
- 资金费率查询
- 多空比查询

## 四、验证标准

- 所有API调用应返回真实数据（非模拟数据）
- 响应时间应在合理范围内
- 数据格式应与文档描述一致

## 五、可能的问题

1. CoinGecko API 可能有速率限制
2. NoFx API 可能需要认证或已更改
3. 网络连接问题可能导致超时