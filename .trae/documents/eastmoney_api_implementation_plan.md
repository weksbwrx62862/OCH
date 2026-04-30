# 东方财富API实施计划

## 目标

使用东方财富妙想API作为主要数据源，yfinance/akshare作为降级方案，并配置24小时以上的缓存TTL。

---

## 实施步骤

### 1. 配置东方财富API密钥

**文件位置**：`/home/xxh/金融技能/MX/API.txt`  
**密钥**：`em_Ybo6o9RLReANUMrTOlin2t7WNhTfId7E`

配置方式：
```bash
export EM_API_KEY="em_Ybo6o9RLReANUMrTOlin2t7WNhTfId7E"
```

---

### 2. 验证东方财富API功能

#### 2.1 测试mx-finance-data技能

**位置**：`/home/xxh/金融技能/MX/mx-finance-data-1.0.10`

**测试命令**：
```bash
cd /home/xxh/金融技能/MX/mx-finance-data-1.0.10
python3 scripts/get_data.py --query "贵州茅台近期走势如何"
```

**验证内容**：
- 自然语言查询功能
- A股数据获取
- Excel文件输出

---

#### 2.2 测试stock-earnings-review技能

**位置**：`/home/xxh/金融技能/MX/stock-earnings-review-1.0.1`

**测试命令**：
```bash
cd /home/xxh/金融技能/MX/stock-earnings-review-1.0.1
python3 scripts/validate_entity.py --query "东方财富 业绩点评"
```

**验证内容**：
- 实体识别
- 业绩点评生成
- PDF/Word附件输出

---

### 3. 多数据源路由策略

#### 数据源优先级

```
1. 东方财富 mx-finance-data（EM_API_KEY）→ 首选
2. Tushare Pro（TUSHARE_TOKEN）→ 备选
3. yfinance → 降级
4. akshare → 降级
```

#### 降级逻辑

- 东方财富API失败 → 尝试Tushare
- Tushare失败 → 尝试yfinance
- yfinance失败 → 尝试akshare
- 所有API失败 → 使用已缓存的本地数据

---

### 4. 缓存策略优化

#### 4.1 现有缓存检查

**位置**：`/home/xxh/.clawith/data/agents/594e34f8-cdef-4774-811b-026f4a61bdeb/skills/data-source`

#### 4.2 缓存TTL配置

**目标**：24小时或更长

| 数据类型 | TTL建议 |
|----------|---------|
| 股票基础信息 | 7天 |
| 实时行情 | 1小时 |
| 财务报表 | 30天 |
| 技术指标 | 24小时 |
| 宏观经济数据 | 7天 |

---

### 5. 技能集成

#### 5.1 在finance-assistant中集成东方财富

修改意图识别逻辑，优先使用东方财富数据源。

#### 5.2 在data-source中集成

更新data-source技能，添加东方财富API作为新的数据源。

---

## 技术细节

### 东方财富API特点

**优势**：
- 覆盖A港美股、基金、债券
- 自然语言查询
- 实时行情、财务报表完整
- 限流宽松

**限制**：
- 单次查询最多5个实体

### yfinance降级使用

**场景**：
- 东方财富API不可用时
- 查询简单的历史数据时
- 不需要完整财务报表时

---

## 验证清单

- [ ] 东方财富API密钥配置成功
- [ ] mx-finance-data技能测试通过
- [ ] stock-earnings-review技能测试通过
- [ ] 多数据源降级逻辑实现
- [ ] 缓存TTL配置为24小时
- [ ] 集成到finance-assistant
- [ ] 集成到data-source
- [ ] 完整功能验证

---

## 相关文档

- `/home/xxh/.trae/documents/api_rate_limit_solutions.md` - API限流解决方案
- `/home/xxh/金融技能/MX/mx-finance-data-1.0.10/SKILL.md` - 东方财富数据源使用说明
