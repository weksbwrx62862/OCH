# 金融技能全面功能验证计划

## 验证日期
2026-04-05

---

## 验证范围

### 1. 东方财富API验证
- [ ] mx-finance-data 数据查询
- [ ] stock-earnings-review 业绩点评

### 2. 多数据源路由器验证
- [ ] 优先使用东方财富API
- [ ] 自动降级机制
- [ ] 缓存功能（24小时TTL）
- [ ] 命令行接口

### 3. finance-assistant验证
- [ ] 意图识别
- [ ] 优先使用东方财富API
- [ ] 技能列表显示
- [ ] 路由到其他技能

### 4. 其他已验证技能验证
- [ ] finance（基础金融）
- [ ] market-data（综合市场）
- [ ] technical（技术分析）
- [ ] portfolio（投资组合）
- [ ] news（新闻资讯）
- [ ] data-source（数据源）
- [ ] risk-assessor（风险评估）
- [ ] crypto-analysis（加密货币）
- [ ] fund-tracker（基金追踪）
- [ ] finance-news-pro（专业财经新闻）

---

## 验证清单

### 东方财富API验证

| 测试项 | 状态 | 说明 |
|---------|------|------|
| mx-finance-data 查询贵州茅台 | [ ] | 验证自然语言查询 |
| mx-finance-data 查询其他股票 | [ ] | 验证多实体支持 |
| stock-earnings-review 实体识别 | [ ] | 验证实体识别功能 |

### 多数据源路由器验证

| 测试项 | 状态 | 说明 |
|---------|------|------|
| 首次查询（东方财富） | [ ] | 验证API调用 |
| 二次查询（缓存） | [ ] | 验证缓存功能 |
| 无缓存查询 | [ ] | 验证 --no-cache 参数 |
| 自定义TTL | [ ] | 验证 --ttl 参数 |

### finance-assistant验证

| 测试项 | 状态 | 说明 |
|---------|------|------|
| 查询贵州茅台（东方财富） | [ ] | 验证优先使用东方财富 |
| 查询加密货币AI500 | [ ] | 验证路由到market-data |
| 显示技能列表 | [ ] | 验证list_skills功能 |

---

## 测试用例

### 东方财富API测试

#### 1. mx-finance-data
```bash
export EM_API_KEY="em_Ybo6o9RLReANUMrTOlin2t7WNhTfId7E"
cd /home/xxh/金融技能/MX/mx-finance-data-1.0.10
python3 scripts/get_data.py --query "贵州茅台近期走势如何"
```

#### 2. stock-earnings-review
```bash
cd /home/xxh/金融技能/MX/stock-earnings-review-1.0.1
python3 scripts/validate_entity.py --query "东方财富 业绩点评"
```

### 多数据源路由器测试

#### 1. 首次查询（东方财富）
```bash
export EM_API_KEY="em_Ybo6o9RLReANUMrTOlin2t7WNhTfId7E"
cd /home/xxh/.clawith/data/agents/594e34f8-cdef-4774-811b-026f4a61bdeb/skills/data-source
python3 scripts/multi_data_source_router.py "贵州茅台近期走势如何"
```

#### 2. 二次查询（缓存）
```bash
python3 scripts/multi_data_source_router.py "贵州茅台近期走势如何"
```

#### 3. 无缓存查询
```bash
python3 scripts/multi_data_source_router.py "贵州茅台近期走势如何" --no-cache
```

#### 4. 自定义TTL
```bash
python3 scripts/multi_data_source_router.py "贵州茅台近期走势如何" --ttl 604800
```

### finance-assistant测试

#### 1. 查询贵州茅台（东方财富）
```bash
export EM_API_KEY="em_Ybo6o9RLReANUMrTOlin2t7WNhTfId7E"
cd /home/xxh/.clawith/data/agents/594e34f8-cdef-4774-811b-026f4a61bdeb/skills/finance-assistant
python3 scripts/assistant.py "贵州茅台近期走势如何"
```

#### 2. 查询加密货币AI500
```bash
python3 scripts/assistant.py "AI500列表"
```

#### 3. 显示技能列表
```bash
python3 scripts/assistant.py --skills
```

---

## 验证报告模板

### 验证总结
- **验证日期**：2026-04-05
- **验证状态**：进行中/已完成
- **通过测试数**：X/Y
- **失败测试数**：X/Y

### 问题记录
- 问题1：
- 问题2：

### 建议
- 建议1：
- 建议2：
