# MX 金融技能安装计划

## 核心目标

1. 使用您的 MX API Key (`em_Ybo6o9RLReANUMrTOlin2t7WNhTfId7E`) 创建 MX 金融技能
2. 实现 MX 系列的核心功能
3. 设计 API 过期后的降级策略

## API 能力

东方财富 MX API 提供：
- **mx_finance_data** - 自然语言查数（行情/财务/估值）
- **mx_macro_data** - 宏观经济查询（GDP/CPI/PMI）
- **mx_stocks_screener** - 自然语言选股
- **mx_finance_search** - 资讯搜索
- **industry_research_report** - 行业研究报告
- **mx_financial_assistant** - 全能金融问答

## 实施步骤

### 步骤 1: 创建 mx-finance 技能目录

```
~/.clawith/data/agents/594e34f8-cdef-4774-811b-026f4a61bdeb/skills/mx-finance/
├── SKILL.md
├── requirements.txt
└── scripts/
    ├── get_data.py        # 统一路由入口
    ├── finance_query.py   # 金融数据查询
    ├── macro_query.py    # 宏观数据查询
    ├── screener.py       # 选股筛选
    ├── news_search.py    # 资讯搜索
    └── report.py         # 报告生成
```

### 步骤 2: 配置 API Key

在 SKILL.md 中设置环境变量：
```bash
export EM_API_KEY="em_Ybo6o9RLReANUMrTOlin2t7WNhTfId7E"
```

### 步骤 3: 创建核心脚本

每个脚本调用东方财富 MX API：
```python
# 示例：金融数据查询
import httpx

EM_API_KEY = os.getenv("EM_API_KEY")
BASE_URL = "https://ai.eastmoney.com/mxClaw/api"

def query_finance(query: str):
    response = httpx.post(
        f"{BASE_URL}/finance_query",
        headers={"Authorization": f"Bearer {EM_API_KEY}"},
        json={"query": query}
    )
    return response.json()
```

### 步骤 4: 实现降级策略

当 MX API 过期时，降级到免费数据源：

| 功能 | MX API | 降级方案 |
|------|--------|----------|
| A股行情 | ✅ | AkShare (免费) |
| 财务数据 | ✅ | tushare-finance (需Token) |
| 宏观数据 | ✅ | AkShare宏观数据 (免费) |
| 选股 | ✅ | AkShare选股器 (免费) |
| 资讯搜索 | ✅ | 东方财富免费接口 |
| 报告生成 | ✅ | 简化为资讯汇总 |

### 步骤 5: 添加智能路由

```python
def get_data(query: str, use_mx: bool = True):
    """智能选择数据源"""
    if use_mx and os.getenv("EM_API_KEY"):
        return call_mx_api(query)  # MX API
    else:
        return call_free_api(query)  # AkShare等免费方案
```

## 核心技能功能

### 1. 金融数据查询 (mx_finance_data)

**命令**：
```bash
python scripts/finance_query.py "贵州茅台近期走势如何"
python scripts/finance_query.py "英伟达现在的PE"
```

**输出**：CSV 文件 + 描述文件

### 2. 宏观数据查询 (mx_macro_data)

**命令**：
```bash
python scripts/macro_query.py "中国GDP"
python scripts/macro_query.py "美国CPI"
```

**输出**：CSV 文件 (按年/季/月频率)

### 3. 智能选股 (mx_stocks_screener)

**命令**：
```bash
python scripts/screener.py --query "股价大于100元，市盈率最低的50只" --type A股
```

**输出**：CSV 文件

### 4. 资讯搜索 (mx_finance_search)

**命令**：
```bash
python scripts/news_search.py "寒武纪最新研报"
```

**输出**：TXT 文件

### 5. 行业报告 (industry_research_report)

**命令**：
```bash
python scripts/report.py --query "半导体行业"
```

**输出**：PDF + DOCX 文件

## API 过期检测与处理

```python
def check_api_status():
    """检测 API 是否可用"""
    try:
        response = httpx.get(f"{BASE_URL}/status")
        return response.json().get("available", False)
    except:
        return False

def fallback_to_free(query: str):
    """降级到免费数据源"""
    if "GDP" in query or "CPI" in query:
        return ak_share_macro(query)
    elif "股价" in query or "市盈率" in query:
        return akshare_quote(query)
    else:
        return {"error": "API已过期，请配置免费数据源"}
```

## 依赖安装

```bash
pip install httpx pandas openpyxl akshare
```

## 触发场景

- "查询贵州茅台的财务数据"
- "中国GDP走势如何"
- "帮我选低估值的A股"
- "半导体行业最新资讯"
- "生成一份新能源汽车行业报告"
- "分析一下当前市场"
