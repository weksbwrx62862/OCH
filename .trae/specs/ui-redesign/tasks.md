# OpenClaw-Harness UI 从零重设计 - 实施计划

## [ ] Task 1：设计令牌体系与基础配置
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 重写 `globals.css`，建立完整的设计令牌 CSS 变量体系（色彩、间距、圆角、阴影、排版）
  - 更新 `tailwind.config.ts`，扩展 theme 配置引用 CSS 变量，移除未使用的 `och` 色阶，确保所有自定义值通过变量引用
  - 确保代码中零硬编码色值，全部通过 `var(--xxx)` 或 Tailwind 语义类引用
  - 安装 `lucide-react` 依赖
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-1.1：`globals.css` 中定义完整的 CSS 变量集（至少包含 background、surface、border、primary、success、warning、error、text 各层级）
  - `programmatic` TR-1.2：`tailwind.config.ts` 中 colors 引用 CSS 变量而非硬编码值
  - `programmatic` TR-1.3：`grep -r "#[0-9a-fA-F]\{3,6\}" frontend/app/ frontend/components/` 无硬编码色值匹配（URL 和合法注释除外）
  - `programmatic` TR-1.4：`lucide-react` 出现在 `package.json` dependencies 中
- **Notes**: 这是所有后续任务的基础，必须首先完成

## [ ] Task 2：基础组件库 - 原子组件
- **Priority**: P0
- **Depends On**: Task 1
- **Description**:
  - 创建 `components/ui/` 目录
  - 实现以下原子组件，每个组件独立文件：
    - `Button` — 变体：primary/secondary/ghost/danger，尺寸：sm/md/lg，支持 loading 状态和图标
    - `Input` — 变体：default/search，支持前缀图标、清除按钮、错误状态
    - `Badge` — 变体：default/success/warning/error/info，尺寸：sm/md
    - `Avatar` — 支持图片/首字母/图标，尺寸：sm/md/lg
    - `Spinner` — 尺寸：sm/md/lg
    - `Switch` — 开关切换，支持禁用状态
    - `Tooltip` — 悬停提示，支持四个方向
  - 每个组件需有完整 TypeScript 类型定义，使用 forwardRef 暴露 ref
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-2.1：`components/ui/` 目录包含 Button.tsx、Input.tsx、Badge.tsx、Avatar.tsx、Spinner.tsx、Switch.tsx、Tooltip.tsx 共 7 个文件
  - `programmatic` TR-2.2：每个组件文件无 TypeScript `any` 类型
  - `programmatic` TR-2.3：每个组件使用 CSS 变量而非硬编码色值
  - `human-judgement` TR-2.4：组件视觉风格与 Linear Dark 主题一致，hover/focus 反馈清晰
- **Notes**: 原子组件是最小粒度的 UI 元素，不依赖其他自定义组件

## [ ] Task 3：基础组件库 - 复合组件
- **Priority**: P0
- **Depends On**: Task 2
- **Description**:
  - 实现以下复合组件：
    - `Card` — 支持 header/body/footer 插槽，hover 效果，可点击变体
    - `Modal` — 遮罩层 + 居中面板，支持标题/内容/操作区，Escape 关闭，点击遮罩关闭
    - `Tabs` — 标签切换，支持受控/非受控模式
    - `Dropdown` — 下拉菜单，支持触发方式（click/hover）、菜单项分组
    - `Toast` — 通知提示，支持 success/error/warning/info 类型，自动消失，可手动关闭
    - `EmptyState` — 空状态占位，支持图标/标题/描述/操作按钮
  - Toast 需配合 Zustand store 的通知系统使用
