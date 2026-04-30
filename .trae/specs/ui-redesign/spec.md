# OpenClaw-Harness UI 从零重设计 - 产品需求文档

## 概述
- **摘要**：对 OpenClaw-Harness 前端进行从零开始的全面 UI 重设计，建立统一的设计系统和可复用组件库，修复导航断裂、视觉不一致、组件化缺失等核心问题，打造专业级 AI Agent 管理平台的用户体验。
- **目的**：当前前端虽然功能完整，但存在架构粗糙、组件化不足、导航体验断裂、视觉风格不一致等严重问题。重设计旨在从根本上解决这些问题，建立可持续演进的前端架构。
- **目标用户**：AI Agent 运维人员、开发者、技术团队管理者

## 目标
- 建立统一的设计系统（Design System），包含色彩、排版、间距、交互规范
- 构建可复用的组件库，消除代码重复，提升开发效率
- 实现全局导航系统，确保页面间流畅跳转
- 统一视觉风格，消除登录页等页面的视觉割裂
- 完善响应式设计，支持桌面和平板设备
- 接入 Zustand 全局状态管理，实现主题切换、通知等跨页面功能
- 用 SVG 图标替代 Emoji，确保跨平台视觉一致性

## 非目标（超出范围）
- 不修改后端 API 接口
- 不增加新的业务功能页面
- 不实现亮色主题（仅保留深色主题，但架构预留切换能力）
- 不做移动端适配（仅桌面 + 平板）
- 不引入重型 UI 框架（如 Ant Design、Material UI），保持轻量手写风格
- 不重构 SSE 流式通信逻辑

## 背景与上下文
- 当前前端基于 Next.js 15 + React 19 + Tailwind CSS + Zustand 构建
- 所有 UI 组件内联在各 page.tsx 中，无独立组件库
- 导航栏仅在首页实现，Chat 页等子页面缺少全局导航
- 登录页使用 Tailwind 默认蓝色主题，与全局紫罗兰深色主题完全脱节
- CSS 变量体系已建立但执行不一致，硬编码色值与变量混用
- Zustand Store 已定义但未被任何页面使用（死代码）
- 大量使用 Emoji 作为图标，跨平台渲染不一致
- 原生 `confirm()`/`prompt()` 对话框与暗色主题不协调

## 功能需求

- **FR-1**：建立设计令牌（Design Tokens）体系，统一色彩、排版、间距、圆角、阴影等基础变量，全部通过 CSS 变量和 Tailwind 配置实现
- **FR-2**：构建基础组件库，至少包含：Button、Input、Card、Badge、Modal、Toast、Avatar、Tooltip、Tabs、Dropdown、Switch、Spinner、EmptyState
- **FR-3**：实现全局侧边栏导航 + 顶部栏布局，所有页面共享同一导航框架
- **FR-4**：重设计登录页，视觉风格与全局深色紫罗兰主题统一
- **FR-5**：重设计 Dashboard 首页，使用新组件库重构统计卡片、活动列表、快捷操作
- **FR-6**：重设计 Chat 对话页，使用新组件库重构消息气泡、工具调用卡片、记忆侧栏、输入区
- **FR-7**：重设计智能体管理页，使用新组件库重构卡片网格、创建/编辑模态框
- **FR-8**：重设计会话管理页，使用新组件库重构列表视图、状态筛选
- **FR-9**：重设计工具库页，使用新组件库重构搜索筛选、工具卡片
- **FR-10**：重设计技能库页，使用新组件库重构筛选、卡片、安装模态框
- **FR-11**：重设计 Swarm 多智能体页，使用新组件库重构团队列表、子智能体网格
- **FR-12**：重设计任务管理页，使用新组件库重构状态统计、任务列表
- **FR-13**：重设计审计日志页，使用新组件库重构筛选、日志列表
- **FR-14**：重设计设置页，使用新组件库重构标签导航、配置表单
- **FR-15**：接入 Zustand 全局状态管理，实现侧边栏折叠/展开、通知系统、命令面板
- **FR-16**：用 SVG 图标库（Lucide React）替代所有 Emoji 图标
- **FR-17**：实现 Toast 通知组件，替代原生 `alert()`/`confirm()`/`prompt()`
- **FR-18**：完善响应式设计，所有页面支持 1024px-1920px 宽度范围

## 非功能需求

- **NFR-1**：首屏加载时间 ≤ 2 秒（Turbopack 开发模式）
- **NFR-2**：组件库 TypeScript 类型完整率 100%，无 any 类型
- **NFR-3**：所有交互元素支持键盘导航（Tab/Enter/Escape）
- **NFR-4**：WCAG 2.1 AA 级色彩对比度（文字与背景至少 4.5:1）
- **NFR-5**：CSS 变量使用率 100%，零硬编码色值
- **NFR-6**：组件库单元测试覆盖率 ≥ 80%

