#!/bin/bash
# ============================================================================
# 智桥 (Zhineng-bridge) 生产环境部署脚本
# ============================================================================
# 用途: 自动化部署 zhineng-bridge 到生产环境
# 使用: ./deploy.sh [options]
# 选项:
#   -s, --skip-checks   跳过预检查
#   -b, --build-only    仅构建镜像，不启动
#   -p, --pull          拉取最新基础镜像
#   -r, --rollback      回滚到上一个镜像版本
#   -h, --help          显示帮助信息
# ============================================================================

set -e  # 遇到错误立即退出
set -u  # 使用未定义的变量时退出
set -o pipefail  # 管道中任何命令失败都返回失败

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
ENV_FILE="${PROJECT_ROOT}/.env.prod"
BACKUP_DIR="${PROJECT_ROOT}/backups"
ROLLBACK_IMAGE_DIR="${PROJECT_ROOT}/.rollback"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ============================================================================
# 帮助信息
# ============================================================================

show_help() {
    cat << EOF
智桥 (Zhineng-bridge) 生产环境部署脚本

用法: $0 [options]

选项:
  -s, --skip-checks    跳过预检查
  -b, --build-only     仅构建镜像，不启动
  -p, --pull           拉取最新基础镜像
  -r, --rollback       回滚到上一个镜像版本
  -h, --help           显示此帮助信息

示例:
  $0                    # 完整部署
  $0 -b                 # 仅构建
  $0 -p                 # 拉取镜像并部署
  $0 -s                 # 跳过检查并部署
  $0 -r                 # 回滚到上一版本

EOF
}

# ============================================================================
# 参数解析
# ============================================================================

SKIP_CHECKS=false
BUILD_ONLY=false
PULL_IMAGES=false
ROLLBACK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--skip-checks)
            SKIP_CHECKS=true
            shift
            ;;
        -b|--build-only)
            BUILD_ONLY=true
            shift
            ;;
        -p|--pull)
            PULL_IMAGES=true
            shift
            ;;
        -r|--rollback)
            ROLLBACK=true
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
# 预检查函数
# ============================================================================

check_docker() {
    log_step "检查 Docker 安装"

    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        log_info "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi

    local docker_version=$(docker --version)
    log_success "Docker 已安装: $docker_version"

    if ! docker info &> /dev/null; then
        log_error "Docker 未运行或没有权限访问"
        log_info "尝试: sudo systemctl start docker"
        log_info "或: sudo usermod -aG docker \$USER"
        exit 1
    fi

    log_success "Docker 运行正常"
}

check_docker_compose() {
    log_step "检查 Docker Compose 安装"

    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        local compose_version=$(docker-compose --version)
        log_success "Docker Compose 已安装: $compose_version"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        local compose_version=$(docker compose version)
        log_success "Docker Compose (插件版) 已安装: $compose_version"
    else
        log_error "Docker Compose 未安装"
        log_info "安装指南: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

check_resources() {
    log_step "检查系统资源"

    local total_mem=$(free -g | awk '/^Mem:/{print $2}')
    local available_mem=$(free -g | awk '/^Mem:/{print $7}')
    local cpu_count=$(nproc)

    log_info "CPU 核心数: $cpu_count"
    log_info "总内存: ${total_mem}GB"
    log_info "可用内存: ${available_mem}GB"

    if [ "$total_mem" -lt 4 ]; then
        log_warning "内存不足 4GB，可能影响性能"
    else
        log_success "系统资源充足"
    fi

    local disk_usage=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 80 ]; then
        log_warning "磁盘使用率超过 80%: ${disk_usage}%"
    else
        log_success "磁盘空间充足"
    fi
}

check_env_file() {
    log_step "检查环境变量文件"

    if [ ! -f "$ENV_FILE" ]; then
        log_error ".env.prod 文件不存在"
        log_info "请从 .env.example 复制并配置: cp .env.example .env.prod"
        exit 1
    fi

    log_success "环境变量文件存在"

    # 检查必需的环境变量
    local required_vars=(
        "ZHINENG_BRIDGE_SECURITY_SECRET_KEY"
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "GRAFANA_ADMIN_PASSWORD"
    )

    local missing_vars=()
    for var in "${required_vars[@]}"; do
        local value=$(grep "^${var}=" "$ENV_FILE" | cut -d'=' -f2)
        if [ -z "$value" ] || [[ "$value" =~ CHANGE_THIS ]]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_error "以下环境变量未正确设置:"
        for var in "${missing_vars[@]}"; do
            log_error "  - $var"
        done
        log_error "请在 $ENV_FILE 中设置这些变量"
        exit 1
    fi

    log_success "所有必需的环境变量已设置"
}

