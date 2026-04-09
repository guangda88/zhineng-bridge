#!/bin/bash
# 智桥服务器启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查端口是否被占用
check_port() {
    local port=$1
    local name=$2

    if lsof -i :$port > /dev/null 2>&1; then
        log_warning "$name port $port is already in use"
        log_info "Attempting to free the port..."
        local pid=$(lsof -ti :$port)
        if [ -n "$pid" ]; then
            kill $pid 2>/dev/null || true
            sleep 1
            if lsof -i :$port > /dev/null 2>&1; then
                log_error "Failed to free port $port"
                return 1
            fi
            log_success "Port $port freed"
        fi
    fi
    return 0
}

# 启动服务器
start_servers() {
    log_info "Starting zhineng-bridge servers..."

    # 检查并释放端口
    check_port 8765 "WebSocket" || return 1
    check_port 8000 "HTTP" || return 1

    # 启动 WebSocket 服务器
    log_info "Starting WebSocket relay server on port 8765..."
    python3 relay-server/start_server.py &
    WS_PID=$!

    # 等待 WebSocket 服务器启动
    sleep 3

    # 检查 WebSocket 服务器是否成功启动
    if ! ps -p $WS_PID > /dev/null; then
        log_error "WebSocket server failed to start"
        return 1
    fi
    log_success "WebSocket server started (PID: $WS_PID)"

    # 启动 HTTP 健康检查服务器
    log_info "Starting HTTP health check server on port 8000..."
    python3 relay-server/health_check.py &
    HTTP_PID=$!

    # 等待 HTTP 服务器启动
    sleep 2

    # 检查 HTTP 服务器是否成功启动
    if ! ps -p $HTTP_PID > /dev/null; then
        log_error "HTTP server failed to start"
        kill $WS_PID 2>/dev/null || true
        return 1
    fi
    log_success "HTTP server started (PID: $HTTP_PID)"

    # 保存 PID
    echo $WS_PID > .ws_server.pid
    echo $HTTP_PID > .http_server.pid

    # 显示启动信息
    echo ""
    echo "=========================================="
    log_success "Servers started successfully!"
    echo "=========================================="
    echo ""
    echo "WebSocket Server:"
    echo "  - URL: ws://localhost:8765"
    echo "  - PID: $WS_PID"
    echo ""
    echo "HTTP Server:"
    echo "  - URL: http://localhost:8000"
    echo "  - PID: $HTTP_PID"
    echo ""
    echo "Access Points:"
    echo "  - Web UI: http://localhost:8000/web/ui/index.html"
    echo "  - Health: http://localhost:8000/health"
    echo "  - Status: http://localhost:8000/status"
    echo ""
    echo "=========================================="
    echo ""
    log_info "Press Ctrl+C to stop all servers"
    echo ""

    # 等待用户中断
    wait
}

# 停止服务器
stop_servers() {
    log_info "Stopping servers..."

    if [ -f .ws_server.pid ]; then
        WS_PID=$(cat .ws_server.pid)
        if ps -p $WS_PID > /dev/null 2>&1; then
            kill $WS_PID
            log_success "WebSocket server stopped (PID: $WS_PID)"
        fi
        rm .ws_server.pid
    fi

    if [ -f .http_server.pid ]; then
        HTTP_PID=$(cat .http_server.pid)
        if ps -p $HTTP_PID > /dev/null 2>&1; then
            kill $HTTP_PID
            log_success "HTTP server stopped (PID: $HTTP_PID)"
        fi
        rm .http_server.pid
    fi

    log_info "All servers stopped"
    exit 0
}

# 捕获 Ctrl+C
trap stop_servers INT TERM

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  智桥 (Zhineng-Bridge) 启动脚本"
    echo "=========================================="
    echo ""

    start_servers
}

# 运行主函数
main
