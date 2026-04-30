# 删除无用文件 Spec

## Why
项目工作区中存在大量开发过程中产生的临时文件、缓存文件、测试产物和内部计划文档，这些文件不属于源代码的一部分，需要清理以保持项目结构清晰。

## What Changes
- 删除开发过程中产生的临时/无用文件和目录
- 更新 `.gitignore` 确保未来不会误提交缓存/产物文件

## Impact
- 受影响目录: `.claw/`, `.workbuddy/`, `.codebuddy/`, `1cbc9b8f3af74051a0772a5195fd9b3f/`, `.trae/documents/`, `.trae/plans/`, `frontend/coverage/`, `graphify-out/`
- 受影响文件: `ANALYSIS_DETAIL_REPORT.md`, `ANALYSIS_DETAIL_tasks.md`, `debug_test.sh`, `frontend/tsconfig.tsbuildinfo`
- 保留的核心代码: `backend/`, `frontend/`, `docs/`, `.github/workflows/`, `.trae/skills/`, `.trae/specs/`, `.trae/mcps/`

## ADDED Requirements

### Requirement: 清理无用文件
系统 SHALL 删除所有不应保留在项目中的临时文件和目录。

#### Scenario: 删除临时会话数据
- **WHEN** 清理 `.claw/sessions/` 目录
- **THEN** 该目录及其所有会话JSONL文件被删除

#### Scenario: 删除内部工作区数据
- **WHEN** 清理 `.workbuddy/` 和 `.codebuddy/` 目录
- **THEN** 这些目录及其内容被删除

#### Scenario: 删除分析报告临时文件
- **WHEN** 清理 `1cbc9b8f3af74051a0772a5195fd9b3f/` 目录
- **THEN** 该目录及其内部报告文件被删除

#### Scenario: 删除开发计划文档
- **WHEN** 清理 `.trae/documents/` 目录
- **THEN** 该目录及其所有计划/报告文件被删除

#### Scenario: 删除内部计划文件
- **WHEN** 清理 `.trae/plans/` 目录
- **THEN** 该目录及其所有计划文件被删除

#### Scenario: 删除测试覆盖率产物
- **WHEN** 清理 `frontend/coverage/` 目录
- **THEN** 该目录及其所有覆盖率报告文件被删除

#### Scenario: 删除graphify缓存
- **WHEN** 清理 `graphify-out/` 目录
- **THEN** 该目录及其所有缓存/图谱文件被删除

#### Scenario: 删除根级临时文件
- **WHEN** 清理 `ANALYSIS_DETAIL_REPORT.md`, `ANALYSIS_DETAIL_tasks.md`, `debug_test.sh`
- **THEN** 这些文件被删除

### Requirement: 更新Git忽略规则
系统 SHALL 更新 `.gitignore` 以覆盖新增的临时目录。

#### Scenario: 添加新忽略规则
- **WHEN** 向 `.gitignore` 添加 `.claw/`, `.workbuddy/`, `.codebuddy/`, `graphify-out/`, `*.tsbuildinfo`
- **THEN** 这些规则生效，未来不会被git追踪

## MODIFIED Requirements
无

## REMOVED Requirements
无
