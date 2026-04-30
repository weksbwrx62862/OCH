# 远程终端换源配置文档

## 1. 系统信息
- **操作系统**: Ubuntu 25.10 (Questing Quokka)
- **网络状态**: 可正常访问GitHub (ping延迟约74ms)

## 2. npm源配置
### 配置步骤
1. 查看当前npm源:
   ```bash
   npm config get registry
   ```

2. 更换为淘宝npm镜像:
   ```bash
   npm config set registry https://registry.npmmirror.com/
   ```

3. 验证配置:
   ```bash
   npm config get registry
   # 输出: https://registry.npmmirror.com/
   ```

4. 测试安装:
   ```bash
   npm install -g npm
   ```

### 配置文件位置
- **配置文件**: `~/.npmrc`
- **当前配置**: `registry=https://registry.npmmirror.com/`

## 3. pip源配置
### 配置步骤
1. 配置阿里云pip镜像:
   ```bash
   pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
   pip config set global.trusted-host mirrors.aliyun.com
   ```

2. 验证配置:
   ```bash
   pip config get global.index-url
   # 输出: https://mirrors.aliyun.com/pypi/simple/
   ```

3. 测试安装:
   ```bash
   python3 -m venv test_venv
   source test_venv/bin/activate
   pip install requests
   deactivate
   rm -rf test_venv
   ```

### 配置文件位置
- **配置文件**: `~/.config/pip/pip.conf`
- **当前配置**:
  ```ini
  [global]
  index-url = https://mirrors.aliyun.com/pypi/simple/
  trusted-host = mirrors.aliyun.com
  ```

## 4. Git加速配置
### 配置步骤
1. 配置gitclone.com镜像加速:
   ```bash
   git config --global url."https://gitclone.com/github.com/".insteadOf "https://github.com/"
   ```

2. 验证配置:
   ```bash
   git config --global --get-regexp url
   # 输出包含: url.https://gitclone.com/github.com/.insteadOf https://github.com/
   ```

3. 测试克隆:
   ```bash
   git clone https://github.com/qingchencloud/clawpanel.git
   ```

### 配置文件位置
- **配置文件**: `~/.gitconfig`
- **相关配置**:
  ```ini
  [url "https://gitclone.com/github.com/"]
      insteadOf = https://github.com/
  ```

## 5. 配置效果
- **npm**: 从淘宝镜像下载，速度显著提升
- **pip**: 从阿里云镜像下载，速度显著提升
- **git**: 通过gitclone.com镜像访问GitHub，速度和稳定性提升

## 6. 故障排查
### 常见问题及解决方案
1. **npm源连接失败**:
   - 尝试切换其他npm镜像，如 `https://npm.taobao.org/mirrors/npm/`

2. **pip源连接失败**:
   - 尝试切换其他pip镜像，如 `https://pypi.tuna.tsinghua.edu.cn/simple/`

3. **git镜像连接失败**:
   - 尝试切换其他GitHub镜像，如 `https://hub.fastgit.xyz/`
   - 或暂时取消镜像配置: `git config --global --unset url."https://gitclone.com/github.com/".insteadOf`

## 7. 其他镜像源推荐
### npm镜像
- 淘宝npm镜像: `https://registry.npmmirror.com/`
- 腾讯npm镜像: `https://mirrors.cloud.tencent.com/npm/`

### pip镜像
- 阿里云: `https://mirrors.aliyun.com/pypi/simple/`
- 清华大学: `https://pypi.tuna.tsinghua.edu.cn/simple/`
- 豆瓣: `https://pypi.douban.com/simple/`

### GitHub镜像
- gitclone.com: `https://gitclone.com/github.com/`
- fastgit.xyz: `https://hub.fastgit.xyz/`
- gitee镜像: 通过gitee导入GitHub仓库