- **Acceptance Criteria Addressed**: AC-2, AC-7
- **Test Requirements**:
  - `programmatic` TR-3.1：`components/ui/` 目录包含 Card.tsx、Modal.tsx、Tabs.tsx、Dropdown.tsx、Toast.tsx、EmptyState.tsx 共 6 个文件
  - `programmatic` TR-3.2：Modal 组件支持 Escape 键关闭和遮罩点击关闭
  - `programmatic` TR-3.3：Toast 组件通过 Zustand store 驱动，支持 addToast/removeToast
  - `programmatic` TR-3.4：所有复合组件无 TypeScript `any` 类型
  - `human-judgement` TR-3.5：Modal 和 Toast 视觉风格与全局深色主题一致，无原生弹窗
- **Notes**: 复合组件可引用原子组件

## [ ] Task 4：全局布局与导航系统
- **Priority**: P0
- **Depends On**: Task 2, Task 3
- **Description**:
  - 创建 `components/layout/` 目录
  - 实现 `Sidebar` 组件：可折叠侧边栏，包含 Logo、导航链接（Dashboard/Chat/Agents/Sessions/Tasks/Tools/Skills/Swarm/Audit/Settings），当前页面高亮，折叠时仅显示图标
  - 实现 `TopBar` 组件：页面标题/面包屑、搜索触发器、用户菜单（头像 + 下拉）
  - 实现 `AppLayout` 组件：组合 Sidebar + TopBar + 主内容区，提供 `useLayout()` hook
  - 更新 `appStore.ts`：接入 sidebarOpen 状态，添加 toggleSidebar action
  - 更新 `layout.tsx`：用 AppLayout 包裹 children，移除各页面内联导航
  - 更新 `AuthProvider`：集成到 AppLayout 中
- **Acceptance Criteria Addressed**: AC-3, AC-8
- **Test Requirements**:
  - `programmatic` TR-4.1：`components/layout/` 目录包含 Sidebar.tsx、TopBar.tsx、AppLayout.tsx
  - `programmatic` TR-4.2：所有 11 个页面路由在 Sidebar 中有对应导航链接
  - `programmatic` TR-4.3：当前页面导航链接有视觉高亮（active 状态）
  - `programmatic` TR-4.4：sidebarOpen 状态通过 Zustand appStore 管理
  - `programmatic` TR-4.5：Sidebar 支持折叠/展开切换
  - `human-judgement` TR-4.6：从任意页面可通过侧边栏导航到其他页面
- **Notes**: 这是解决导航断裂问题的核心任务

## [ ] Task 5：Zustand 全局状态管理完善
- **Priority**: P1
- **Depends On**: Task 4
- **Description**:
  - 重写 `appStore.ts`，定义完整的状态结构：
    - `user` — 用户信息
    - `sidebarOpen` — 侧边栏状态
    - `theme` — 主题（预留，当前固定 dark）
    - `toasts` — 通知列表
    - `commandPaletteOpen` — 命令面板状态
  - 实现 actions：`toggleSidebar`、`addToast`、`removeToast`、`setUser`、`toggleCommandPalette`
  - 实现 `ToastContainer` 组件：渲染 appStore 中的 toasts，支持堆叠和自动消失
  - 实现 `CommandPalette` 组件：Cmd+K 触发，搜索页面和操作
  - 确保各页面通过 appStore 管理全局状态，不再自行管理
- **Acceptance Criteria Addressed**: AC-8, AC-7
- **Test Requirements**:
  - `programmatic` TR-5.1：appStore 导出 toggleSidebar、addToast、removeToast、setUser、toggleCommandPalette actions
  - `programmatic` TR-5.2：ToastContainer 组件渲染 appStore.toasts 状态
  - `programmatic` TR-5.3：Cmd+K 快捷键可打开 CommandPalette
  - `programmatic` TR-5.4：各页面不再自行管理 sidebarOpen 等全局状态
  - `human-judgement` TR-5.5：Toast 通知视觉风格与全局主题一致
- **Notes**: CommandPalette 为基础版，仅支持页面搜索和跳转

