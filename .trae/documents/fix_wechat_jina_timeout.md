## 分析现状 (Current State Analysis)
根据截图和代码探索发现，两个工具报错“调用无返回”的核心原因是超时和网络阻塞：
1. **`jina_read` 工具**：由于当前网络环境无法访问 `r.jina.ai`，`httpx` 请求会在 30 秒超时后抛出异常，返回给 Agent 时没有携带可用数据。同理，`jina_search` 也会因访问 `s.jina.ai` 失败而报错。
2. **`wechat-article-getter` 技能**：该技能使用 `fetch_article.py` 调用 Playwright，其内置页面加载超时设置为 30 秒。然而，Agent 调用它时使用的 `execute_code` 工具默认硬性超时也是 30 秒，这就导致当 Playwright 卡在 `#js_content`（或由于网络/防爬原因加载过慢）时，执行进程会被 `execute_code` 强制杀死，从而导致“技能调用无返回”。

## 解决方案 (Proposed Changes)

1. **为 `jina_read` 和 `jina_search` 添加降级后备方案**
   - **修改文件**：`backend/app/services/agent_tools.py`
   - **修改内容**：
     - 在 `_jina_read` 的 `except` 块中，增加使用 `httpx` 直连 URL 并使用 `BeautifulSoup` 提取网页纯文本的逻辑。
     - 在 `_jina_search` 的 `except` 块中，增加降级调用 `_search_duckduckgo` 的逻辑。

2. **延长 `execute_code` 的最大执行时间**
   - **修改文件**：`backend/app/services/agent_tools.py`
   - **修改内容**：将 `execute_code` 的默认超时时间从 30 秒延长至 60 秒，最大超时时间从 60 秒延长至 120 秒，以便于执行爬虫等耗时操作。并更新工具定义中的描述。

3. **优化 `wechat-article-getter` 的超时与加载策略**
   - **修改文件**：`backend/skills/wechat-article-getter/scripts/fetch_article.py`
   - **修改内容**：
     - 将 `page.goto` 的等待策略从不稳定的 `wait_until="networkidle"` 修改为 `wait_until="domcontentloaded"`。
     - 将默认的 `timeout_ms` 从 30000 降至 25000（25秒），确保它在 `execute_code` 被强杀之前优雅地返回带有错误信息的 JSON。

## 假设和决策 (Assumptions & Decisions)
- 假设服务器上已经安装了 `beautifulsoup4` 和 `httpx`（经检查环境均已存在）。
- 不引入复杂的代理配置，而是采用更具鲁棒性的容错降级（Fallback）方案来保证任务流转不断裂。
- 修改 `wechat-article-getter` 的加载策略有助于跳过某些不必要的静态资源加载，提升响应速度。

## 验证步骤 (Verification Steps)
1. 运行修改后的 `jina_read`（提供一个常规 URL），确认在 Jina 失败时能走降级流程获取到网页文本。
2. 运行修改后的 `jina_search`，确认在 Jina 失败时能返回 DuckDuckGo 的搜索结果。
3. 检查修改后的 `execute_code` 是否允许超时设定为 60 秒。
4. 使用 `fetch_article.py` 提取微信文章，观察其是否能更快速加载或优雅超时。
