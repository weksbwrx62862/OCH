# XFCE美化计划 - 打造现代美观的桌面环境

## [ ] 任务1: 切换回XFCE配置
- **优先级**: P0
- **依赖项**: 无
- **描述**: 
  - 更新.xsessionrc使用XFCE
  - 更新xrdp启动脚本
- **成功标准**: 配置文件已更新为XFCE
- **测试要求**:
  - `programmatic` TR-1.1: .xsessionrc使用xfce4-session
  - `programmatic` TR-1.2: startwm.sh配置XFCE环境

## [ ] 任务2: 安装Arc主题和Papirus图标
- **优先级**: P0
- **依赖项**: 任务1
- **描述**: 
  - 安装Arc主题（现代GNOME风格主题）
  - 安装Papirus图标（美观的图标包）
  - 安装其他美化工具
- **成功标准**: 主题和图标已安装
- **测试要求**:
  - `programmatic` TR-2.1: Arc主题已安装
  - `programmatic` TR-2.2: Papirus图标已安装

## [ ] 任务3: 配置XFCE外观设置
- **优先级**: P0
- **依赖项**: 任务2
- **描述**: 
  - 创建配置脚本设置主题
  - 设置窗口管理器主题
  - 设置图标主题
  - 调整面板布局
- **成功标准**: 外观配置已准备好
- **测试要求**:
  - `human-judgement` TR-3.1: 主题应用后界面美观
  - `human-judgement` TR-3.2: 图标统一美观

## [ ] 任务4: 重启并测试
- **优先级**: P0
- **依赖项**: 任务3
- **描述**: 
  - 重启xrdp服务
  - 用户远程连接后手动选择主题
  - 验证界面美观且功能正常
- **成功标准**: 可以正常使用美观的XFCE桌面
- **测试要求**:
  - `human-judgement` TR-4.1: 用户确认界面美观现代
  - `human-judgement` TR-4.2: 功能正常且响应迅速
