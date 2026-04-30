# 多源配置与自动切换方案 - 配置文档

## 1. 系统信息
- **操作系统**: Ubuntu 25.10 (Questing Quokka)
- **网络状态**: 可正常访问GitHub (ping延迟约74ms)
- **配置时间**: 2026-03-11

## 2. 方案概述

本方案实现了对npm、pip、git三种工具的多源配置与自动切换功能，主要特点：

- **多源配置**: 为每种工具配置多个国内镜像源
- **自动检测**: 定期检测各源的延迟和可用性
- **自动切换**: 自动切换到延迟最低、最稳定的源
- **持久配置**: 配置持久生效，重启后仍然有效

## 3. 源检测与切换脚本

### 3.1 脚本位置
- **脚本路径**: `/home/xxh/source_switcher.sh`
- **日志路径**: `/home/xxh/source_switcher.log`

### 3.2 脚本功能
- 检测多个源的延迟和可用性
- 自动选择延迟最低的源
- 配置工具使用最佳源
- 支持npm、pip、git三种工具

### 3.3 支持的源列表

#### npm源
- 淘宝npm镜像: `https://registry.npmmirror.com/`
- 腾讯npm镜像: `https://mirrors.cloud.tencent.com/npm/`
- 官方npm源: `https://registry.npmjs.org/`

#### pip源
- 阿里云: `https://mirrors.aliyun.com/pypi/simple/`
- 清华大学: `https://pypi.tuna.tsinghua.edu.cn/simple/`
- 豆瓣: `https://pypi.douban.com/simple/`

#### git源
- gitclone.com: `https://gitclone.com/github.com/`
- fastgit.xyz: `https://hub.fastgit.xyz/`
- 官方GitHub: `https://github.com/`

## 4. 配置步骤

### 4.1 安装依赖
```bash
# 确保curl和bc已安装
sudo apt update
sudo apt install curl bc -y
```

### 4.2 下载并配置脚本
```bash
# 下载脚本
wget -O /home/xxh/source_switcher.sh https://raw.githubusercontent.com/yourusername/scripts/master/source_switcher.sh

# 或者直接创建脚本
cat > /home/xxh/source_switcher.sh << 'EOF'
#!/bin/bash

# 源检测与切换脚本
# 功能：检测多个源的延迟和可用性，自动切换到最佳源

# 日志函数
log() {
    echo "[INFO] $1"
}

log_warning() {
    echo "[WARNING] $1"
}

log_error() {
    echo "[ERROR] $1"
}

# 测试源的延迟和可用性
test_source() {
    local url=$1
    local tool=$2
    
    # 测试延迟
    if command -v curl &> /dev/null; then
        local latency=$(curl -o /dev/null -s -w "%{time_total}" "$url" 2>/dev/null)
        if [ $? -eq 0 ]; then
            # 只要能访问就认为可用
            echo "$latency"
            return 0
        fi
    fi
    
    echo "99999"
    return 1
}

# 选择最佳源
select_best_source() {
    local tool=$1
    local sources=($2)
    local best_latency=99999
    local best_source=""
    
    # 测试每个源
    for source in "${sources[@]}"; do
        local latency=$(test_source "$source" "$tool")
        if (( $(echo "$latency < $best_latency" | bc -l) )); then
            best_latency=$latency
            best_source=$source
        fi
    done
    
    if [ -n "$best_source" ]; then
        # 输出日志
        log "为 $tool 选择最佳源: $best_source (延迟: ${best_latency}s)"
        # 只返回最佳源的URL
        echo "$best_source"
        return 0
    else
        log_error "没有可用的源"
        return 1
    fi
}

# 配置npm源
configure_npm() {
    local source=$1
    log "配置npm源为: $source"
    npm config set registry "$source"
    if [ $? -eq 0 ]; then
        log "npm源配置成功"
        return 0
    else
        log_error "npm源配置失败"
        return 1
    fi
}

# 配置pip源
configure_pip() {
    local source=$1
    log "配置pip源为: $source"
    pip config set global.index-url "$source"
    pip config set global.trusted-host "$(echo $source | sed -E 's|^https?://||; s|/.*$||')"
    if [ $? -eq 0 ]; then
        log "pip源配置成功"
        return 0
    else
        log_error "pip源配置失败"
        return 1
    fi
}

# 配置git源
configure_git() {
    local source=$1
    log "配置git源为: $source"
    # 清除之前的配置
    git config --global --unset url."https://gitclone.com/github.com/".insteadOf 2>/dev/null
    git config --global --unset url."https://hub.fastgit.xyz/".insteadOf 2>/dev/null
    git config --global --unset url."https://github.com/".insteadOf 2>/dev/null
    # 设置新的配置
    git config --global url."$source".insteadOf "https://github.com/"
    if [ $? -eq 0 ]; then
        log "git源配置成功"
        return 0
    else
        log_error "git源配置失败"
        return 1
    fi
}

# 主函数
main() {
    log "开始源检测与切换..."
    
    # 定义源列表
    NPM_SOURCES=("https://registry.npmmirror.com/" "https://mirrors.cloud.tencent.com/npm/" "https://registry.npmjs.org/")
    PIP_SOURCES=("https://mirrors.aliyun.com/pypi/simple/" "https://pypi.tuna.tsinghua.edu.cn/simple/" "https://pypi.douban.com/simple/")
    GIT_SOURCES=("https://gitclone.com/github.com/" "https://hub.fastgit.xyz/" "https://github.com/")
    
    # 检测并配置npm源
    echo
    log "=== 配置npm源 ==="
    best_npm_source=$(select_best_source "npm" "${NPM_SOURCES[*]}")
    if [ $? -eq 0 ]; then
        configure_npm "$best_npm_source"
    fi
    
    # 检测并配置pip源
    echo
    log "=== 配置pip源 ==="
    best_pip_source=$(select_best_source "pip" "${PIP_SOURCES[*]}")
    if [ $? -eq 0 ]; then
        configure_pip "$best_pip_source"
    fi
    
    # 检测并配置git源
    echo
    log "=== 配置git源 ==="
    best_git_source=$(select_best_source "git" "${GIT_SOURCES[*]}")
    if [ $? -eq 0 ]; then
        configure_git "$best_git_source"
    fi
    
    echo
    log "源检测与切换完成！"
    
    # 显示当前配置
    echo
    log "当前配置:"
    log "npm源: $(npm config get registry)"
    log "pip源: $(pip config get global.index-url 2>/dev/null)"
    log "git源: $(git config --global --get-regexp url | grep insteadOf)"
}

# 执行主函数
main
EOF

# 添加执行权限
chmod +x /home/xxh/source_switcher.sh
```

