# GNOME xrdp修复或XFCE美化计划

## [ ] 任务1: 禁用Wayland，强制使用Xorg
- **优先级**: P0
- **依赖项**: 无
- **描述**: 
  - 修改GDM配置，禁用Wayland
  - GNOME在xrdp上需要使用Xorg而不是Wayland
- **成功标准**: Wayland被禁用，系统使用Xorg
- **测试要求**:
  - `programmatic` TR-1.1: 验证WaylandEnable=false已取消注释
  - `programmatic` TR-1.2: 重启后验证使用Xorg

## [ ] 任务2: 配置GNOME xrdp会话
- **优先级**: P0
- **依赖项**: 任务1
- **描述**: 
  - 更新.xsessionrc文件使用GNOME
  - 更新xrdp启动脚本
  - 配置正确的环境变量
- **成功标准**: 配置文件已更新
- **测试要求**:
  - `programmatic` TR-2.1: 验证.xsessionrc使用GNOME
  - `programmatic` TR-2.2: 验证startwm.sh配置正确

## [ ] 任务3: 测试GNOME远程桌面连接
- **优先级**: P0
- **依赖项**: 任务2
- **描述**: 
  - 重启Ubuntu系统
  - 测试Windows远程桌面连接GNOME
  - 检查是否还有闪退问题
- **成功标准**: 可以正常连接并使用GNOME桌面
- **测试要求**:
  - `human-judgement` TR-3.1: 用户确认可以正常使用GNOME桌面
  - `human-judgement` TR-3.2: 界面美观且功能正常

## [ ] 任务4 (备选): 如果GNOME仍有问题，美化XFCE
- **优先级**: P1
- **依赖项**: 任务3 (如果失败)
- **描述**: 
  - 安装Arc主题和Papirus图标
  - 配置XFCE外观接近GNOME
  - 调整面板和布局
- **成功标准**: XFCE界面美观现代
- **测试要求**:
  - `human-judgement` TR-4.1: 用户确认界面美观
  - `human-judgement` TR-4.2: 功能正常且响应迅速
