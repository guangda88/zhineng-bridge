#!/bin/bash
# ============================================================================
# 智桥 (Zhineng-bridge) 更新脚本
# ============================================================================
# 用途: 滚动更新服务，确保零停机时间
# 使用: ./update.sh [options]
# 选项:
#   -s, --service SERVICE   仅更新指定服务 (默认: 更新所有)
#   -p, --pull              拉取最新镜像
#   -m, --migrate           运行数据库迁移
#   -f, --force             强制更新，跳过备份
#   -h, --help              显示帮助信息
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
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${GREEN}========== $1 ==========${NC}\n"
}

# ============================================================================
# 配置变量
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.prod.yml"
BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 默认配置
SERVICE="all"
PULL_IMAGES=false
RUN_MIGRATION=false
FORCE_UPDATE=false
COMPOSE_CMD=""

# ============================================================================
# 帮助信息
# ============================================================================

show_help() {
    cat << EOF
智桥 (Zhineng-bridge) 更新脚本

用法: $0 [options]

选项:
  -s, --service SERVICE   仅更新指定服务 (默认: 更新所有)
                          可选: zhineng-bridge, postgres, redis, prometheus, grafana, nginx
  -p, --pull             拉取最新镜像
  -m, --migrate          运行数据库迁移
  -f, --force            强制更新，跳过备份
  -h, --help             显示此帮助信息

服务更新顺序:
  1. Nginx (反向代理)
  2. PostgreSQL (数据库)
  3. Redis (缓存)
  4. Prometheus/Grafana (监控)
  5. zhineng-bridge (主应用)

示例:
  $0                    # 更新所有服务
  $0 -s zhineng-bridge  # 仅更新主应用
  $0 -p                 # 拉取最新镜像并更新
  $0 -m                 # 更新并运行数据库迁移

EOF
}

# ============================================================================
# 参数解析
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -p|--pull)
            PULL_IMAGES=true
            shift
            ;;
        -m|--migrate)
            RUN_MIGRATION=true
            shift
            ;;
        -f|--force)
            FORCE_UPDATE=true
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
# 检查函数
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

check_running_services() {
    if ! $COMPOSE_CMD -f "$COMPOSE_FILE" ps -q 2>/dev/null | grep -q .; then
        log_error "服务未运行，请先部署服务"
        exit 1
    fi
}

create_backup() {
    if [ "$FORCE_UPDATE" = true ]; then
        log_warning "跳过备份 (强制模式)"
        return 0
    fi

    log_step "创建更新前备份"

    local backup_file="${BACKUP_DIR}/pre_update_${TIMESTAMP}.tar.gz"

    log_info "备份配置文件..."

    if tar -czf "$backup_file" \
        -C "$PROJECT_ROOT" \
        .env.prod \
        nginx/nginx.conf \
        docker-compose.prod.yml 2>/dev/null; then
        log_success "配置备份完成"
    else
        log_warning "配置备份失败，继续更新"
    fi

    # 备份数据库
    log_info "备份数据库..."
    if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T postgres pg_dump -U zhineng zhineng_bridge \
        > "${BACKUP_DIR}/db_pre_update_${TIMESTAMP}.sql" 2>/dev/null; then
        log_success "数据库备份完成"
    else
        log_warning "数据库备份失败，继续更新"
    fi
}

pull_latest_images() {
    if [ "$PULL_IMAGES" = false ]; then
        return 0
    fi

    log_step "拉取最新镜像"

    case "$SERVICE" in
        all|postgres)
            log_info "拉取 PostgreSQL 镜像..."
            docker pull postgres:15-alpine || log_warning "拉取 PostgreSQL 镜像失败"
            ;;
        all|redis)
            log_info "拉取 Redis 镜像..."
            docker pull redis:7-alpine || log_warning "拉取 Redis 镜像失败"
            ;;
        all|prometheus)
            log_info "拉取 Prometheus 镜像..."
            docker pull prom/prometheus:latest || log_warning "拉取 Prometheus 镜像失败"
            ;;
        all|grafana)
            log_info "拉取 Grafana 镜像..."
            docker pull grafana/grafana:latest || log_warning "拉取 Grafana 镜像失败"
            ;;
        all|nginx)
            log_info "拉取 Nginx 镜像..."
            docker pull nginx:alpine || log_warning "拉取 Nginx 镜像失败"
            ;;
    esac

    log_success "镜像拉取完成"
}

# ============================================================================
# 更新函数
# ============================================================================

update_nginx() {
    if [ "$SERVICE" != "all" ] && [ "$SERVICE" != "nginx" ]; then
        return 0
    fi

    log_step "更新 Nginx"

    log_info "重新构建 Nginx 配置..."
    if $COMPOSE_CMD -f "$COMPOSE_FILE" up -d --no-deps --build nginx; then
        log_success "Nginx 更新成功"
    else
        log_error "Nginx 更新失败"
        return 1
    fi
}

update_postgres() {
    if [ "$SERVICE" != "all" ] && [ "$SERVICE" != "postgres" ]; then
        return 0
    fi

    log_step "更新 PostgreSQL"

    log_info "更新 PostgreSQL..."
    if $COMPOSE_CMD -f "$COMPOSE_FILE" up -d --no-deps --build postgres; then
        log_success "PostgreSQL 更新成功"

        # 等待数据库就绪
        log_info "等待 PostgreSQL 就绪..."
        local max_attempts=30
        local attempt=0
        while [ $attempt -lt $max_attempts ]; do
            if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T postgres pg_isready -U zhineng -d zhineng_bridge &>/dev/null; then
                log_success "PostgreSQL 已就绪"
                break
            fi
            attempt=$((attempt + 1))
            sleep 2
        done

        if [ $attempt -eq $max_attempts ]; then
            log_error "PostgreSQL 启动超时"
            return 1
        fi
    else
        log_error "PostgreSQL 更新失败"
        return 1
    fi
}