## [ ] Task 6：登录页重设计
- **Priority**: P0
- **Depends On**: Task 2, Task 3
- **Description**:
  - 重写 `login/page.tsx`，使用新组件库（Input、Button、Card）
  - 视觉风格统一为深色紫罗兰主题，移除所有 Tailwind 默认蓝色
  - 添加品牌元素：Logo、渐变装饰
  - 保持开发环境免密登录功能
  - 添加表单验证和错误提示（使用 Toast）
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `programmatic` TR-6.1：login/page.tsx 中无 `bg-blue-`、`bg-gray-8`、`bg-gray-9` 等 Tailwind 默认色类名
  - `programmatic` TR-6.2：login/page.tsx 使用 components/ui/ 中的 Button 和 Input 组件
  - `programmatic` TR-6.3：登录页背景色使用 CSS 变量 `var(--background)`
  - `human-judgement` TR-6.4：登录页视觉风格与全局深色紫罗兰主题一致
- **Notes**: 这是最明显的视觉割裂点，需优先修复

## [ ] Task 7：Dashboard 首页重设计
- **Priority**: P1
- **Depends On**: Task 4, Task 5
- **Description**:
  - 重写 `page.tsx`（首页），使用新组件库和 AppLayout
  - 移除内联导航栏（已由 AppLayout 提供）
  - 使用 Card 组件重构统计卡片区域
  - 使用 Lucide 图标替代 Emoji
  - 使用 Badge 组件替代内联状态标签
  - 使用 EmptyState 组件处理空数据状态
  - 保持原有 API 调用逻辑不变
- **Acceptance Criteria Addressed**: AC-6, AC-11, AC-12
- **Test Requirements**:
  - `programmatic` TR-7.1：首页无内联导航栏代码
  - `programmatic` TR-7.2：首页无 Emoji 字符用于 UI 图标
  - `programmatic` TR-7.3：首页使用 Card、Badge 等组件库组件
  - `programmatic` TR-7.4：首页 API 调用逻辑与旧版等价（/sessions、/agents、/audit）
  - `human-judgement` TR-7.5：首页视觉风格统一，无割裂感
- **Notes**: 首页是用户入口，需确保数据展示完整

## [ ] Task 8：Chat 对话页重设计
- **Priority**: P0
- **Depends On**: Task 4, Task 5
- **Description**:
  - 重写 `chat/page.tsx`，使用新组件库和 AppLayout
  - 移除内联导航，改用 AppLayout 提供的侧边栏
  - 使用 Lucide 图标替代 Emoji
  - 使用 Button、Input、Badge、Card 等组件重构 UI
  - 使用 Modal 替代原生 confirm/prompt
  - 保持 SSE 流式通信逻辑不变
  - 保持 MarkdownRenderer 功能不变
  - 使用 Toast 替代 alert
  - 优化消息列表性能（正确的 memoization）
- **Acceptance Criteria Addressed**: AC-5, AC-6, AC-7, AC-11
- **Test Requirements**:
  - `programmatic` TR-8.1：Chat 页无内联导航代码
  - `programmatic` TR-8.2：Chat 页无 Emoji 字符用于 UI 图标
  - `programmatic` TR-8.3：Chat 页无 `confirm()`、`prompt()`、`alert()` 调用
  - `programmatic` TR-8.4：SSE 流式通信逻辑（streamChat）保持不变
  - `programmatic` TR-8.5：MarkdownRenderer 导入和渲染逻辑保持不变
  - `human-judgement` TR-8.6：Chat 页消息气泡、工具调用卡片视觉清晰，交互流畅
- **Notes**: Chat 页是最复杂的页面，需特别注意保持功能完整性

## [ ] Task 9：智能体管理页重设计
- **Priority**: P1
- **Depends On**: Task 4, Task 5
- **Description**:
  - 重写 `agents/page.tsx`，使用新组件库和 AppLayout
  - 使用 Card 组件重构智能体卡片
  - 使用 Modal 组件替代原生 prompt/confirm 实现创建和编辑
  - 使用 Avatar、Badge、Button 组件
  - 使用 Lucide 图标替代 Emoji
  - 保持 CRUD API 调用逻辑不变
