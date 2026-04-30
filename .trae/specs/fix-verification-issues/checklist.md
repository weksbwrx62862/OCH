# Checklist — 部署验证问题迭代修复

## Bug 修复
- [x] Agent 模型 sessions 关系添加级联删除配置
- [x] 删除有关联 Session 的 Agent 不再返回 500 IntegrityError
- [x] MCP 服务器详情 GET 路由已添加
- [x] GET /mcp/servers/{id} 返回 200 + 服务器详情
- [x] GET /mcp/servers/{不存在id} 返回 404
- [x] _find_tool() 支持大小写不敏感匹配
- [x] GET /tools/bash 返回 200（与 /tools/Bash 一致）

## 修复后验证
- [x] Agent 级联删除：创建Agent→创建Session→删除Agent→无500
- [x] MCP 详情：创建→GET详情→200，不存在→404
- [x] 工具大小写：/tools/bash→200，/tools/Bash→200，/tools/webfetch→200
- [x] 全量回归验证通过率 100%