check_ports() {
    log_step "检查端口占用"

    local ports=(80 443 8000 8765 5432 6379 9090 3000)
    local busy_ports=()

    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            busy_ports+=($port)
        fi
    done

    if [ ${#busy_ports[@]} -gt 0 ]; then
        log_warning "以下端口已被占用:"
        for port in "${busy_ports[@]}"; do
            log_warning "  - $port"
        done
        log_warning "部署可能会失败，请检查并停止占用这些端口的进程"
    else
        log_success "所有必需的端口均可用"
    fi
}

check_ssl_certificates() {
    log_step "检查 SSL 证书"

    local cert_dir="${PROJECT_ROOT}/nginx/ssl"
    local cert_file="${cert_dir}/cert.pem"
    local key_file="${cert_dir}/key.pem"

    local enable_wss=$(grep "^ZHINENG_BRIDGE_ENABLE_WSS=" "$ENV_FILE" | cut -d'=' -f2)

    if [ "$enable_wss" = "true" ]; then
        if [ ! -f "$cert_file" ] || [ ! -f "$key_file" ]; then
            log_error "启用了 WSS 但 SSL 证书文件不存在"
            log_info "请将证书放置在 $cert_dir/ 目录"
            log_info "证书获取指南: docs/SSL_SETUP.md"
            exit 1
        fi

        log_success "SSL 证书文件存在"

        # 检查证书有效期
        if command -v openssl &> /dev/null; then
            local cert_expiry=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2)
            log_info "证书有效期至: $cert_expiry"
        fi
    else
        log_info "WSS 未启用，SSL 证书检查跳过"
    fi
}

create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log_info "创建备份目录: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi
}

backup_existing_deployment() {
    log_step "备份现有部署"

    if $COMPOSE_CMD -f "$COMPOSE_FILE" ps -q 2>/dev/null | grep -q .; then
        log_info "现有部署正在运行，创建备份..."

        local backup_file="${BACKUP_DIR}/pre_deploy_${TIMESTAMP}.tar.gz"

        # 备份数据卷
        log_info "备份数据卷..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T postgres pg_dump -U zhineng zhineng_bridge \
            > "${BACKUP_DIR}/db_pre_deploy_${TIMESTAMP}.sql" 2>/dev/null || true

        # 备份 Redis
        log_info "备份 Redis 数据..."
        $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T redis redis-cli --raw SAVE > /dev/null 2>&1 || true
        $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T redis cat /data/dump.rdb \
            > "${BACKUP_DIR}/redis_pre_deploy_${TIMESTAMP}.rdb" 2>/dev/null || true

        # 备份当前镜像标签（用于回滚）
        save_current_image_tag

        log_success "备份完成: $backup_file"
    else
        log_info "未发现现有部署，跳过备份"
    fi
}

save_current_image_tag() {
    mkdir -p "$ROLLBACK_IMAGE_DIR"
    local current_image=$($COMPOSE_CMD -f "$COMPOSE_FILE" images -q zhineng-bridge 2>/dev/null | head -1)
    if [ -n "$current_image" ]; then
        local image_id=$(docker inspect --format='{{.Id}}' "$current_image" 2>/dev/null || echo "")
        if [ -n "$image_id" ]; then
            echo "$image_id" > "${ROLLBACK_IMAGE_DIR}/previous_image_id"
            log_info "已保存当前镜像 ID 用于回滚"
        fi
    fi
    # 保存 docker-compose 文件快照
    cp "$COMPOSE_FILE" "${ROLLBACK_IMAGE_DIR}/previous_compose.yml" 2>/dev/null || true
}

rollback_deployment() {
    log_step "回滚部署"

    local prev_image_file="${ROLLBACK_IMAGE_DIR}/previous_image_id"
    local prev_compose="${ROLLBACK_IMAGE_DIR}/previous_compose.yml"

    if [ -f "$prev_compose" ]; then
        log_info "发现上一个版本的 compose 配置，正在回滚..."
        $COMPOSE_CMD -f "$prev_compose" down 2>/dev/null || true
        $COMPOSE_CMD -f "$prev_compose" up -d
        log_success "已使用上一个 compose 配置启动服务"
        wait_for_services
        show_deployment_info
        return 0
    fi

    if [ -f "$prev_image_file" ]; then
        local prev_image_id=$(cat "$prev_image_file")
        log_info "发现上一个镜像: ${prev_image_id:0:12}，正在回滚..."
        docker tag "$prev_image_id" zhineng-bridge:previous 2>/dev/null || true
        $COMPOSE_CMD -f "$COMPOSE_FILE" down 2>/dev/null || true
        # 临时修改 image 引用并启动
        local temp_compose="${ROLLBACK_IMAGE_DIR}/rollback_compose.yml"
        sed "s|zhineng-bridge:.*|zhineng-bridge:previous|g" "$COMPOSE_FILE" > "$temp_compose" 2>/dev/null || true
        $COMPOSE_CMD -f "$temp_compose" up -d
        log_success "已回滚到上一个镜像版本"
        wait_for_services
        show_deployment_info
        return 0
    fi

    log_error "未找到可回滚的版本"
    log_info "回滚方法:"
    log_info "  1. 修改 docker-compose.prod.yml 中的 image 标签"
    log_info "  2. docker-compose -f docker-compose.prod.yml up -d"
    exit 1
}

# ============================================================================
# 部署函数
# ============================================================================

