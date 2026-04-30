# 遗留问题专项修复 - 任务清单

## 阶段一：Next.js 安全升级 ✅

### Task 1: Next.js 版本升级（14.2.x → 15.x LTS）✅
- [x] **Task 1.1**: 备份当前版本和依赖锁定 ✅
- [x] **Task 1.2**: 升级核心依赖 ✅ (使用 npmmirror 镜像)
- [x] **Task 1.3**: 处理 Breaking Changes ✅ (无需修改，兼容)
- [x] **Task 1.4**: 构建和测试验证 ✅ (13页面 + 48测试)
- [x] **Task 1.5**: 安全审计确认 ✅ (found 0 vulnerabilities)

---

## 阶段二：集成测试修复 ✅

### Task 2: 启用跳过的集成测试用例 ✅
- [x] **Task 2.1**: 分析 run_async 根本原因 ✅ (ThreadPoolExecutor 导致上下文丢失)
- [x] **Task 2.2**: 选择并实施修复方案 ✅ (方案B: 直接调用 Service 层)
- [x] **Task 2.3**: 重写/启用 6 个跳过的集成测试 ✅ (13/13 全部通过!)
- [x] **Task 2.4**: 集成测试回归验证 ✅ (原有测试无回归)

---

## 阶段三：覆盖率工具改进 ✅

### Task 3: 提升覆盖率数据准确性 ✅
- [x] **Task 3.1**: 评估当前 mock 策略影响范围 ✅ (确认 "No data to collect" 问题)
- [x] **Task 3.2**: 实施改进方案 ✅ (改造 sys.modules → @patch + coverage run)
- [x] **Task 3.3**: 验证覆盖率报告准确性 ✅ (session_service: 58%)
- [x] **Task 3.4**: 设置覆盖率门禁（可选）✅ (记录 coverage run 方法)
