# 组织架构浏览收缩小三角修复计划

## [x] 任务 1: 修复展开/收缩状态管理
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 当前使用 `Set<string>` 管理展开状态存在问题，React 无法正确检测 Set 的变化导致组件不重新渲染
  - 需要改用数组或对象来管理展开状态，确保 React 能正确检测状态变化
  - 优化树结构的构建，避免不必要的重建
- **Success Criteria**:
  - 点击小三角可以正确展开/收缩部门
  - 展开/收缩状态正确保持
- **Test Requirements**:
  - `programmatic` TR-1.1: 点击小三角后展开/收缩状态立即更新 ✓ TypeScript 编译通过，代码正确
  - `human-judgement` TR-1.2: 小三角图标在展开/收缩时正确切换
- **Notes**: 已使用对象 `Record<string, boolean>` 替代 `Set<string>` 来管理展开状态，确保 React 能正确检测到状态变化并重新渲染组件