pull_images() {
    log_step "拉取最新基础镜像"

    if [ "$PULL_IMAGES" = true ]; then
        log_info "拉取 PostgreSQL 镜像..."
        docker pull postgres:15-alpine || log_warning "拉取 PostgreSQL 镜像失败"

        log_info "拉取 Redis 镜像..."
        docker pull redis:7-alpine || log_warning "拉取 Redis 镜像失败"

        log_info "拉取 Prometheus 镜像..."
        docker pull prom/prometheus:latest || log_warning "拉取 Prometheus 镜像失败"

        log_info "拉取 Grafana 镜像..."
        docker pull grafana/grafana:latest || log_warning "拉取 Grafana 镜像失败"

        log_info "拉取 Nginx 镜像..."
        docker pull nginx:alpine || log_warning "拉取 Nginx 镜像失败"

        log_success "基础镜像拉取完成"
    else
        log_info "跳过镜像拉取 (-p 选项未指定)"
    fi
}

build_image() {
    log_step "构建应用镜像"

    cd "$PROJECT_ROOT"

    log_info "构建 zhineng-bridge 镜像..."
    if $COMPOSE_CMD -f "$COMPOSE_FILE" build --no-cache zhineng-bridge; then
        log_success "镜像构建成功"
    else
        log_error "镜像构建失败"
        exit 1
    fi
}

start_services() {
    log_step "启动服务"

    cd "$PROJECT_ROOT"

    log_info "停止现有服务（如果存在）..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" down 2>/dev/null || true

    log_info "启动服务..."
    if $COMPOSE_CMD -f "$COMPOSE_FILE" up -d; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败"
        exit 1
    fi
}

wait_for_services() {
    log_step "等待服务就绪"

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
        exit 1
    fi

    log_info "等待 Redis 就绪..."
    attempt=0
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
        exit 1
    fi

    log_info "等待主应用就绪..."
    sleep 10

    if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T zhineng-bridge python3 -c "
import urllib.request
urllib.request.urlopen('http://localhost:8000/health')
" &>/dev/null; then
        log_success "主应用已就绪"
    else
        log_warning "主应用健康检查失败，但继续部署"
    fi
}

show_deployment_info() {
    log_step "部署信息"

    echo "服务状态:"
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps

    echo -e "\n访问地址:"
    echo "  - WebSocket: ws://localhost:8765"
    echo "  - HTTP API: http://localhost:8000"
    echo "  - Health Check: http://localhost:8000/health"
    echo "  - Metrics: http://localhost:8000/metrics"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - Grafana: http://localhost:3000"
    echo "  - Nginx: http://localhost"

    echo -e "\n日志命令:"
    echo "  - 查看所有日志: docker-compose -f docker-compose.prod.yml logs -f"
    echo "  - 查看应用日志: docker-compose -f docker-compose.prod.yml logs -f zhineng-bridge"
    echo "  - 查看数据库日志: docker-compose -f docker-compose.prod.yml logs -f postgres"

    echo -e "\n管理命令:"
    echo "  - 停止服务: docker-compose -f docker-compose.prod.yml down"
    echo "  - 重启服务: docker-compose -f docker-compose.prod.yml restart"
    echo "  - 更新服务: ./scripts/update.sh"
    echo "  - 备份数据: ./scripts/backup.sh"
    echo "  - 验证部署: ./scripts/verify_deployment.sh"

    echo -e "\n注意: 首次启动后，请修改 Grafana 管理员密码"
}

# ============================================================================
# 主流程
# ============================================================================

main() {
    log_step "智桥 (Zhineng-bridge) 生产环境部署"
    log_info "部署时间: $(date)"
    log_info "项目目录: $PROJECT_ROOT"

    # 回滚模式
    if [ "$ROLLBACK" = true ]; then
        rollback_deployment
        return $?
    fi

    # 预检查
    if [ "$SKIP_CHECKS" = false ]; then
        check_docker
        check_docker_compose
        check_resources
        check_env_file
        check_ports
        check_ssl_certificates
    else
        log_warning "跳过预检查"
    fi

    # 备份
    create_backup_dir
    backup_existing_deployment

    # 部署
    pull_images
    build_image

    if [ "$BUILD_ONLY" = false ]; then
        start_services
        wait_for_services
        show_deployment_info

        log_step "部署完成"
        log_success "智桥 (Zhineng-bridge) 已成功部署到生产环境"

        echo -e "\n${GREEN}⚠️  重要提醒:${NC}"
        echo "1. 请修改 .env.prod 中的默认密码"
        echo "2. 首次登录 Grafana 后，请修改管理员密码"
        echo "3. 配置 SSL 证书以启用 HTTPS (参考 docs/SSL_SETUP.md)"
        echo "4. 设置监控告警 (Prometheus + Grafana)"
        echo "5. 定期备份数据 (使用 ./scripts/backup.sh)"
    else
        log_step "构建完成"
        log_success "镜像构建完成，使用以下命令启动:"
        echo "  docker-compose -f docker-compose.prod.yml up -d"
    fi
}

# 运行主流程
main
