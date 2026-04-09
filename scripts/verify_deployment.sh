#!/bin/bash
# ============================================================================
# 智桥 (Zhineng-bridge) 部署验证脚本
# ============================================================================
# 用途: 验证生产环境部署是否成功，所有服务是否正常运行
# 使用: ./verify_deployment.sh [options]
# 选项:
#   -q, --quick            快速验证 (跳过详细检查)
#   -v, --verbose          详细输出
#   -h, --help             显示帮助信息
# ============================================================================

set -e  # 遇到错误立即退出
set -u  # 使用未定义的变量时退出

# ============================================================================
# 颜色和日志函数
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_step() {
    echo -e "\n${GREEN}========== $1 ==========${NC}\n"
}

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

# ============================================================================
# 配置变量
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.prod.yml"

# 验证结果统计
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# 默认配置
QUICK_MODE=false
VERBOSE_MODE=false
COMPOSE_CMD=""

# ============================================================================
# 帮助信息
# ============================================================================

show_help() {
    cat << EOF
智桥 (Zhineng-bridge) 部署验证脚本

用法: $0 [options]

选项:
  -q, --quick           快速验证 (跳过详细检查)
  -v, --verbose         详细输出
  -h, --help            显示此帮助信息

验证项目:
  - Docker 和 Docker Compose 安装
  - 容器状态
  - 端口监听
  - 服务健康检查
  - 数据库连接
  - Redis 连接
  - HTTP 端点
  - WebSocket 连接
  - SSL 证书 (如果启用)
  - Prometheus 指标
  - Grafana 访问

示例:
  $0                    # 完整验证
  $0 -q                 # 快速验证
  $0 -v                 # 详细验证输出

EOF
}

# ============================================================================
# 参数解析
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -q|--quick)
            QUICK_MODE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE_MODE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# ============================================================================
# 辅助函数
# ============================================================================

check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        log_error "Docker Compose 未安装"
        exit 1
    fi
}

run_test() {
    local test_name="$1"
    local test_command="$2"

    log_test "$test_name"

    if eval "$test_command" > /dev/null 2>&1; then
        log_success "$test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log_error "$test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        if [ "$VERBOSE_MODE" = true ]; then
            echo "失败命令: $test_command"
        fi
        return 1
    fi
}

skip_test() {
    local test_name="$1"
    local reason="$2"

    log_warning "跳过: $test_name ($reason)"
    TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
}

# ============================================================================
# 验证函数
# ============================================================================

verify_docker() {
    log_step "1. 验证 Docker 环境"

    run_test "Docker 已安装" "command -v docker"
    run_test "Docker 运行正常" "docker info"
    run_test "Docker Compose 已安装" "command -v docker-compose || docker compose version"
}

verify_containers() {
    log_step "2. 验证容器状态"

    local containers=(
        "zhineng-bridge-prod"
        "zhineng-bridge-postgres-prod"
        "zhineng-bridge-redis-prod"
        "zhineng-bridge-prometheus-prod"
        "zhineng-bridge-grafana-prod"
        "zhineng-bridge-nginx-prod"
    )

    for container in "${containers[@]}"; do
        run_test "容器 $container 运行中" "$COMPOSE_CMD -f $COMPOSE_FILE ps -q $container | grep -q ."
    done
}

verify_ports() {
    log_step "3. 验证端口监听"

    local ports=(80 443 8000 8765 5432 6379 9090 3000)

    for port in "${ports[@]}"; do
        run_test "端口 $port 监听中" "netstat -tlnp 2>/dev/null | grep -q ":$port " || ss -tlnp 2>/dev/null | grep -q ":$port ""
    done
}

verify_health_checks() {
    log_step "4. 验证健康检查"

    # PostgreSQL 健康检查
    run_test "PostgreSQL 健康检查" \
        "$COMPOSE_CMD -f $COMPOSE_FILE exec -T postgres pg_isready -U zhineng -d zhineng_bridge"

    # Redis 健康检查
    run_test "Redis 健康检查" \
        "$COMPOSE_CMD -f $COMPOSE_FILE exec -T redis redis-cli ping | grep -q PONG"
}

verify_database() {
    if [ "$QUICK_MODE" = true ]; then
        skip_test "数据库连接测试" "快速模式"
        return 0
    fi

    log_step "5. 验证数据库连接"

    # 测试数据库连接
    run_test "数据库可连接" \
        "$COMPOSE_CMD -f $COMPOSE_FILE exec -T postgres psql -U zhineng -d zhineng_bridge -c 'SELECT 1;'"

    # 检查表结构
    run_test "数据库表存在" \
        "$COMPOSE_CMD -f $COMPOSE_FILE exec -T postgres psql -U zhineng -d zhineng_bridge -c '\dt' | grep -q users"
}

