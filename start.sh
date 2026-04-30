#!/bin/bash
# ============================================
# OpenClaw-Harness Quick Start Script
# ============================================

set -e

echo "🚀 OpenClaw-Harness 启动脚本"
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 Python 3，请先安装${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
echo -e "${BLUE}📦 Python 版本: $PYTHON_VERSION${NC}"

# Backend Setup
echo ""
echo -e "${YELLOW}[1/5] 设置 Backend 环境...${NC}"

if [ ! -d "backend/.venv" ]; then
    echo "   创建虚拟环境..."
    python3 -m venv backend/.venv
fi

source backend/.venv/bin/activate

# 安装依赖（如果需要）
if ! python -c "import flask" &> /dev/null 2>&1; then
    echo "   安装 Python 依赖..."
    pip install --quiet -r backend/requirements.txt || {
        echo -e "${RED}❌ 依赖安装失败${NC}"
        exit 1
    }
fi

echo -e "${GREEN}   ✅ Backend 环境就绪${NC}"

# 初始化数据库
echo ""
echo -e "${YELLOW}[2/5] 初始化数据库...${NC}"

export DATABASE_URL="sqlite+aiosqlite:///./och.db"
cd backend && alembic upgrade head 2>/dev/null || echo "   (使用 SQLite 数据库)"
cd ..

echo -e "${GREEN}   ✅ 数据库初始化完成${NC}"

# Frontend Setup
echo ""
echo -e "${YELLOW}[3/5] 检查 Frontend...${NC}"

if [ ! -d "frontend/node_modules" ]; then
    echo "   安装 Node.js 依赖..."
    cd frontend && npm install && cd ..
else
    echo "   Node.js 依赖已安装"
fi

echo -e "${GREEN}   ✅ Frontend 环境就绪${NC}"

# 创建 .env 文件（如果不存在）
if [ ! -f ".env" ]; then
    echo ""
    echo -e "${YELLOW}[4/5] 创建配置文件...${NC}"
    cp .env.example .env 2>/dev/null || true
    echo -e "${GREEN}   ✅ 配置文件已创建${NC}"
fi

# 启动服务
echo ""
echo -e "${YELLOW}[5/5] 启动服务...${NC}"
echo ""

# 检查端口占用
check_port() {
    if lsof -i :$1 > /dev/null 2>&1; then
        return 1
    fi
    return 0
}

BACKEND_PORT=8008
FRONTEND_PORT=3000

if check_port $BACKEND_PORT; then
    echo -e "${YELLOW}⚠️  端口 $BACKEND_PORT 已被占用，尝试终止旧进程...${NC}"
    lsof -ti :$BACKEND_PORT | xargs kill -9 2>/dev/null || true
    sleep 1
fi

echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}  🌟 OpenClaw-Harness Development Server${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}Backend:  http://localhost:$BACKEND_PORT${NC}"
echo -e "  ${GREEN}Frontend: http://localhost:$FRONTEND_PORT${NC}"
echo -e "  ${GREEN}API Docs: http://localhost:$BACKEND_PORT/docs${NC}"
echo ""
echo -e "${BLUE}按 Ctrl+C 停止所有服务${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

# 启动 Backend (后台)
source backend/.venv/bin/activate
export PYTHONPATH="$SCRIPT_DIR/backend:$PYTHONPATH"
cd backend && python -m app.main &
BACKEND_PID=$!
cd ..

# 等待 Backend 启动
sleep 2

# 启动 Frontend (后台)
cd frontend && npm run dev -- -p $FRONTEND_PORT &
FRONTEND_PID=$!
cd ..

# 等待用户中断
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo ''; echo '👋 服务已停止'; exit 0" SIGINT SIGTERM

wait
