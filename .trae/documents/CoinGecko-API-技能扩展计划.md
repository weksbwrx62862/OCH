# CoinGecko Pro API 技能扩展计划

## 目标
扩展现有 crypto-analysis 技能，整合 CoinGecko Pro API 功能

## 当前技能状态
**现有功能**（基于 NoFx API + 公共 CoinGecko API）：
- 实时价格查询
- 历史数据分析
- AI500/AI300 指数分析
- 资金费率分析（OI, netflow, funding rates）
- 多空比分析
- 热力图分析
- 热门查询排行

## CoinGecko Pro API 扩展方案

### 新增独特功能（相对于现有 NoFx API）

#### 1. Onchain DEX 数据（核心新增）
GeckoTerminal DEX 数据 - 这是现有 NoFx API **没有**的独特功能：
- DEX 流动性数据
- DEX 交易对价格
- 合约代币价格（如 ETH 主网代币）
- 流动性池分析

#### 2. 增强现有功能
- **更高的速率限制**：Pro API 比公共 API 更稳定
- **更多数据维度**：增强市场数据覆盖
- **专业数据端点**：Pro 专属的高级市场数据

### 技能扩展结构

```
/home/xxh/金融技能/crypto-analysis/
├── SKILL.md                              # 更新：添加 Pro API 命令
├── scripts/
│   ├── main.py                           # 更新：添加 Pro API 调用方法
│   ├── coingecko_pro_client.py           # 新增：CoinGecko Pro API 客户端
│   └── onchain_dex_analyzer.py           # 新增：链上 DEX 分析器
└── references/
    └── api_reference.md                   # 新增：CoinGecko Pro API 参考
```

## 实施步骤

### 1. 更新 SKILL.md
在现有基础上添加：
- CoinGecko Pro API 认证说明
- 新增命令：
  - `crypto onchain price <contract> <network>` - 获取链上代币价格
  - `crypto dex pairs <network> <token>` - 获取 DEX 交易对
  - `crypto liquidity <pool>` - 流动性池分析

### 2. 创建 CoinGecko Pro API 客户端
**文件**: `scripts/coingecko_pro_client.py`
- Header 认证：`x-cg-pro-api-key`
- API 根地址：`https://pro-api.coingecko.com`
- 信用点追踪
- 速率限制处理
- 错误处理和重试机制

### 3. 创建链上 DEX 分析器
**文件**: `scripts/onchain_dex_analyzer.py`
- `get_onchain_token_price()` - 获取链上代币价格
- `get_dex_pairs()` - 获取 DEX 交易对
- `analyze_pool_liquidity()` - 流动性池分析

### 4. 更新 main.py
在 `CryptoAnalyzer` 类中添加：
- `CoinGeckoProClient` 集成
- 新命令处理逻辑

### 5. 创建 API 参考文档
**文件**: `references/api_reference.md`
- Pro API 认证方式
- Onchain DEX 端点说明
- 请求/响应示例
- 信用点消耗说明

## 技术要点

### API 认证
- Header 方式（推荐）：`x-cg-pro-api-key`
- API 根 URL：`https://pro-api.coingecko.com`
- 用户密钥：`CG-wfikqg8tRikdLj2dGg9TprAF`

### 速率限制
- 每分钟请求限制（Pro API 更高）
- 信用点数消耗（1 成功请求 = 1 信用）

### Onchain DEX 数据（核心）
- 网络支持：ETH, BSC, Polygon, Arbitrum, Optimism 等
- 端点示例：`/onchain/simple/networks/eth/token_price/{address}`

## 验证步骤
1. 测试 Pro API ping 连接
2. 测试链上代币价格查询
3. 测试 DEX 交易对查询
4. 验证新命令与现有功能集成
