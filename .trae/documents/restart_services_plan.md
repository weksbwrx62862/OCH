# 重启 Clawith 前后端服务计划

## 任务目标
安全地停止当前正在运行的 Clawith 前端（Vite）和后端（Uvicorn）服务，并重新启动它们，确保服务正常可用。

## 步骤计划

### 第一步：检查并终止现有进程
1. 查找占用前端端口（`3008`）的 Node.js/Vite 进程。
2. 查找占用后端端口（`8008`）的 Python/Uvicorn 进程。
3. 使用 `kill -9 <PID>` 命令强制终止这些旧进程，释放端口资源。

### 第二步：重启后端服务
1. 进入后端目录：`cd /home/xxh/Clawith/backend`
2. 激活虚拟环境并以后台异步模式启动 Uvicorn：
   `.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8008`
3. 使用 `curl http://localhost:8008/api/health` 检查后端服务是否启动成功。

### 第三步：重启前端服务
1. 进入前端目录：`cd /home/xxh/Clawith/frontend`
2. 以后台异步模式启动 Vite 开发服务器：
   `npx vite --host 0.0.0.0 --port 3008`
3. 使用 `curl -I http://localhost:3008` 检查前端服务是否启动成功。

### 第四步：完成验证
1. 确认前后端均无报错日志。
2. 使用 `OpenPreview` 工具为用户在 IDE 中打开前端页面。

## 下一步行动
等待用户确认此计划。一旦批准，我将立即按照上述步骤执行端口清理和服务的重新启动。