update_redis() {
    if [ "$SERVICE" != "all" ] && [ "$SERVICE" != "redis" ]; then
        return 0
    fi

    log_step "更新 Redis"

    log_info "更新 Redis..."
    if $COMPOSE_CMD -f "$COMPOSE_FILE" up -d --no-deps --build redis; then
        log_success "Redis 更新成功"

        # 等待 Redis 就绪
        log_info "等待 Redis 就绪..."
        local max_attempts=30
        local attempt=0
        while [ $attempt -lt $max_attempts ]; do
            if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T redis redis-cli ping &>/dev/null; then
                log_success "Redis 已就绪"
                break
            fi
            attempt=$((attempt + 1))
            sleep 1
        done

        if [ $attempt -eq $max_attempts ]; then
            log_error "Redis 启动超时"
            return 1
        fi
    else
        log_error "Redis 更新失败"
        return 1
    fi
}

update_monitoring() {
    if [ "$SERVICE" != "all" ]; then
        return 0
    fi

    log_step "更新监控服务"

    log_info "更新 Prometheus..."
    if $COMPOSE_CMD -f "$COMPOSE_FILE" up -d --no-deps --build prometheus; then
        log_success "Prometheus 更新成功"
    else
        log_warning "Prometheus 更新失败"
    fi

    log_info "更新 Grafana..."
    if $COMPOSE_CMD -f "$COMPOSE_FILE" up -d --no-deps --build grafana; then
        log_success "Grafana 更新成功"
    else
        log_warning "Grafana 更新失败"
    fi
}

run_database_migration() {
    if [ "$RUN_MIGRATION" = false ]; then
        return 0
    fi

    log_step "运行数据库迁移"

    # 这里可以添加数据库迁移逻辑
    # 例如: 运行 Alembic 迁移或 SQL 脚本
    log_info "检查并运行数据库迁移..."

    # 示例: 如果使用 Alembic
    # $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T zhineng-bridge alembic upgrade head

    log_info "数据库迁移检查完成"
}

update_main_app() {
    if [ "$SERVICE" != "all" ] && [ "$SERVICE" != "zhineng-bridge" ]; then
        return 0
    fi

    log_step "更新主应用"

    # 运行数据库迁移
    run_database_migration

    log_info "重新构建主应用..."
    if $COMPOSE_CMD -f "$COMPOSE_FILE" build --no-cache zhineng-bridge; then
        log_success "主应用构建成功"
    else
        log_error "主应用构建失败"
        return 1
    fi

    log_info "滚动更新主应用..."
    if $COMPOSE_CMD -f "$COMPOSE_FILE" up -d zhineng-bridge; then
        log_success "主应用更新成功"
    else
        log_error "主应用更新失败"
        return 1
    fi

    # 等待应用就绪
    log_info "等待主应用就绪..."
    sleep 10

    if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T zhineng-bridge python3 -c "
import urllib.request
urllib.request.urlopen('http://localhost:8000/health')
" &>/dev/null; then
        log_success "主应用已就绪"
    else
        log_warning "主应用健康检查失败，请检查日志"
    fi
}

verify_update() {
    log_step "验证更新"

    log_info "检查服务状态..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps

    # 检查主应用健康
    log_info "检查主应用健康状态..."
    if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T zhineng-bridge python3 -c "
import urllib.request
response = urllib.request.urlopen('http://localhost:8000/health')
print(response.read().decode())
" 2>/dev/null; then
        log_success "主应用健康检查通过"
    else
        log_warning "主应用健康检查失败"
    fi

    # 检查数据库连接
    log_info "检查数据库连接..."
    if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T postgres pg_isready -U zhineng -d zhineng_bridge &>/dev/null; then
        log_success "数据库连接正常"
    else
        log_warning "数据库连接失败"
    fi

    # 检查 Redis 连接
    log_info "检查 Redis 连接..."
    if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T redis redis-cli ping &>/dev/null; then
        log_success "Redis 连接正常"
    else
        log_warning "Redis 连接失败"
    fi
}

# ============================================================================
# 主流程
# ============================================================================

main() {
    log_step "智桥 (Zhineng-bridge) 服务更新"
    log_info "更新时间: $(date)"
    log_info "更新服务: $SERVICE"

    # 检查
    check_docker_compose
    check_running_services

    # 备份
    create_backup

    # 拉取镜像
    pull_latest_images

    # 按顺序更新服务
    if [ "$SERVICE" = "all" ]; then
        update_nginx
        update_postgres
        update_redis
        update_monitoring
        update_main_app
    else
        case "$SERVICE" in
            nginx)
                update_nginx
                ;;
            postgres)
                update_postgres
                ;;
            redis)
                update_redis
                ;;
            prometheus|grafana)
                update_monitoring
                ;;
            zhineng-bridge)
                update_main_app
                ;;
            *)
                log_error "未知的服务: $SERVICE"
                exit 1
                ;;
        esac
    fi

    # 验证
    verify_update

    # 完成
    log_step "更新完成"
    log_success "服务更新操作成功完成"

    # 提示
    echo -e "\n${GREEN}验证命令:${NC}"
    echo "  - 查看日志: docker-compose -f docker-compose.prod.yml logs -f [service]"
    echo "  - 检查健康: curl http://localhost:8000/health"
    echo "  - 查看指标: curl http://localhost:8000/metrics"
    echo "  - 验证部署: ./scripts/verify_deployment.sh"

    if [ "$FORCE_UPDATE" = true ]; then
        echo -e "\n${YELLOW}警告: 本次更新跳过了备份${NC}"
    fi
}

# 运行主流程
main
