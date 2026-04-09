#!/bin/bash
# ============================================================================
# 智桥 (Zhineng-bridge) 数据备份脚本
# ============================================================================
# 用途: 备份数据库、Redis 数据和配置文件
# 使用: ./backup.sh [options]
# 选项:
#   -d, --dir DIR         备份目录 (默认: ../backups)
#   -t, --type TYPE        备份类型: full, db, redis, config (默认: full)
#   -k, --keep NUM         保留的备份数量 (默认: 7)
#   -c, --compress         压缩备份 (默认: true)
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
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 默认配置
BACKUP_DIR="${PROJECT_ROOT}/backups"
BACKUP_TYPE="full"
KEEP_BACKUPS=7
COMPRESS=true
COMPOSE_CMD=""

# ============================================================================
# 帮助信息
# ============================================================================

show_help() {
    cat << EOF
智桥 (Zhineng-bridge) 数据备份脚本

用法: $0 [options]

选项:
  -d, --dir DIR         备份目录 (默认: ../backups)
  -t, --type TYPE       备份类型: full, db, redis, config (默认: full)
  -k, --keep NUM        保留的备份数量 (默认: 7)
  -c, --compress        压缩备份 (默认: true)
  -h, --help            显示此帮助信息

备份类型说明:
  full    - 完整备份 (数据库 + Redis + 配置)
  db      - 仅备份数据库
  redis   - 仅备份 Redis
  config  - 仅备份配置文件

示例:
  $0                    # 完整备份到默认目录
  $0 -t db              # 仅备份数据库
  $0 -d /tmp/backups    # 备份到指定目录
  $0 -k 30              # 保留30个备份

EOF
}

# ============================================================================
# 参数解析
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -t|--type)
            BACKUP_TYPE="$2"
            shift 2
            ;;
        -k|--keep)
            KEEP_BACKUPS="$2"
            shift 2
            ;;
        -c|--compress)
            COMPRESS=true
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
        log_error "服务未运行，请先启动服务"
        exit 1
    fi
}

create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        log_info "创建备份目录: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi

    # 创建子目录
    mkdir -p "${BACKUP_DIR}/db"
    mkdir -p "${BACKUP_DIR}/redis"
    mkdir -p "${BACKUP_DIR}/config"
}

# ============================================================================
# 备份函数
# ============================================================================

backup_database() {
    log_step "备份数据库"

    local backup_file="${BACKUP_DIR}/db/zhineng_bridge_${TIMESTAMP}.sql"

    log_info "备份数据库到: $backup_file"

    if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T postgres pg_dump -U zhineng zhineng_bridge > "$backup_file"; then
        log_success "数据库备份成功"

        local file_size=$(du -h "$backup_file" | cut -f1)
        log_info "备份文件大小: $file_size"

        if [ "$COMPRESS" = true ]; then
            log_info "压缩备份文件..."
            if gzip -f "$backup_file"; then
                backup_file="${backup_file}.gz"
                file_size=$(du -h "$backup_file" | cut -f1)
                log_success "压缩完成: $backup_file ($file_size)"
            fi
        fi
    else
        log_error "数据库备份失败"
        return 1
    fi
}

backup_redis() {
    log_step "备份 Redis"

    local backup_file="${BACKUP_DIR}/redis/redis_${TIMESTAMP}.rdb"

    log_info "保存 Redis 数据..."

    # 触发 Redis 保存
    $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T redis redis-cli --raw SAVE > /dev/null 2>&1 || {
        log_warning "Redis SAVE 命令失败，尝试直接复制文件"
    }

    # 从容器复制数据文件
    if $COMPOSE_CMD -f "$COMPOSE_FILE" cp zhineng-bridge-redis-prod:/data/dump.rdb "$backup_file"; then
        log_success "Redis 备份成功"

        local file_size=$(du -h "$backup_file" | cut -f1)
        log_info "备份文件大小: $file_size"

        if [ "$COMPRESS" = true ]; then
            log_info "压缩备份文件..."
            if gzip -f "$backup_file"; then
                backup_file="${backup_file}.gz"
                file_size=$(du -h "$backup_file" | cut -f1)
                log_success "压缩完成: $backup_file ($file_size)"
            fi
        fi
    else
        log_error "Redis 备份失败"
        return 1
    fi
}