- **Acceptance Criteria Addressed**: AC-6, AC-7, AC-11
- **Test Requirements**:
  - `programmatic` TR-9.1：无 `prompt()`、`confirm()` 调用
  - `programmatic` TR-9.2：无 Emoji 图标
  - `programmatic` TR-9.3：使用 Modal 组件实现创建/编辑对话框
  - `programmatic` TR-9.4：CRUD API 调用逻辑与旧版等价
  - `human-judgement` TR-9.5：智能体卡片视觉清晰，操作直观
- **Notes**: 需确保创建/编辑/删除流程完整可用

## [ ] Task 10：会话管理页重设计
- **Priority**: P1
- **Depends On**: Task 4, Task 5
- **Description**:
  - 重写 `sessions/page.tsx`，使用新组件库和 AppLayout
  - 使用 Card、Badge、Button 组件
  - 使用 Modal 替代原生 confirm
  - 使用 Lucide 图标替代 Emoji
  - 添加响应式网格断点
  - 保持 API 调用逻辑不变
- **Acceptance Criteria Addressed**: AC-6, AC-7, AC-9, AC-11
- **Test Requirements**:
  - `programmatic` TR-10.1：无 `confirm()` 调用
  - `programmatic` TR-10.2：无 Emoji 图标
  - `programmatic` TR-10.3：统计卡片网格有响应式断点（grid-cols-1 md:grid-cols-2 lg:grid-cols-4）
  - `programmatic` TR-10.4：API 调用逻辑与旧版等价
- **Notes**: 会话列表是核心功能，需确保跳转到 Chat 页正常

## [ ] Task 11：工具库页重设计
- **Priority**: P1
- **Depends On**: Task 4, Task 5
- **Description**:
  - 重写 `tools/page.tsx`，使用新组件库和 AppLayout
  - 使用 Card、Badge、Input（搜索）、Button 组件
  - 使用 Lucide 图标替代 Emoji
  - 保持搜索和筛选逻辑不变
- **Acceptance Criteria Addressed**: AC-6, AC-11
- **Test Requirements**:
  - `programmatic` TR-11.1：无 Emoji 图标
  - `programmatic` TR-11.2：使用组件库组件
  - `programmatic` TR-11.3：搜索和分类筛选功能正常
- **Notes**: 工具危险等级颜色标签需保持语义清晰

## [ ] Task 12：技能库页重设计
- **Priority**: P1
- **Depends On**: Task 4, Task 5
- **Description**:
  - 重写 `skills/page.tsx`，使用新组件库和 AppLayout
  - 使用 Card、Badge、Button、Modal、Switch 组件
  - 使用 Lucide 图标替代 Emoji
  - 使用 Modal 替代原生 prompt 实现安装
  - 保持 API 调用逻辑不变
- **Acceptance Criteria Addressed**: AC-6, AC-7, AC-11
- **Test Requirements**:
  - `programmatic` TR-12.1：无 `prompt()` 调用
  - `programmatic` TR-12.2：无 Emoji 图标
  - `programmatic` TR-12.3：使用 Modal 实现安装对话框
  - `programmatic` TR-12.4：启用/禁用切换功能正常
- **Notes**: Switch 组件用于启用/禁用切换

## [ ] Task 13：Swarm 多智能体页重设计
- **Priority**: P2
- **Depends On**: Task 4, Task 5
- **Description**:
  - 重写 `swarm/page.tsx`，使用新组件库和 AppLayout
  - 使用 Card、Badge、Avatar、Button 组件
  - 使用 Lucide 图标替代 Emoji
  - 使用 Modal 替代原生 confirm
  - 保持 API 调用逻辑不变