## 约束
- **技术**：必须使用 Next.js 15 App Router + React 19 + Tailwind CSS 3.4 + Zustand 4.4，不引入新框架
- **技术**：图标库选用 Lucide React（轻量、树摇优化、与 React 生态兼容）
- **技术**：不使用 shadcn/ui 等 UI 框架，保持手写组件以维持设计独特性
- **业务**：所有现有页面路由保持不变
- **业务**：API 调用逻辑（apiClient、useApi hook）保持不变
- **依赖**：需新增 lucide-react 依赖

## 假设
- 用户主要在桌面浏览器（Chrome/Firefox/Edge）中使用
- 深色主题是唯一需要的主题，但架构应预留亮色主题切换能力
- 后端 API 在重设计期间保持稳定
- 现有的 SSE 流式通信机制无需修改

## 验收标准

### AC-1：设计令牌体系
- **Given**：项目使用 Tailwind CSS 和 CSS 变量
- **When**：查看 globals.css 和 tailwind.config.ts
- **Then**：所有色彩、间距、圆角、阴影值均通过 CSS 变量定义，代码中无硬编码色值（如 `#111111`、`bg-gray-900`）
- **验证**：`programmatic`
- **备注**：可通过 grep 检查硬编码色值

### AC-2：组件库完整性
- **Given**：项目需要可复用的 UI 组件
- **When**：查看 `components/` 目录
- **Then**：包含 Button、Input、Card、Badge、Modal、Toast、Avatar、Tooltip、Tabs、Dropdown、Switch、Spinner、EmptyState 共 13 个组件，每个组件有独立文件和 TypeScript 类型定义
- **验证**：`programmatic`

### AC-3：全局导航
- **Given**：用户在任意页面
- **When**：查看页面布局
- **Then**：左侧显示可折叠侧边栏，包含所有页面导航链接和当前页面高亮；顶部显示面包屑或页面标题
- **验证**：`human-judgment`

### AC-4：登录页视觉统一
- **Given**：用户访问 /login 页面
- **When**：页面加载完成
- **Then**：登录页使用与全局一致的深色紫罗兰主题，无 Tailwind 默认蓝色（bg-blue-600 等），背景色与全局一致
- **验证**：`programmatic`

### AC-5：Chat 页功能完整
- **Given**：用户在 Chat 页进行对话
- **When**：发送消息并接收 AI 回复
- **Then**：SSE 流式响应正常工作，工具调用卡片正确显示，Markdown 渲染正确，记忆侧栏可展开
- **验证**：`programmatic`

### AC-6：Emoji 图标替换
- **Given**：页面中原本使用 Emoji 作为图标
- **When**：检查所有页面源码
- **Then**：所有 Emoji 图标已替换为 Lucide React SVG 图标组件，代码中无 Emoji 字符用于 UI 图标
- **验证**：`programmatic`

### AC-7：原生弹窗替换
- **Given**：页面中原本使用 `confirm()`/`prompt()`/`alert()`
- **When**：执行创建/删除等操作
- **Then**：使用自定义 Modal/Toast 组件替代，视觉风格与全局主题一致
- **验证**：`human-judgment`

### AC-8：Zustand 状态管理接入
- **Given**：appStore 已定义但未使用
- **When**：查看各页面代码
- **Then**：侧边栏折叠状态通过 appStore 管理，通知系统通过 appStore 管理，无页面自行管理这些全局状态
- **验证**：`programmatic`

### AC-9：响应式设计
- **Given**：浏览器窗口宽度在 1024px-1920px 之间变化
- **When**：调整窗口大小
- **Then**：所有页面布局自适应，无内容溢出或截断，统计卡片网格在小屏时自动减少列数
- **验证**：`human-judgment`

### AC-10：代码质量
- **Given**：重设计完成后的代码库
- **When**：运行 TypeScript 类型检查和 ESLint
- **Then**：零类型错误，零 ESLint 错误
- **验证**：`programmatic`

### AC-11：页面功能等价
- **Given**：重设计后的各页面
- **When**：执行与旧版相同的操作
- **Then**：所有业务功能（CRUD、筛选、排序、跳转）正常工作，行为与旧版等价
- **验证**：`programmatic`

### AC-12：视觉一致性
- **Given**：所有页面使用新设计系统
- **When**：浏览不同页面
- **Then**：色彩、排版、间距、交互反馈风格统一，无视觉割裂感
- **验证**：`human-judgment`

## 待解决问题
- [ ] 侧边栏默认展开还是折叠？建议默认展开，窄屏时自动折叠
- [ ] 命令面板（Command Palette）是否在本次实现？建议实现基础版
- [ ] 是否需要页面过渡动画？建议最小化动画，仅保留 hover/focus 反馈
