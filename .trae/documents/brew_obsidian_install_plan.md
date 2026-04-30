# Homebrew 和 Obsidian CLI 安装计划

## [x] 任务 1: 清理之前的 Homebrew 安装
- **优先级**: P1
- **依赖**: 无
- **描述**:
  - 清理之前可能失败的 Homebrew 安装
  - 移除任何残留的 Homebrew 目录
- **成功标准**:
  - 系统中没有 Homebrew 相关的残留文件
- **测试要求**:
  - `programmatic` TR-1.1: 执行 `which brew` 命令返回 "brew: not found"
  - `programmatic` TR-1.2: 确认 `~/.linuxbrew` 和 `/home/linuxbrew` 目录不存在或为空
- **注意**:
  - 确保清理干净，避免影响新的安装

## [x] 任务 2: 使用国内镜像源安装 Homebrew
- **优先级**: P0
- **依赖**: 任务 1
- **描述**:
  - 使用国内镜像源加速 Homebrew 安装
  - 配置 Homebrew 环境变量
- **成功标准**:
  - Homebrew 成功安装
  - `brew --version` 命令能够正常执行
- **测试要求**:
  - `programmatic` TR-2.1: 执行 `brew --version` 命令返回 Homebrew 版本信息
  - `programmatic` TR-2.2: 执行 `brew doctor` 命令检查 Homebrew 安装状态
- **注意**:
  - 使用中科大镜像源加速下载
  - 确保正确设置 PATH 环境变量

## [x] 任务 3: 安装 obsidian-cli
- **优先级**: P0
- **依赖**: 任务 2
- **描述**:
  - 使用 Homebrew 安装 obsidian-cli
  - 验证 obsidian-cli 安装成功
- **成功标准**:
  - obsidian-cli 成功安装
  - `obsidian-cli --version` 命令能够正常执行
- **测试要求**:
  - `programmatic` TR-3.1: 执行 `obsidian-cli --version` 命令返回版本信息
  - `programmatic` TR-3.2: 执行 `obsidian-cli help` 命令显示帮助信息
- **注意**:
  - 使用 `yakitrak/yakitrak/obsidian-cli` 公式

## [x] 任务 4: 设置默认 Vault 为 "KN"
- **优先级**: P0
- **依赖**: 任务 3
- **描述**:
  - 使用 obsidian-cli 设置默认 Vault 为 "KN"
  - 验证默认 Vault 设置成功
- **成功标准**:
  - 默认 Vault 成功设置为 "KN"
  - obsidian-cli 能够正确识别默认 Vault
- **测试要求**:
  - `programmatic` TR-4.1: 执行 `obsidian-cli get-default` 命令返回 "KN"
  - `programmatic` TR-4.2: 执行 `obsidian-cli open` 命令能够打开默认 Vault
- **注意**:
  - 确保 "KN" Vault 已经存在
  - 如果 Vault 不存在，需要先创建

## [x] 任务 5: 验证 Obsidian 启动
- **优先级**: P1
- **依赖**: 任务 4
- **描述**:
  - 启动 Obsidian 应用
  - 验证 Obsidian 能够自动打开默认 Vault "KN"
- **成功标准**:
  - Obsidian 成功启动
  - Obsidian 自动打开 "KN" Vault
- **测试要求**:
  - `human-judgement` TR-5.1: Obsidian 应用能够正常启动
  - `human-judgement` TR-5.2: Obsidian 自动打开 "KN" Vault，无需手动选择
- **注意**:
  - 可能需要处理沙盒相关的问题
  - 如果遇到崩溃，尝试使用 `--no-sandbox` 参数

## 实施策略

1. **清理阶段**:
   - 移除之前的 Homebrew 安装
   - 清理相关环境变量

2. **安装阶段**:
   - 使用中科大镜像源安装 Homebrew
   - 配置环境变量
   - 安装 obsidian-cli

3. **配置阶段**:
   - 设置默认 Vault
   - 验证配置

4. **验证阶段**:
   - 启动 Obsidian
   - 确认默认 Vault 设置生效

## 预期成果

- Homebrew 成功安装并配置
- obsidian-cli 成功安装
- 默认 Vault 成功设置为 "KN"
- Obsidian 能够正常启动并自动打开 "KN" Vault