- **Acceptance Criteria Addressed**: AC-6, AC-7, AC-11
- **Test Requirements**:
  - `programmatic` TR-13.1：无 `confirm()` 调用
  - `programmatic` TR-13.2：无 Emoji 图标
  - `programmatic` TR-13.3：使用组件库组件
  - `programmatic` TR-13.4：API 调用逻辑与旧版等价
- **Notes**: Swarm 页功能相对简单，优先级较低

## [ ] Task 14：任务管理页重设计
- **Priority**: P1
- **Depends On**: Task 4, Task 5
- **Description**:
  - 重写 `tasks/page.tsx`，使用新组件库和 AppLayout
  - 使用 Card、Badge、Button 组件
  - 使用 Lucide 图标替代 Emoji
  - 添加响应式网格断点
  - 保持 API 调用逻辑不变
- **Acceptance Criteria Addressed**: AC-6, AC-9, AC-11
- **Test Requirements**:
  - `programmatic` TR-14.1：无 Emoji 图标
  - `programmatic` TR-14.2：统计栏有响应式断点
  - `programmatic` TR-14.3：任务列表和状态筛选功能正常
- **Notes**: 任务进度条需保持视觉清晰

## [ ] Task 15：审计日志页重设计
- **Priority**: P2
- **Depends On**: Task 4, Task 5
- **Description**:
  - 重写 `audit/page.tsx`，使用新组件库和 AppLayout
  - 使用 Card、Badge、Button 组件
  - 使用 Lucide 图标替代 Emoji
  - 使用 Modal 替代原生 confirm（清理操作）
  - 保持 API 调用逻辑不变
- **Acceptance Criteria Addressed**: AC-6, AC-7, AC-11
- **Test Requirements**:
  - `programmatic` TR-15.1：无 `confirm()` 调用
  - `programmatic` TR-15.2：无 Emoji 图标
  - `programmatic` TR-15.3：筛选和导出功能正常
- **Notes**: 审计日志页为辅助功能，优先级较低

## [ ] Task 16：设置页重设计
- **Priority**: P1
- **Depends On**: Task 4, Task 5
- **Description**:
  - 重写 `settings/page.tsx`，使用新组件库和 AppLayout
  - 使用 Tabs、Card、Input、Button、Switch 组件
  - 使用 Lucide 图标替代 Emoji
  - 保持各 Tab 内容和 API 调用逻辑不变
- **Acceptance Criteria Addressed**: AC-6, AC-11
- **Test Requirements**:
  - `programmatic` TR-16.1：无 Emoji 图标
  - `programmatic` TR-16.2：使用 Tabs 组件实现标签切换
  - `programmatic` TR-16.3：5 个 Tab 内容完整显示
  - `programmatic` TR-16.4：MCP 服务添加表单功能正常
- **Notes**: 设置页使用 Tabs 组件替代内联标签导航

## [ ] Task 17：响应式设计与最终验证
- **Priority**: P1
- **Depends On**: Task 6-16
- **Description**:
  - 检查所有页面的响应式布局，确保 1024px-1920px 宽度范围内正常显示
  - 修复任何溢出或截断问题
  - 运行 TypeScript 类型检查和 ESLint，修复所有错误
  - 验证所有页面功能与旧版等价
  - 清理死代码（未使用的导入、变量等）
  - 更新 graphify 知识图谱
- **Acceptance Criteria Addressed**: AC-9, AC-10, AC-11
- **Test Requirements**:
  - `programmatic` TR-17.1：`npx tsc --noEmit` 零错误
  - `programmatic` TR-17.2：`npx next lint` 零错误
  - `programmatic` TR-17.3：所有页面在 1024px 宽度下无水平溢出
  - `human-judgement` TR-17.4：所有页面视觉风格统一，无割裂感
  - `human-judgement` TR-17.5：所有 CRUD 操作流程完整可用
- **Notes**: 这是最终验证任务，确保整体质量
