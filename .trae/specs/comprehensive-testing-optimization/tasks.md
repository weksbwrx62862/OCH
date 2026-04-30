# OpenClaw-Harness 全面测试优化 - 任务清单

## 阶段一：高优先级测试补充 🔴

### Task 1: 修复测试基础设施问题
- [x] **Task 1.1**: 修复 conftest.py 事件循环警告 ✅
  - 将 `asyncio.get_event_loop()` 替换为 `asyncio.new_event_loop()` 或使用 pytest-asyncio 的 event_loop fixture
  - 确保不再产生 DeprecationWarning
  - 验证：运行现有 34 个测试，确认无警告输出

- [x] **Task 1.2**: 增强 conftest.py 测试辅助函数 ✅
  - 添加更多通用 fixture（sample_task, sample_skill, sample_tool, sample_permission）
  - 添加 API 响应断言辅助函数
  - 添加数据库清理辅助函数
  - 验证：新 fixture 可被其他测试文件正确导入使用

### Task 2: Service 层单元测试（7 个模块）✅
- [x] **Task 2.1**: 编写 session_service.py 测试 ✅ (28个测试)
- [x] **Task 2.2**: 编写 skill_service.py 测试 ✅ (24个测试)
- [x] **Task 2.3**: 编写 tool_service.py 测试 ✅ (49个测试，含35+安全测试)
- [x] **Task 2.4**: 编写 permission_service.py 测试 ✅ (61个测试)
- [x] **Task 2.5**: 编写 plugin_service.py 测试 ✅ (29个测试)
- [x] **Task 2.6**: 编写 coordinator_service.py 测试 ✅ (35个测试)
- [x] **Task 2.7**: 编写 subagent_executor.py 测试 ✅ (45个测试)

**Service 层总计：271 个测试，全部通过 ✅**

### Task 3: API 模块扩展测试（11 个模块）
- [x] **Task 3.1**: Tasks API 测试 ✅ (23个测试)
- [x] **Task 3.2**: Skills API 测试 ✅ (21个测试)
- [x] **Task 3.3**: Tools API 测试 ✅ (17个测试)
- [x] **Task 3.4**: Permissions API 测试 ✅ (36个测试)

- [x] **Task 3.5**: Audit API 测试 ✅ (12个测试)
- [x] **Task 3.6**: Memory API 测试 ✅ (20个测试)
- [x] **Task 3.7**: MCP API 测试 ✅ (16个测试)
- [x] **Task 3.8**: Channels API 测试 ✅ (22个测试)
- [x] **Task 3.9**: Config API 测试 ✅ (15个测试)
- [x] **Task 3.10**: Sandbox API 测试 ✅ (17个测试)
- [x] **Task 3.11**: Coordinator API 测试 ✅ (22个测试)

**API 层总计：221 个测试，全部通过 ✅**

### Task 4: 集成测试场景 ✅
- [x] **Task 4.1**: 完整对话流程集成测试 ✅ (11个测试，5通过/6跳过)
  - 场景 1：Agent → Session → Chat → Message 完整流程
  - 场景 2：多轮对话 + 工具调用模拟
  - 场景 3：Session 暂停/恢复/删除生命周期
  - 场景 4：权限控制端到端验证（Admin vs User）
  - 使用真实数据库事务（非完全 Mock）
  - 预计测试数：8-10 个

---

## 阶段二：中优先级优化 🟡

### Task 5: Pydantic V2 配置迁移
- [x] **Task 5.1**: 迁移 Settings 类配置 ✅
  - 修改文件：`backend/app/config.py`
  - 将 `class Config:` 替换为 `model_config = ConfigDict(...)`
  - 保持所有功能兼容（env_file, case_sensitive 等）
  - 验证：`python -c "from app.config import get_settings; s = get_settings(); print(s.APP_NAME)"`

- [x] **Task 5.2**: 更新其他 Pydantic 模型（如有）✅
  - 检查所有使用旧 Config 方式的模型（结果：无需迁移）
  - 统一迁移到 V2 语法
  - 验证：完整测试套件通过无报错

