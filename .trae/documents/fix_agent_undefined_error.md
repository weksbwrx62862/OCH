# 修复 `[LLM call error] name 'agent' is not defined` 报错计划

## 问题分析
根据截图报错和代码检索，该错误发生在 `app/api/websocket.py` 文件中的 `call_llm` 函数。
在构建请求 `payload` 时，代码尝试访问 `agent.model_config_overrides`：
```python
"temperature": (agent.model_config_overrides or {}).get("temperature", 0.7),
```
但是在 `call_llm` 函数作用域内，并没有定义 `agent` 变量。获取到的代理对象变量名为 `_agent`，而且被包含在 `if agent_id:` 块中，在某些情况（如 `agent_id` 为空或者数据库查询不到）下，`_agent` 甚至可能未定义，导致在后面使用 `agent` 时抛出未定义的异常 `[LLM call error] name 'agent' is not defined`。

## 解决步骤
1. **修改 `/home/xxh/Clawith/backend/app/api/websocket.py` 文件**:
   - 在 `call_llm` 函数开头初始化 `_agent = None`，保证变量始终被定义。
   - 在构建 `payload` 字典代码（约 214-217 行）前，添加逻辑判断以安全地提取配置 `config_overrides = _agent.model_config_overrides if _agent else {}`。
   - 将所有错误引用的 `agent.model_config_overrides` 替换为 `config_overrides`，修正 `temperature`, `top_p`, `presence_penalty`, `max_tokens` 参数的获取逻辑。

## 预期效果
修复后，WebSocket 聊天接口在调用大语言模型时能够安全且正确地读取模型覆盖配置，不再因为变量拼写错误导致崩溃中断，让对话能够正常进行。