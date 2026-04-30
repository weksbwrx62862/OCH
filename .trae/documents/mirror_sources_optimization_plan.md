# 远程终端镜像源优化计划

## [x] 任务 1: 分析当前系统包管理器和软件源配置
- **优先级**: P0
- **依赖**: 无
- **描述**:
  - 识别系统使用的包管理器（如 apt、npm、pip 等）
  - 检查当前软件源配置
  - 测试当前下载速度
- **成功标准**:
  - 确认系统使用的包管理器
  - 了解当前软件源配置
  - 获得当前下载速度基准
- **测试要求**:
  - `programmatic` TR-1.1: 执行 `lsb_release -a` 命令确认系统版本
  - `programmatic` TR-1.2: 执行 `cat /etc/apt/sources.list` 命令查看 apt 源配置
  - `programmatic` TR-1.3: 执行 `npm config get registry` 命令查看 npm 源配置
  - `programmatic` TR-1.4: 执行 `pip config get global.index-url` 命令查看 pip 源配置
  - `programmatic` TR-1.5: 执行 `wget -O /dev/null https://download.ubuntu.com/ubuntu/pool/main/a/apt/apt_2.4.11_amd64.deb` 命令测试当前下载速度
- **注意**:
  - 记录所有测试结果，作为优化后的对比基准

## [x] 任务 2: 优化 APT 软件源
- **优先级**: P0
- **依赖**: 任务 1
- **描述**:
  - 备份当前 APT 源配置
  - 替换为国内镜像源（如阿里云、中科大、清华等）
  - 更新 APT 缓存
- **成功标准**:
  - APT 源成功替换为国内镜像源
  - APT 缓存更新成功
  - 下载速度明显提升
- **测试要求**:
  - `programmatic` TR-2.1: 执行 `sudo apt update` 命令更新缓存，无错误
  - `programmatic` TR-2.2: 执行 `wget -O /dev/null http://mirrors.aliyun.com/ubuntu/pool/main/a/apt/apt_2.4.11_amd64.deb` 命令测试下载速度
  - `human-judgement` TR-2.3: 下载速度相比之前有明显提升
- **注意**:
  - 选择适合系统版本的镜像源
  - 确保源配置格式正确

## [x] 任务 3: 优化 npm 软件源
- **优先级**: P1
- **依赖**: 任务 1
- **描述**:
  - 设置 npm 国内镜像源（如淘宝镜像）
  - 验证 npm 源配置
- **成功标准**:
  - npm 源成功设置为国内镜像源
  - npm 安装包速度明显提升
- **测试要求**:
  - `programmatic` TR-3.1: 执行 `npm config get registry` 命令确认源已更改
  - `programmatic` TR-3.2: 执行 `npm install -g lodash` 命令测试安装速度
  - `human-judgement` TR-3.3: 安装速度相比之前有明显提升
- **注意**:
  - 可以使用 `npm config set registry` 命令设置源
  - 也可以使用 nrm 工具管理多个源

## [x] 任务 4: 优化 pip 软件源
- **优先级**: P1
- **依赖**: 任务 1
- **描述**:
  - 设置 pip 国内镜像源（如阿里云、清华等）
  - 验证 pip 源配置
- **成功标准**:
  - pip 源成功设置为国内镜像源
  - pip 安装包速度明显提升
- **测试要求**:
  - `programmatic` TR-4.1: 执行 `pip config get global.index-url` 命令确认源已更改
  - `programmatic` TR-4.2: 执行 `pip install requests` 命令测试安装速度
  - `human-judgement` TR-4.3: 安装速度相比之前有明显提升
- **注意**:
  - 可以使用 `pip config set global.index-url` 命令设置源
  - 也可以在 ~/.pip/pip.conf 文件中配置

## [x] 任务 5: 优化 Homebrew 软件源
- **优先级**: P1
- **依赖**: 任务 1
- **描述**:
  - 设置 Homebrew 国内镜像源（如中科大镜像）
  - 验证 Homebrew 源配置
- **成功标准**:
  - Homebrew 源成功设置为国内镜像源
  - Homebrew 安装包速度明显提升
- **测试要求**:
  - `programmatic` TR-5.1: 执行 `git -C "$(brew --repo)" remote -v` 命令确认源已更改
  - `programmatic` TR-5.2: 执行 `brew update` 命令测试更新速度
  - `human-judgement` TR-5.3: 更新速度相比之前有明显提升
- **注意**:
  - 需要设置 HOMEBREW_BREW_GIT_REMOTE 和 HOMEBREW_CORE_GIT_REMOTE 环境变量

## [x] 任务 6: 测试综合下载速度
- **优先级**: P0
- **依赖**: 任务 2, 任务 3, 任务 4, 任务 5
- **描述**:
  - 测试各包管理器的下载速度
  - 对比优化前后的下载速度
  - 验证所有镜像源配置正确
- **成功标准**:
  - 所有包管理器的下载速度都有明显提升
  - 没有出现配置错误
- **测试要求**:
  - `programmatic` TR-6.1: 执行 `sudo apt install -y curl` 命令测试 apt 安装速度
  - `programmatic` TR-6.2: 执行 `npm install -g express` 命令测试 npm 安装速度
  - `programmatic` TR-6.3: 执行 `pip install numpy` 命令测试 pip 安装速度
  - `programmatic` TR-6.4: 执行 `brew install wget` 命令测试 Homebrew 安装速度
  - `human-judgement` TR-6.5: 所有测试的下载速度都相比优化前有明显提升
- **注意**:
  - 记录所有测试结果
  - 对比优化前后的下载速度差异

## 实施策略

1. **分析阶段**:
   - 识别系统使用的包管理器
   - 检查当前软件源配置
   - 测试当前下载速度

2. **优化阶段**:
   - 优化 APT 软件源
   - 优化 npm 软件源
   - 优化 pip 软件源
   - 优化 Homebrew 软件源

3. **测试阶段**:
   - 测试各包管理器的下载速度
   - 对比优化前后的下载速度
   - 验证所有镜像源配置正确

## 预期成果

- APT 软件源优化完成，下载速度明显提升
- npm 软件源优化完成，下载速度明显提升
- pip 软件源优化完成，下载速度明显提升
- Homebrew 软件源优化完成，下载速度明显提升
- 远程终端的整体下载和升级速度得到显著改善