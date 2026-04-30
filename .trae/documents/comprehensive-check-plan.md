# 全面异常检查计划

## 已修复的问题回顾
| 问题 | 修复文件 | 状态 |
|------|----------|------|
| Layout.tsx useQuery enabled 条件 | Layout.tsx | ✅ |
| Dashboard.tsx useQuery enabled 条件 | Dashboard.tsx | ✅ |
| agents.py plaza 字段缺失 | agents.py | ✅ |
| permissions.py plaza 字段缺失 | permissions.py | ✅ |
| 数据库 plaza 字段更新 | - | ✅ |

---

## 本次检查任务

### [ ] 任务 1：后端完整健康检查
- **Priority**: P0
- **Depends On**: None
- **Description**: 检查后端是否运行正常，没有未捕获的错误
- **Success Criteria**: 后端健康检查通过，API 完整测试通过
- **Test Requirements**:
  - `programmatic` TR-1.1: 健康检查返回 200
  - `programmatic` TR-1.2: 所有核心 API（登录、agents 列表、agent 详情）测试通过
  - `human-judgement` TR-1.3: 后端日志中无 ERROR 级别错误

---

### [ ] 任务 2：前端完整健康检查
- **Priority**: P0
- **Depends On**: None
- **Description**: 检查前端是否有编译错误或运行时错误
- **Success Criteria**: 前端编译无错误，关键页面可以正常访问
- **Test Requirements**:
  - `programmatic` TR-2.1: TypeScript 编译无错误
  - `human-judgement` TR-2.2: 浏览器控制台无关键错误

---

### [ ] 任务 3：所有路由异常检查
- **Priority**: P1
- **Depends On**: None
- **Description**: 检查所有可能缺少 plaza 字段的 API 路由
- **Success Criteria**: 所有构造 Agent 模型的地方都有完整的 plaza 字段
- **Test Requirements**:
  - `programmatic` TR-3.1: 搜索代码库中所有构造 Agent 模型的地方
  - `programmatic` TR-3.2: 确保所有地方都包含 plaza 字段

---

### [ ] 任务 4：数据库一致性检查
- **Priority**: P1
- **Depends On**: None
- **Description**: 确保数据库中所有记录都有完整的 plaza 字段
- **Success Criteria**: 所有 agents 记录的 plaza_posting_enabled 都有值
- **Test Requirements**:
  - `programmatic` TR-4.1: 验证所有 agents 记录 plaza 字段完整

---

## 修改文件清单
- 可能需要修改：任何构造 Agent 模型但缺少 plaza 字段的文件
