#!/bin/bash
# 智桥 (Zhineng-Bridge) 快速开始脚本
# 自动安装依赖并启动服务器

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

# 检查命令是否存在
command_exists() {
    command -v "$1" &> /dev/null
}

# 检查系统要求
check_requirements() {
    log_info "Checking system requirements..."

    # 检查 Python 3.8+
    if ! command_exists python3; then
        log_error "Python 3 is not installed"
        log_info "Please install Python 3.8 or higher"
        log_info "Visit: https://www.python.org/downloads/"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    log_success "Python $PYTHON_VERSION found"

    # 检查 Node.js 16+
    if ! command_exists node; then
        log_error "Node.js is not installed"
        log_info "Please install Node.js 16 or higher"
        log_info "Visit: https://nodejs.org/"
        exit 1
    fi

    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 16 ]; then
        log_error "Node.js version is too old: v$(node --version)"
        log_info "Please install Node.js 16 or higher"
        log_info "Visit: https://nodejs.org/"
        exit 1
    fi
    log_success "Node.js $(node --version) found"

    # 检查 npm
    if ! command_exists npm; then
        log_error "npm is not installed"
        log_info "npm should be included with Node.js"
        exit 1
    fi
    log_success "npm $(npm --version) found"

    # 检查 pip
    if ! command_exists pip3; then
        log_error "pip3 is not installed"
        log_info "Please install pip3"
        log_info "On Ubuntu/Debian: sudo apt-get install python3-pip"
        exit 1
    fi
    log_success "pip3 found"

    log_success "All requirements met!"
    echo ""
}

# 安装 Python 依赖
install_python_deps() {
    log_info "Installing Python dependencies..."

    # 尝试使用 --break-system-packages（针对 Debian 系统）
    if pip3 install --break-system-packages -r requirements.txt 2>/dev/null; then
        log_success "Python dependencies installed"
    else
        # 如果失败，尝试普通安装
        if pip3 install -r requirements.txt 2>/dev/null; then
            log_success "Python dependencies installed"
        else
            log_warning "Failed to install Python dependencies"
            log_info "Attempting individual package installation..."

            # 尝试单独安装核心依赖
            pip3 install websockets asyncio pydantic-settings cachetools 2>/dev/null || \
            pip3 install --break-system-packages websockets asyncio pydantic-settings cachetools || \
            log_warning "Some Python dependencies may not be installed"
        fi
    fi
    echo ""
}

# 安装 JavaScript 依赖
install_js_deps() {
    log_info "Installing JavaScript dependencies..."

    if [ -f package.json ]; then
        npm install --silent
        if [ $? -eq 0 ]; then
            log_success "JavaScript dependencies installed"
        else
            log_error "Failed to install JavaScript dependencies"
            exit 1
        fi
    else
        log_warning "package.json not found, skipping JavaScript dependencies"
    fi
    echo ""
}

# 运行测试（可选）
run_tests() {
    log_info "Running tests..."

    if python3 -m pytest tests/unit/ -v 2>/dev/null; then
        log_success "Unit tests passed"
    else
        log_warning "Unit tests failed or not found"
    fi
    echo ""
}

# 启动服务器
start_servers() {
    log_info "Starting zhineng-bridge servers..."

    # 检查端口是否被占用
    if lsof -i :8765 > /dev/null 2>&1; then
        log_warning "Port 8765 is already in use"
        log_info "Attempting to free port..."
        local pid=$(lsof -ti :8765)
        if [ -n "$pid" ]; then
            kill $pid 2>/dev/null || true
            sleep 1
            log_success "Port 8765 freed"
        fi
    fi

    if lsof -i :8000 > /dev/null 2>&1; then
        log_warning "Port 8000 is already in use"
        log_info "Attempting to free port..."
        local pid=$(lsof -ti :8000)
        if [ -n "$pid" ]; then
            kill $pid 2>/dev/null || true
            sleep 1
            log_success "Port 8000 freed"
        fi
    fi

    # 启动 WebSocket 服务器
    log_info "Starting WebSocket relay server on port 8765..."
    python3 relay-server/start_server.py &
    WS_PID=$!
    sleep 3

    if ! ps -p $WS_PID > /dev/null; then
        log_error "WebSocket server failed to start"
        log_error "Please check the logs for details"
        exit 1
    fi
    log_success "WebSocket server started (PID: $WS_PID)"

    # 启动 HTTP 服务器
    log_info "Starting HTTP health check server on port 8000..."
    python3 relay-server/health_check.py &
    HTTP_PID=$!
    sleep 2

    if ! ps -p $HTTP_PID > /dev/null; then
        log_error "HTTP server failed to start"
        kill $WS_PID 2>/dev/null || true
        exit 1
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
    echo "  - Docs: http://localhost:8000/docs"
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
            kill $WS_PID 2>/dev/null || true
            log_success "WebSocket server stopped (PID: $WS_PID)"
        fi
        rm .ws_server.pid
    fi

    if [ -f .http_server.pid ]; then
        HTTP_PID=$(cat .http_server.pid)
        if ps -p $HTTP_PID > /dev/null 2>&1; then
            kill $HTTP_PID 2>/dev/null || true
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
    echo "  智桥 (Zhineng-Bridge) 快速开始"
    echo "=========================================="
    echo ""

    # 检查系统要求
    check_requirements

    # 安装依赖
    install_python_deps
    install_js_deps

    # 可选：运行测试
    if [ "$1" = "--test" ] || [ "$1" = "-t" ]; then
        run_tests
    fi

    # 启动服务器
    start_servers
}

# 显示帮助信息
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --test    Run tests before starting servers"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Example:"
    echo "  $0              # Start servers directly"
    echo "  $0 --test       # Run tests and start servers"
}

# 解析命令行参数
case "$1" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
