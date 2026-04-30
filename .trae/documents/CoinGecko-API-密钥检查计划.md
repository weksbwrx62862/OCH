# CoinGecko API 密钥类型检查与修复计划

## 问题分析

用户提供的 API 密钥可能是 **Demo API** 密钥，而不是 Pro API 密钥。

### Demo API vs Pro API 区别

| 特性 | Demo API | Pro API |
|------|----------|---------|
| Header | `x-cg-demo-api-key` | `x-cg-pro-api-key` |
| 根 URL | `https://api.coingecko.com/api/v3` | `https://pro-api.coingecko.com/api/v3` |
| Onchain DEX | ❌ 不支持 | ✅ 支持 |
| 速率限制 | 低 | 高 |
| 信用点 | 有限 | 根据订阅计划 |

## 检查步骤

### Step 1: 确认密钥类型
根据 API Key 格式判断：
- Demo Key: 通常以 `CG-` 开头
- Pro Key: 也以 `CG-` 开头，需要实际测试确认

### Step 2: 测试 API 连接
尝试使用 Demo API 端点测试连接

### Step 3: 修复代码（如果需要）
如果用户只有 Demo API，需要修改：
1. 将 `base_url` 从 `https://pro-api.coingecko.com` 改为 `https://api.coingecko.com`
2. 将 `x-cg-pro-api-key` 改为 `x-cg-demo-api-key`
3. 移除不支持的 Onchain DEX 端点调用（或添加备选方案）

### Step 4: 验证 Demo API 功能
测试基本端点是否可用

## 需要修改的文件

### main.py
```python
# 当前配置 (Pro API)
self.base_url = "https://pro-api.coingecko.com/api/v3"
self.headers = {"x-cg-pro-api-key": api_key, "Accept": "application/json"}

# 需要改为 (Demo API)
self.base_url = "https://api.coingecko.com/api/v3"
self.headers = {"x-cg-demo-api-key": api_key, "Accept": "application/json"}
```

## 预估工作量

1. 检查密钥类型：5 分钟
2. 修改代码支持 Demo API：15 分钟
3. 验证 Demo API 功能：10 分钟
