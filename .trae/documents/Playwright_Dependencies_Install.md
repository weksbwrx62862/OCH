# 无头浏览器底层依赖安装清单

在 Linux 系统中，即使使用了免安装版（如 Camoufox）或已预装了部分核心，Playwright 和无头浏览器仍依赖一系列关键的 C/C++ 共享库（如字体处理、音频/视频解码、网络安全库等）。

如果在处理复杂网页时遇到渲染崩溃、字体方块、视频无法加载等问题，请在您的系统终端中（**而非智能体内部**）使用 `sudo` 权限执行以下命令以补齐环境：

```bash
# 1. 更新包列表
sudo apt-get update

# 2. 安装 Playwright / Chromium 所需的底层依赖
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libdbus-1-3
```

> **注意**：以上包名适用于 Ubuntu/Debian 系统。如果您使用的是 CentOS、Fedora 等其他发行版，包名可能有所不同。安装完成后，所有依赖无头浏览器的技能（如 `wechat-article-to-markdown`）将获得更好的稳定性。