backup_config() {
    log_step "备份配置文件"

    local backup_file="${BACKUP_DIR}/config/config_${TIMESTAMP}.tar"

    log_info "备份配置文件..."

    if tar -cf "$backup_file" \
        -C "$PROJECT_ROOT" \
        .env.prod \
        nginx/nginx.conf \
        docker-compose.prod.yml 2>/dev/null; then

        log_success "配置备份成功"

        local file_size=$(du -h "$backup_file" | cut -f1)
        log_info "备份文件大小: $file_size"

        if [ "$COMPRESS" = true ]; then
            log_info "压缩备份文件..."
            if gzip -f "$backup_file"; then
                backup_file="${backup_file}.gz"
                file_size=$(du -h "$backup_file" | cut -f1)
                log_success "压缩完成: $backup_file ($file_size)"
            fi
        fi
    else
        log_error "配置备份失败"
        return 1
    fi
}

backup_full() {
    log_step "完整备份"

    local backup_file="${BACKUP_DIR}/full_backup_${TIMESTAMP}.tar.gz"

    log_info "开始完整备份..."

    # 备份数据库
    backup_database || return 1

    # 备份 Redis
    backup_redis || return 1

    # 备份配置
    backup_config || return 1

    # 创建完整备份文件
    log_info "创建完整备份归档..."

    if tar -czf "$backup_file" \
        -C "$BACKUP_DIR" \
        db/ \
        redis/ \
        config/; then

        log_success "完整备份成功: $backup_file"

        local file_size=$(du -h "$backup_file" | cut -f1)
        log_info "完整备份大小: $file_size"

        # 显示备份摘要
        echo -e "\n${GREEN}备份摘要:${NC}"
        echo "  - 备份文件: $backup_file"
        echo "  - 文件大小: $file_size"
        echo "  - 备份时间: $(date)"
        echo "  - 备份类型: 完整备份"
    else
        log_error "完整备份归档失败"
        return 1
    fi
}

cleanup_old_backups() {
    log_step "清理旧备份"

    local backup_patterns=()

    case "$BACKUP_TYPE" in
        full)
            backup_patterns=("${BACKUP_DIR}/full_backup_*.tar.gz")
            ;;
        db)
            backup_patterns=("${BACKUP_DIR}/db/zhineng_bridge_*.sql" "${BACKUP_DIR}/db/zhineng_bridge_*.sql.gz")
            ;;
        redis)
            backup_patterns=("${BACKUP_DIR}/redis/redis_*.rdb" "${BACKUP_DIR}/redis/redis_*.rdb.gz")
            ;;
        config)
            backup_patterns=("${BACKUP_DIR}/config/config_*.tar" "${BACKUP_DIR}/config/config_*.tar.gz")
            ;;
    esac

    for pattern in "${backup_patterns[@]}"; do
        local count=$(ls -1 $pattern 2>/dev/null | wc -l)

        if [ $count -gt $KEEP_BACKUPS ]; then
            log_info "发现 $count 个备份，保留最新的 $KEEP_BACKUPS 个"

            local to_delete=$((count - KEEP_BACKUPS))
            log_info "删除 $to_delete 个旧备份..."

            ls -t1 $pattern 2>/dev/null | tail -n $to_delete | while read file; do
                log_info "删除: $file"
                rm -f "$file"
            done

            log_success "旧备份清理完成"
        else
            log_info "备份数量 ($count) 未超过保留限制 ($KEEP_BACKUPS)"
        fi
    done
}

# ============================================================================
# 主流程
# ============================================================================

main() {
    log_step "智桥 (Zhineng-bridge) 数据备份"
    log_info "备份时间: $(date)"
    log_info "备份类型: $BACKUP_TYPE"
    log_info "备份目录: $BACKUP_DIR"

    # 检查
    check_docker_compose
    check_running_services
    create_backup_dir

    # 执行备份
    case "$BACKUP_TYPE" in
        full)
            backup_full
            ;;
        db)
            backup_database
            ;;
        redis)
            backup_redis
            ;;
        config)
            backup_config
            ;;
        *)
            log_error "未知的备份类型: $BACKUP_TYPE"
            exit 1
            ;;
    esac

    # 清理旧备份
    cleanup_old_backups

    # 完成
    log_step "备份完成"
    log_success "备份操作成功完成"

    # 提示
    echo -e "\n${GREEN}备份位置:${NC}"
    echo "  - 数据库: ${BACKUP_DIR}/db/"
    echo "  - Redis: ${BACKUP_DIR}/redis/"
    echo "  - 配置: ${BACKUP_DIR}/config/"
    echo "  - 完整: ${BACKUP_DIR}/full_backup_${TIMESTAMP}.tar.gz"

    echo -e "\n${YELLOW}提示:${NC}"
    echo "  - 使用 ./scripts/restore.sh 恢复备份"
    echo "  - 定期备份建议: 添加到 crontab"
    echo "    示例: 0 2 * * * /path/to/scripts/backup.sh -t full -k 7"
}

# 运行主流程
main
