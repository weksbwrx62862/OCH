# Clawith 飞书 Webhook URL 配置计划

## 问题分析

从代码分析来看，Clawith 生成 webhook URL 的优先级是：
1. 系统设置中的 `public_base_url`（数据库）
2. 环境变量 `PUBLIC_BASE_URL`
3. 默认使用 `request.base_url`（即 localhost）

## 解决方案（按推荐顺序）

### [ ] 方案 1：通过环境变量配置（推荐，最简单）
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在 `.env` 文件中添加 `PUBLIC_BASE_URL` 环境变量
  - 设置为当前的 localtunnel 公网 URL
- **Success Criteria**:
  - Clawith 生成的 webhook URL 使用公网地址
- **Test Requirements**:
  - `programmatic` TR-1.1: 验证 `.env` 文件已更新
  - `programmatic` TR-1.2: 重启服务后验证 webhook URL 是否正确
- **Notes**: 需要重启后端服务

### [ ] 方案 2：通过系统设置 API 配置（如果方案 1 不生效）
- **Priority**: P1
- **Depends On**: 方案 1
- **Description**: 
  - 通过 Clawith 的系统设置 API 配置 `public_base_url`
- **Success Criteria**:
  - 数据库中已保存正确的公网 URL
- **Test Requirements**:
  - `programmatic` TR-2.1: 验证 API 调用成功
  - `programmatic` TR-2.2: 验证 webhook URL 已更新

### [ ] 方案 3：确保 localtunnel 持续运行
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 确保 localtunnel 隧道持续运行
  - 如果重启隧道，需要更新 URL
- **Success Criteria**:
  - localtunnel 服务正常运行
- **Test Requirements**:
  - `programmatic` TR-3.1: 验证 localtunnel 进程在运行
  - `programmatic` TR-3.2: 验证公网 URL 可访问

## 当前公网 URL
```
https://olive-queens-serve.loca.lt
```