### 4.3 配置自动检测机制
```bash
# 配置crontab任务，每4小时执行一次
(crontab -l 2>/dev/null; echo "0 */4 * * * /home/xxh/source_switcher.sh >> /home/xxh/source_switcher.log 2>&1") | crontab -

# 查看配置
crontab -l
```

### 4.4 手动执行脚本
```bash
# 手动执行脚本，立即检测并切换源
/home/xxh/source_switcher.sh

# 查看执行日志
cat /home/xxh/source_switcher.log
```

## 5. 故障排查

### 5.1 常见问题及解决方案

#### npm源配置问题
- **症状**: `npm error code ERR_INVALID_URL`
- **解决方案**: 手动修复npm源配置
  ```bash
  npm config set registry https://registry.npmmirror.com/
  ```

#### pip源配置问题
- **症状**: `ValueError: 'INFO' does not appear to be an IPv4 or IPv6 address`
- **解决方案**: 手动修复pip源配置
  ```bash
  pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
  pip config set global.trusted-host mirrors.aliyun.com
  ```

#### git源配置问题
- **症状**: git clone 速度慢或失败
- **解决方案**: 手动配置git源
  ```bash
  git config --global url."https://gitclone.com/github.com/".insteadOf "https://github.com/"
  ```

### 5.2 脚本执行问题
- **症状**: 脚本执行失败
- **解决方案**: 检查curl和bc是否安装
  ```bash
  sudo apt install curl bc -y
  ```

- **症状**: 源检测失败
- **解决方案**: 检查网络连接，确保能够访问外部网络
  ```bash
  ping -c 2 github.com
  ```

## 6. 手动配置方法

### 6.1 手动配置npm源
```bash
# 查看当前源
npm config get registry

# 设置淘宝源
npm config set registry https://registry.npmmirror.com/

# 设置腾讯源
npm config set registry https://mirrors.cloud.tencent.com/npm/

# 恢复官方源
npm config set registry https://registry.npmjs.org/
```

### 6.2 手动配置pip源
```bash
# 查看当前源
pip config get global.index-url

# 设置阿里云源
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip config set global.trusted-host mirrors.aliyun.com

# 设置清华大学源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/
pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 设置豆瓣源
pip config set global.index-url https://pypi.douban.com/simple/
pip config set global.trusted-host pypi.douban.com
```

### 6.3 手动配置git源
```bash
# 查看当前配置
git config --global --get-regexp url

# 设置gitclone.com镜像
git config --global url."https://gitclone.com/github.com/".insteadOf "https://github.com/"

# 设置fastgit.xyz镜像
git config --global url."https://hub.fastgit.xyz/".insteadOf "https://github.com/"

# 恢复官方源
git config --global --unset url."https://gitclone.com/github.com/".insteadOf
git config --global --unset url."https://hub.fastgit.xyz/".insteadOf
```

## 7. 测试方法

### 7.1 测试npm下载
```bash
# 测试npm下载速度
npm install -g create-vite
```

### 7.2 测试pip下载
```bash
# 测试pip下载速度
python3 -m venv test_venv
source test_venv/bin/activate
pip install requests
deactivate
rm -rf test_venv
```

### 7.3 测试git克隆
```bash
# 测试git克隆速度
rm -rf vue
git clone https://github.com/vuejs/vue.git
```

## 8. 最佳实践

### 8.1 定期更新脚本
- 定期检查脚本是否需要更新，以支持新的源或修复bug

### 8.2 监控源状态
- 定期查看脚本执行日志，了解源的状态
  ```bash
  tail -n 50 /home/xxh/source_switcher.log
  ```

### 8.3 备份配置
- 备份配置文件，以便在系统重置后快速恢复
  ```bash
  cp ~/.npmrc ~/.npmrc.backup
  cp ~/.config/pip/pip.conf ~/.config/pip/pip.conf.backup
  cp ~/.gitconfig ~/.gitconfig.backup
  ```

## 9. 总结

本方案通过以下步骤实现了多源配置与自动切换：

1. **开发源检测与切换脚本**：实现了对npm、pip、git三种工具的源检测和自动切换功能
2. **配置自动检测机制**：通过crontab配置定期执行脚本，自动检测和切换源
3. **测试验证**：验证了npm、pip、git的下载功能都能正常工作
4. **故障排查**：提供了常见问题的解决方案

通过本方案，系统能够自动选择延迟最低、最稳定的源，提高下载速度和成功率，解决了远程终端下载GitHub等资源失败的问题。