verify_redis() {
    if [ "$QUICK_MODE" = true ]; then
        skip_test "Redis 功能测试" "快速模式"
        return 0
    fi

    log_step "6. 验证 Redis 功能"

    # 测试 SET/GET
    run_test "Redis SET/GET 操作" \
        "$COMPOSE_CMD -f $COMPOSE_FILE exec -T redis redis-cli SET test_key test_value > /dev/null 2>&1 && $COMPOSE_CMD -f $COMPOSE_FILE exec -T redis redis-cli GET test_key | grep -q test_value"
}

verify_http_endpoints() {
    log_step "7. 验证 HTTP 端点"

    # 健康检查端点
    run_test "健康检查端点 (/health)" \
        "curl -sf http://localhost:8000/health"

    # Prometheus 指标端点
    run_test "Prometheus 指标端点 (/metrics)" \
        "curl -sf http://localhost:8000/metrics"

    # API 文档端点
    run_test "API 文档端点 (/docs)" \
        "curl -sf http://localhost:8000/docs"

    if [ "$QUICK_MODE" = false ]; then
        # Prometheus UI
        run_test "Prometheus UI 可访问" \
            "curl -sf http://localhost:9090"

        # Grafana UI
        run_test "Grafana UI 可访问" \
            "curl -sf http://localhost:3000"
    fi
}

verify_websocket() {
    if [ "$QUICK_MODE" = true ]; then
        skip_test "WebSocket 连接测试" "快速模式"
        return 0
    fi

    log_step "8. 验证 WebSocket 连接"

    # 检查 WebSocket 端口
    run_test "WebSocket 端口 (8765) 可访问" \
        "timeout 5 bash -c 'cat < /dev/null > /dev/tcp/localhost/8765'"

    # 如果安装了 wscat，测试 WebSocket 连接
    if command -v wscat &> /dev/null; then
        run_test "WebSocket 连接" \
            "timeout 5 wscat -c ws://localhost:8765 --no-color | head -n 1"
    else
        skip_test "WebSocket 连接测试" "wscat 未安装"
    fi
}

verify_ssl() {
    log_step "9. 验证 SSL 配置"

    # 检查是否启用 WSS
    local enable_wss=$(grep "^ZHINENG_BRIDGE_ENABLE_WSS=" "$PROJECT_ROOT/.env.prod" | cut -d'=' -f2)

    if [ "$enable_wss" = "true" ]; then
        run_test "SSL 证书文件存在" \
            "[ -f $PROJECT_ROOT/nginx/ssl/cert.pem ] && [ -f $PROJECT_ROOT/nginx/ssl/key.pem ]"

        if [ "$QUICK_MODE" = false ]; then
            # 验证 SSL 证书
            if command -v openssl &> /dev/null; then
                run_test "SSL 证书有效" \
                    "openssl x509 -in $PROJECT_ROOT/nginx/ssl/cert.pem -checkend 86400 -noout"

                # 测试 HTTPS 连接
                run_test "HTTPS 连接成功" \
                    "curl -sfk https://localhost/health"
            else
                skip_test "SSL 证书验证" "openssl 未安装"
            fi
        fi
    else
        skip_test "SSL 验证" "WSS 未启用"
    fi
}

verify_prometheus_metrics() {
    if [ "$QUICK_MODE" = true ]; then
        skip_test "Prometheus 指标验证" "快速模式"
        return 0
    fi

    log_step "10. 验证 Prometheus 指标"

    # 检查应用是否暴露指标
    run_test "应用暴露 Prometheus 指标" \
        "curl -sf http://localhost:8000/metrics | grep -q 'zhineng_bridge'"

    # 检查 Prometheus 抓取配置
    run_test "Prometheus 抓取配置" \
        "$COMPOSE_CMD -f $COMPOSE_FILE exec -T prometheus curl -s http://localhost:9090/api/v1/targets | grep -q 'up'"
}

verify_grafana() {
    if [ "$QUICK_MODE" = true ]; then
        skip_test "Grafana 验证" "快速模式"
        return 0
    fi

    log_step "11. 验证 Grafana"

    # 检查 Grafana 数据源
    run_test "Grafana 可访问" \
        "curl -sf http://localhost:3000/api/health"

    if [ "$VERBOSE_MODE" = true ]; then
        log_info "Grafana 登录信息:"
        log_info "  URL: http://localhost:3000"
        log_info "  用户名: admin"
        log_info "  密码: 查看 .env.prod 中的 GRAFANA_ADMIN_PASSWORD"
    fi
}