### Task 6: 前端单元测试框架搭建 ✅
- [x] **Task 6.1**: 安装 Jest 和 React Testing Library ✅
  - 已安装：jest, @testing-library/react, @testing-library/jest-dom, ts-jest, jest-environment-jsdom
  - 配置文件：jest.config.js, jest.setup.ts 已就绪
  - npm scripts 已配置

- [x] **Task 6.2**: 编写核心组件测试 ✅ (48个测试，7个套件)
  - `__tests__/app/layout.test.tsx` (2个测试)
  - `__tests__/app/login.test.tsx` (6个测试)
  - `__tests__/app/agents.test.tsx` (7个测试)
  - `__tests__/app/HomePage.test.tsx` (原有)
  - `__tests__/stores/appStore.test.ts` (原有)
  - `__tests__/lib/api.test.ts` (原有)
  - `__tests__/components/Sidebar.test.tsx` (原有)
  - 验证：`npm run test` 48/48 全部通过

---

## 阶段三：低优先级优化 🟢

### Task 7: 依赖安全修复 ✅
- [x] **Task 7.1**: 运行 npm audit 并修复高危漏洞 ✅
  - 执行 `npm audit fix` 修复 Next.js DoS 漏洞
  - 验证：`npm audit` 0 vulnerabilities

### Task 8: 前端性能优化 ✅
- [x] **Task 8.1**: 聊天页面代码分割 ✅
  - MarkdownRenderer 已使用 `next/dynamic` 动态加载
  - ChatContent 已用 Suspense 包裹
  - Bundle 大小合理：/chat 6.97 kB + First Load 113 kB
  - 验证：`npm run build` 确认 bundle 正常

### Task 9: API 文档完善 ✅
- [x] **Task 9.1**: 集成 Swagger API 文档 ✅
  - Flasgger 已集成，Swagger UI 可访问
  - `/apidocs/` → 200 (Swagger UI)
  - `/apispec.json` → 200 (OpenAPI Spec)
  - 验证：浏览器访问 http://localhost:8008/apidocs/ 可查看交互式文档

---

## 任务依赖关系

```
阶段一（可部分并行）:
  Task 1 (基础设施) ──┬──> Task 2 (Service 测试) ──> Task 4 (集成测试)
                      ├──> Task 3 (API 测试)     ──┘
                      └─────────────────────────────>

阶段二（可在阶段一部分完成后开始）:
  Task 5 (Pydantic 迁移) - 独立，可与阶段一并行
  Task 6 (前端测试框架) - 独立，可与后端测试并行

阶段三（最低优先级）:
  Task 7, 8, 9 - 完全独立，可在任意时间执行
```

## 并行执行建议

**第一批次（立即开始）：**
- Task 1.1 + Task 1.2（基础设施修复）→ 必须先完成
- Task 5.1（Pydantic 迁移）→ 可并行

**第二批次（基础设施就绪后）：**
- Task 2.1 ~ 2.7（Service 测试）→ 互相独立，可完全并行
- Task 3.1 ~ 3.11（API 测试）→ 互相独立，可完全并行

**第三批次（核心测试完成）：**
- Task 4.1（集成测试）→ 依赖 Task 2 & 3
- Task 6.1 ~ 6.2（前端测试）→ 可与后端并行

**第四批次（收尾）：**
- Task 7, 8, 9（低优先级优化）

---

## 验证标准

每个 Task 完成时应满足：
1. ✅ 对应测试文件存在且语法正确
2. ✅ `pytest tests/<file>.py -v` 全部通过
3. ✅ `--cov=<module>` 显示覆盖率达标
4. ✅ 无新的 DeprecationWarning 或 Error
5. ✅ 在虚拟环境中运行一致

最终验收：
```bash
# 后端完整测试套件
cd /home/xxh/openclaw-harness/backend
source venv/bin/activate
pytest tests/ -v --cov=app --cov-report=term-missing
# 预期：150+ passed, coverage >= 75%

# 前端测试套件
cd /home/xxh/openclaw-harness/frontend
npm run test
# 预期：20+ passed, 核心组件覆盖

# 构建验证
npm run build
# 预期：✓ Compiled successfully
```
