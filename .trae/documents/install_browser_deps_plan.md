# 安装无头浏览器底层依赖计划

## 1. 摘要 (Summary)
自动为当前系统 (Ubuntu 25.10) 安装运行无头浏览器 (Playwright / Camoufox) 所需的全部底层 C/C++ 依赖库。

## 2. 现状分析 (Current State Analysis)
- 当前系统为 **Ubuntu 25.10 (Questing Quokka)**。
- 之前生成的 `Playwright_Dependencies_Install.md` 文档中列出了所需的包名（如 `libnss3`, `libgbm1` 等）。这些包在 Ubuntu 环境下完全兼容。
- 目标是通过 `sudo apt-get` 工具非交互式地完成所有包的安装。

## 3. 提议的变更 (Proposed Changes)
将执行以下命令来完成依赖的安装：

1. **更新包列表**：
   运行 `sudo apt-get update` 以确保能获取到最新的包版本信息。
2. **静默安装依赖库**：
   运行以下命令安装缺失的共享库：
   ```bash
   sudo apt-get install -y \
       libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
       libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
       libxdamage1 libxfixes3 libxrandr2 libgbm1 \
       libasound2 libpango-1.0-0 libcairo2 libdbus-1-3
   ```

## 4. 假设与决策 (Assumptions & Decisions)
- **假设**: 终端工具 (RunCommand) 在当前上下文中可以正常使用 `sudo` 权限执行命令（或者用户已经配置了免密 `sudo`）。如果需要密码，系统会提示或等待输入。由于 `RunCommand` 工具能够直接在用户的环境里运行，我们将直接下发安装指令。
- **决策**: 采用 `-y` 参数保证安装过程非交互式进行，防止因等待用户确认（[Y/n]）而导致命令卡死。

## 5. 验证步骤 (Verification Steps)
- 检查 `apt-get install` 命令的退出码（Exit Code）是否为 0。
- 可选：通过 `dpkg -l | grep libnss3` 等命令抽查部分关键包的安装状态，确认已成功安装。