verify_nginx() {
    log_step "12. 验证 Nginx"

    # 测试 Nginx 配置
    run_test "Nginx 配置有效" \
        "$COMPOSE_CMD -f $COMPOSE_FILE exec nginx nginx -t"

    # 测试 HTTP 重定向到 HTTPS
    run_test "HTTP 可访问" \
        "curl -sf http://localhost/"

    if [ "$QUICK_MODE" = false ]; then
        # 检查 Nginx 状态页面
        run_test "Nginx 状态页面" \
            "$COMPOSE_CMD -f $COMPOSE_FILE exec nginx wget -qO- http://localhost/nginx_status | grep -q 'Active connections'"
    fi
}

verify_logs() {
    if [ "$VERBOSE_MODE" = false ]; then
        return 0
    fi

    log_step "13. 检查服务日志 (详细模式)"

    log_info "检查应用日志中的错误..."
    local app_errors=$($COMPOSE_CMD -f $COMPOSE_FILE logs --tail=100 zhineng-bridge 2>/dev/null | grep -i error | wc -l)

    if [ "$app_errors" -eq 0 ]; then
        log_success "应用日志中无错误"
    else
        log_warning "应用日志中发现 $app_errors 个错误"
    fi

    log_info "检查数据库日志..."
    local db_errors=$($COMPOSE_CMD -f $COMPOSE_FILE logs --tail=100 postgres 2>/dev/null | grep -i error | wc -l)

    if [ "$db_errors" -eq 0 ]; then
        log_success "数据库日志中无错误"
    else
        log_warning "数据库日志中发现 $db_errors 个错误"
    fi
}

verify_performance() {
    if [ "$QUICK_MODE" = true ]; then
        return 0
    fi

    log_step "14. 性能基准测试"

    # 测试健康检查响应时间
    log_test "健康检查响应时间"
    local response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/health)

    if (( $(echo "$response_time < 1.0" | bc -l) )); then
        log_success "健康检查响应时间: ${response_time}s (低于 1.0s)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_warning "健康检查响应时间: ${response_time}s (高于 1.0s，可能需要优化)"
        TESTS_PASSED=$((TESTS_PASSED + 1))  # 不算失败，只是警告
    fi
}

print_summary() {
    log_step "验证摘要"

    local total_tests=$((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))

    echo "总测试数: $total_tests"
    log_success "通过: $TESTS_PASSED"
    log_error "失败: $TESTS_FAILED"
    log_warning "跳过: $TESTS_SKIPPED"

    if [ "$TESTS_FAILED" -eq 0 ]; then
        log_step "验证通过！"
        log_success "所有关键验证项目均通过"
        echo ""
        echo "访问地址:"
        echo "  - WebSocket: ws://localhost:8765"
        echo "  - HTTP API: http://localhost:8000"
        echo "  - 健康检查: http://localhost:8000/health"
        echo "  - API 文档: http://localhost:8000/docs"
        echo "  - Prometheus: http://localhost:9090"
        echo "  - Grafana: http://localhost:3000"
        echo "  - Nginx: http://localhost"
        return 0
    else
        log_step "验证失败"
        log_error "有 $TESTS_FAILED 个测试失败，请检查"
        echo ""
        echo "排查建议:"
        echo "  - 查看服务日志: docker-compose -f docker-compose.prod.yml logs -f [service]"
        echo "  - 检查服务状态: docker-compose -f docker-compose.prod.yml ps"
        echo "  - 查看详细错误: $0 -v"
        echo "  - 查看部署文档: docs/PRODUCTION_DEPLOYMENT.md"
        return 1
    fi
}

# ============================================================================
# 主流程
# ============================================================================

main() {
    log_step "智桥 (Zhineng-bridge) 部署验证"
    log_info "验证时间: $(date)"
    log_info "验证模式: $([ "$QUICK_MODE" = true ] && echo "快速" || echo "完整")"

    # 检查 Docker Compose
    check_docker_compose

    # 运行验证
    verify_docker
    verify_containers
    verify_ports
    verify_health_checks

    if [ "$QUICK_MODE" = false ]; then
        verify_database
        verify_redis
        verify_websocket
        verify_prometheus_metrics
        verify_grafana
        verify_ssl
        verify_logs
        verify_performance
    else
        verify_redis
        verify_ssl
    fi

    verify_http_endpoints
    verify_nginx

    # 打印摘要
    print_summary
}

# 运行主流程
main
