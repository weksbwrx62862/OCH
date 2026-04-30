# OpenClaw-Harness UI 从零重设计 - 验证清单

## 设计令牌体系
- [ ] globals.css 中定义了完整的 CSS 变量集（background、surface、border、primary、success、warning、error、text 各层级）
- [ ] tailwind.config.ts 中 colors 引用 CSS 变量而非硬编码值
- [ ] 前端代码中无硬编码色值（如 `#111111`、`bg-gray-900`）
- [ ] lucide-react 已安装并出现在 package.json 中

## 组件库完整性
- [ ] components/ui/ 目录包含 13 个组件文件：Button、Input、Card、Badge、Modal、Toast、Avatar、Tooltip、Tabs、Dropdown、Switch、Spinner、EmptyState
- [ ] 每个组件有完整 TypeScript 类型定义，无 any 类型
- [ ] 每个组件使用 CSS 变量而非硬编码色值
- [ ] Button 组件支持 primary/secondary/ghost/danger 变体和 loading 状态
- [ ] Modal 组件支持 Escape 关闭和遮罩点击关闭
- [ ] Toast 组件通过 Zustand store 驱动
- [ ] Card 组件支持 header/body/footer 插槽

## 全局导航
- [ ] components/layout/ 目录包含 Sidebar.tsx、TopBar.tsx、AppLayout.tsx
- [ ] Sidebar 包含所有 11 个页面导航链接
- [ ] 当前页面导航链接有视觉高亮
- [ ] Sidebar 支持折叠/展开切换
- [ ] 从任意页面可通过侧边栏导航到其他页面
- [ ] layout.tsx 使用 AppLayout 包裹 children

## Zustand 状态管理
- [ ] appStore 导出 toggleSidebar、addToast、removeToast、setUser、toggleCommandPalette actions
- [ ] ToastContainer 组件渲染 appStore.toasts 状态
- [ ] Cmd+K 快捷键可打开 CommandPalette
- [ ] 各页面不再自行管理 sidebarOpen 等全局状态

## 登录页
- [ ] 登录页无 Tailwind 默认蓝色类名（bg-blue-600 等）
- [ ] 登录页使用组件库中的 Button 和 Input 组件
- [ ] 登录页背景色使用 CSS 变量
- [ ] 登录页视觉风格与全局深色紫罗兰主题一致

## Dashboard 首页
- [ ] 首页无内联导航栏代码
- [ ] 首页无 Emoji 图标
- [ ] 首页使用 Card、Badge 等组件库组件
- [ ] 首页 API 调用逻辑与旧版等价

## Chat 对话页
- [ ] Chat 页无内联导航代码
- [ ] Chat 页无 Emoji 图标
- [ ] Chat 页无 confirm()、prompt()、alert() 调用
- [ ] SSE 流式通信逻辑保持不变
- [ ] MarkdownRenderer 导入和渲染逻辑保持不变
- [ ] 工具调用卡片正确显示
- [ ] 记忆侧栏可展开

## 智能体管理页
- [ ] 无 prompt()、confirm() 调用
- [ ] 无 Emoji 图标
- [ ] 使用 Modal 组件实现创建/编辑对话框
- [ ] CRUD 操作流程完整可用

## 会话管理页
- [ ] 无 confirm() 调用
- [ ] 无 Emoji 图标
- [ ] 统计卡片网格有响应式断点
- [ ] 跳转到 Chat 页功能正常

## 工具库页
- [ ] 无 Emoji 图标
- [ ] 搜索和分类筛选功能正常
- [ ] 危险等级颜色标签语义清晰

## 技能库页
- [ ] 无 prompt() 调用
- [ ] 无 Emoji 图标
- [ ] 使用 Modal 实现安装对话框
- [ ] 启用/禁用切换功能正常

## Swarm 多智能体页
- [ ] 无 confirm() 调用
- [ ] 无 Emoji 图标
- [ ] API 调用逻辑与旧版等价

## 任务管理页
- [ ] 无 Emoji 图标
- [ ] 统计栏有响应式断点
- [ ] 任务列表和状态筛选功能正常

## 审计日志页
- [ ] 无 confirm() 调用
- [ ] 无 Emoji 图标
- [ ] 筛选和导出功能正常

## 设置页
- [ ] 无 Emoji 图标
- [ ] 使用 Tabs 组件实现标签切换
- [ ] 5 个 Tab 内容完整显示
- [ ] MCP 服务添加表单功能正常

## 响应式设计
- [ ] 所有页面在 1024px 宽度下无水平溢出
- [ ] 统计卡片网格在小屏时自动减少列数
- [ ] 侧边栏在窄屏时自动折叠

## 代码质量
- [ ] npx tsc --noEmit 零错误
- [ ] npx next lint 零错误
- [ ] 无死代码（未使用的导入、变量）
- [ ] 所有组件使用 CSS 变量，零硬编码色值

## 视觉一致性
- [ ] 所有页面色彩风格统一（深色紫罗兰主题）
- [ ] 所有页面排版风格统一（Inter + JetBrains Mono）
- [ ] 所有页面间距风格统一
- [ ] 所有页面交互反馈风格统一（hover/focus/loading）
- [ ] 无视觉割裂感
