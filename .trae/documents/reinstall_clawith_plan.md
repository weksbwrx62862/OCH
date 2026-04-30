# Clawith 重新安装计划

## [ ] 任务 1: 停止正在运行的 Clawith 进程
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 检查并停止所有正在运行的 Clawith 相关进程（包括前端和后端服务）
  - 清理所有相关的后台进程
- **Success Criteria**:
  - 确认没有 Clawith 相关进程在运行
- **Test Requirements**:
  - `programmatic` TR-1.1: 使用 `ps` 命令确认没有 uvicorn、vite 或 Clawith 进程
  - `programmatic` TR-1.2: 使用 `lsof` 确认端口 8008 和 3008 已释放
- **Notes**: 这一步是为了避免删除文件时的权限问题和端口冲突

## [ ] 任务 2: 删除现有 Clawith 目录
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**: 
  - 删除 `/home/xxh/Clawith` 目录及其所有内容
- **Success Criteria**:
  - 确认 `/home/xxh/Clawith` 目录已被完全删除
- **Test Requirements**:
  - `programmatic` TR-2.1: 使用 `ls` 命令确认目录已不存在
- **Notes**: 确保使用 `rm -rf` 命令进行递归删除

## [ ] 任务 3: 在根目录克隆 Clawith 仓库
- **Priority**: P0
- **Depends On**: 任务 2
- **Description**: 
  - 在 `/home/xxh` 目录下克隆 `https://github.com/dataelement/Clawith.git`
- **Success Criteria**:
  - 仓库成功克隆到 `/home/xxh/Clawith`
- **Test Requirements**:
  - `programmatic` TR-3.1: 使用 `ls -la /home/xxh/Clawith` 确认仓库文件存在
  - `programmatic` TR-3.2: 使用 `git status` 确认仓库状态正常
- **Notes**: 克隆时确保使用正确的仓库 URL

## [ ] 任务 4: 运行 Clawith 安装脚本
- **Priority**: P0
- **Depends On": 任务 3
- **Description**: 
  - 进入 `/home/xxh/Clawith` 目录
  - 运行 `bash setup.sh` 进行安装
- **Success Criteria**:
  - 安装脚本执行成功完成
- **Test Requirements**:
  - `programmatic` TR-4.1: 检查安装脚本的输出，确认没有错误
  - `programmatic` TR-4.2: 确认 `.env` 文件已创建
  - `programmatic` TR-4.3: 确认依赖已安装（venv 和 npm 依赖）
- **Notes**: 如果需要开发环境，可以使用 `bash setup.sh --dev`

## [ ] 任务 5: 验证安装并启动服务
- **Priority**: P1
- **Depends On": 任务 4
- **Description**: 
  - 运行 `bash restart.sh` 启动 Clawith 服务
  - 验证服务是否正常运行
- **Success Criteria**:
  - 服务成功启动，前端和后端都可访问
- **Test Requirements**:
  - `programmatic` TR-5.1: 确认前端服务在 http://localhost:3008 可访问
  - `programmatic` TR-5.2: 确认后端服务在 http://localhost:8008 可访问
  - `human-judgement` TR-5.3: 检查服务日志确认没有错误
- **Notes**: 使用 `nohup` 或后台进程确保服务持久运行
