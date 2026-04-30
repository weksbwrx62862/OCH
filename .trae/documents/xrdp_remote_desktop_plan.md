# Ubuntu远程桌面配置 - 实施计划

## [ ] 任务1: 下载xrdp安装脚本
- **优先级**: P0
- **依赖项**: 无
- **描述**: 
  - 从c-nergy.be下载xrdp-installer脚本
  - 解压缩脚本文件
  - 赋予脚本执行权限
- **成功标准**: 脚本文件存在且可执行
- **测试要求**:
  - `programmatic` TR-1.1: 验证xrdp-installer-1.4.8.sh文件存在
  - `programmatic` TR-1.2: 验证脚本具有执行权限
- **备注**: 使用wget下载zip压缩包

## [ ] 任务2: 运行xrdp安装脚本
- **优先级**: P0
- **依赖项**: 任务1
- **描述**: 
  - 执行xrdp-installer脚本安装xrdp服务
  - 脚本会自动配置必要的依赖和设置
- **成功标准**: xrdp服务安装成功
- **测试要求**:
  - `programmatic` TR-2.1: 验证xrdp命令可执行
  - `programmatic` TR-2.2: 验证xrdp服务已安装
- **备注**: 脚本执行可能需要一些时间

## [ ] 任务3: 查看Ubuntu主机IP地址
- **优先级**: P0
- **依赖项**: 任务2
- **描述**: 
  - 获取Ubuntu主机的局域网IP地址
  - 记录IP地址供Windows远程桌面连接使用
- **成功标准**: 成功获取IP地址
- **测试要求**:
  - `programmatic` TR-3.1: 获取到有效的局域网IP地址
- **备注**: 使用ifconfig或ip addr命令

## [ ] 任务4: 验证xrdp服务状态
- **优先级**: P1
- **依赖项**: 任务2
- **描述**: 
  - 检查xrdp服务是否正常运行
  - 确认3389端口是否在监听
- **成功标准**: xrdp服务正常运行且3389端口开放
- **测试要求**:
  - `programmatic` TR-4.1: xrdp服务状态显示active (running)
  - `programmatic` TR-4.2: 3389端口处于LISTEN状态
- **备注**: 使用systemctl和netstat/ss命令

## [ ] 任务5: 重启Ubuntu主机（重要）
- **优先级**: P0
- **依赖项**: 任务4
- **描述**: 
  - 重启Ubuntu系统以确保所有配置生效
  - 重启后不要登录Ubuntu账户
- **成功标准**: 系统重启完成
- **测试要求**:
  - `human-judgement` TR-5.1: 系统成功重启并显示登录界面
- **备注**: 这是避免蓝屏问题的关键步骤
