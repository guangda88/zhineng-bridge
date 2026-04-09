#!/bin/bash
# 智桥测试启动脚本
# 自动启动服务器、运行测试、停止服务器

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

    if ss -tuln | grep -q ":${port} "; then
        log_warning "$name port $port is already in use"
        log_info "Attempting to free port..."
        local pid=$(lsof -ti :$port 2>/dev/null || true)
        if [ -n "$pid" ]; then
            kill $pid 2>/dev/null || true
            sleep 1
            if ss -tuln | grep -q ":${port} "; then
                log_error "Failed to free port $port"
                return 1
            fi
            log_success "Port $port freed"
        fi
    fi
    return 0
}

# 停止所有服务器
stop_all_servers() {
    log_info "Stopping all servers..."

    # 从 PID 文件停止
    if [ -f .ws_server.pid ]; then
        WS_PID=$(cat .ws_server.pid)
        if ps -p $WS_PID > /dev/null 2>&1; then
            kill $WS_PID
            log_success "WebSocket server stopped (PID: $WS_PID)"
        fi
        rm -f .ws_server.pid
    fi

    if [ -f .http_server.pid ]; then
        HTTP_PID=$(cat .http_server.pid)
        if ps -p $HTTP_PID > /dev/null 2>&1; then
            kill $HTTP_PID
            log_success "HTTP server stopped (PID: $HTTP_PID)"
        fi
        rm -f .http_server.pid
    fi

    # 查找并停止所有相关进程
    pkill -f "start_server.py" 2>/dev/null || true
    pkill -f "health_check.py" 2>/dev/null || true
    pkill -f "start_manager.py" 2>/dev/null || true

    log_info "All servers stopped"
}

# 启动服务器
start_servers() {
    log_info "Starting zhineng-bridge servers..."

    # 检查并释放端口
    check_port 8765 "WebSocket" || return 1
    check_port 8000 "HTTP" || return 1

    # 启动 WebSocket 服务器
    log_info "Starting WebSocket relay server on port 8765..."
    cd relay-server
    python3 start_server.py > /tmp/ws_server.log 2>&1 &
    WS_PID=$!
    cd ..
    echo $WS_PID > .ws_server.pid

    # 等待 WebSocket 服务器启动
    sleep 3

    # 检查 WebSocket 服务器是否成功启动
    if ! ps -p $WS_PID > /dev/null 2>&1; then
        log_error "WebSocket server failed to start"
        cat /tmp/ws_server.log
        return 1
    fi
    log_success "WebSocket server started (PID: $WS_PID)"

    # 启动 HTTP 健康检查服务器
    log_info "Starting HTTP health check server on port 8000..."
    cd relay-server
    python3 health_check.py > /tmp/http_server.log 2>&1 &
    HTTP_PID=$!
    cd ..
    echo $HTTP_PID > .http_server.pid

    # 等待 HTTP 服务器启动
    sleep 2

    # 检查 HTTP 服务器是否成功启动
    if ! ps -p $HTTP_PID > /dev/null 2>&1; then
        log_error "HTTP server failed to start"
        cat /tmp/http_server.log
        stop_all_servers
        return 1
    fi
    log_success "HTTP server started (PID: $HTTP_PID)"

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
    echo "=========================================="
    echo ""
}

# 运行测试
run_tests() {
    log_info "Running test suite..."

    # 等待服务器完全启动
    sleep 2

    # 运行 pytest
    python3 -m pytest tests/ -v --tb=short "$@"

    TEST_RESULT=$?

    echo ""
    if [ $TEST_RESULT -eq 0 ]; then
        log_success "All tests passed!"
    else
        log_error "Some tests failed"
    fi

    return $TEST_RESULT
}

# 清理函数
cleanup() {
    echo ""
    log_info "Cleaning up..."
    stop_all_servers
}

# 捕获中断信号
trap cleanup INT TERM EXIT

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  智桥 (Zhineng-Bridge) 测试脚本"
    echo "=========================================="
    echo ""

    # 停止任何现有的服务器
    stop_all_servers
    sleep 1

    # 启动服务器
    start_servers
    if [ $? -ne 0 ]; then
        exit 1
    fi

    # 运行测试
    run_tests "$@"
    TEST_RESULT=$?

    # 停止服务器
    stop_all_servers

    exit $TEST_RESULT
}

# 运行主函数
main "$@"
