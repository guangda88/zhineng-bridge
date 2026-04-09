#!/bin/bash
# ============================================================================
# 智桥 (Zhineng-bridge) 数据恢复脚本
# ============================================================================
# 用途: 从备份恢复数据库、Redis 数据和配置文件
# 使用: ./restore.sh [options] <backup_file>
# 选项:
#   -t, --type TYPE       恢复类型: full, db, redis, config (默认: auto)
#   -f, --force           强制恢复，不提示确认
#   -h, --help            显示帮助信息
# 参数:
#   <backup_file>         备份文件路径
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

# 默认配置
RESTORE_TYPE="auto"
FORCE_RESTORE=false
COMPOSE_CMD=""
BACKUP_FILE=""

# ============================================================================
# 帮助信息
# ============================================================================

show_help() {
    cat << EOF
智桥 (Zhineng-bridge) 数据恢复脚本

用法: $0 [options] <backup_file>

选项:
  -t, --type TYPE       恢复类型: full, db, redis, config (默认: auto)
  -f, --force           强制恢复，不提示确认
  -h, --help            显示此帮助信息

参数:
  <backup_file>         备份文件路径

恢复类型说明:
  auto    - 自动检测 (根据备份文件)
  full    - 完整恢复 (数据库 + Redis + 配置)
  db      - 仅恢复数据库
  redis   - 仅恢复 Redis
  config  - 仅恢复配置文件

示例:
  $0 ../backups/full_backup_20260301_120000.tar.gz    # 自动检测
  $0 -t db ../backups/db/zhineng_bridge_20260301.sql.gz  # 恢复数据库
  $0 -f ../backups/redis/redis_20260301.rdb.gz       # 强制恢复 Redis

警告: 恢复操作会覆盖现有数据，请谨慎操作！

EOF
}

# ============================================================================
# 参数解析
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            RESTORE_TYPE="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_RESTORE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
        *)
            BACKUP_FILE="$1"
            shift
            ;;
    esac
done

if [ -z "$BACKUP_FILE" ]; then
    log_error "必须指定备份文件"
    show_help
    exit 1
fi

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

check_backup_file() {
    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "备份文件不存在: $BACKUP_FILE"
        exit 1
    fi

    log_info "备份文件: $BACKUP_FILE"
    local file_size=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "文件大小: $file_size"

    # 自动检测恢复类型
    if [ "$RESTORE_TYPE" = "auto" ]; then
        local filename=$(basename "$BACKUP_FILE")

        case "$filename" in
            full_backup_*)
                RESTORE_TYPE="full"
                log_info "自动检测: 完整备份"
                ;;
            zhineng_bridge_*.sql*)
                RESTORE_TYPE="db"
                log_info "自动检测: 数据库备份"
                ;;
            redis_*.rdb*)
                RESTORE_TYPE="redis"
                log_info "自动检测: Redis 备份"
                ;;
            config_*.tar*)
                RESTORE_TYPE="config"
                log_info "自动检测: 配置备份"
                ;;
            *)
                log_error "无法自动检测备份类型，请使用 -t 参数指定"
                exit 1
                ;;
        esac
    fi
}

check_running_services() {
    if ! $COMPOSE_CMD -f "$COMPOSE_FILE" ps -q 2>/dev/null | grep -q .; then
        log_error "服务未运行，请先启动服务"
        exit 1
    fi
}

confirm_restore() {
    if [ "$FORCE_RESTORE" = true ]; then
        return 0
    fi

    echo -e "\n${RED}警告: 恢复操作会覆盖现有数据！${NC}"
    echo "  备份文件: $BACKUP_FILE"
    echo "  恢复类型: $RESTORE_TYPE"
    echo ""
    read -p "确认恢复? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "恢复操作已取消"
        exit 0
    fi
}

# ============================================================================
# 恢复函数
# ============================================================================

extract_backup() {
    local tar_file="$1"
    local extract_dir="$2"

    log_info "解压备份文件..."

    if [[ "$tar_file" == *.gz ]]; then
        if ! tar -xzf "$tar_file" -C "$extract_dir"; then
            log_error "解压失败"
            return 1
        fi
    else
        if ! tar -xf "$tar_file" -C "$extract_dir"; then
            log_error "解压失败"
            return 1
        fi
    fi

    log_success "解压完成"
}

restore_database() {
    log_step "恢复数据库"

    local sql_file=""
    local temp_dir="/tmp/zhineng_restore_$$"

    if [[ "$BACKUP_FILE" == *.tar* ]]; then
        log_info "从完整备份中提取数据库..."

        mkdir -p "$temp_dir"
        extract_backup "$BACKUP_FILE" "$temp_dir"

        # 查找 SQL 文件
        sql_file=$(find "$temp_dir" -name "zhineng_bridge_*.sql*" -type f | head -n 1)

        if [ -z "$sql_file" ]; then
            log_error "未找到数据库备份文件"
            rm -rf "$temp_dir"
            return 1
        fi

        # 如果是 gzip 文件，解压
        if [[ "$sql_file" == *.gz ]]; then
            log_info "解压 SQL 文件..."
            gzip -d "$sql_file"
            sql_file="${sql_file%.gz}"
        fi
    else
        sql_file="$BACKUP_FILE"

        # 如果是 gzip 文件，解压
        if [[ "$sql_file" == *.gz ]]; then
            log_info "解压 SQL 文件..."
            local temp_sql="${sql_file%.gz}"
            gunzip -c "$sql_file" > "$temp_sql"
            sql_file="$temp_sql"
        fi
    fi

    log_info "恢复数据库..."

    # 停止应用以避免数据冲突
    log_info "停止应用服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" stop zhineng-bridge

    # 恢复数据库
    if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T postgres psql -U zhineng zhineng_bridge < "$sql_file"; then
        log_success "数据库恢复成功"
    else
        log_error "数据库恢复失败"
        $COMPOSE_CMD -f "$COMPOSE_FILE" start zhineng-bridge
        rm -rf "$temp_dir"
        rm -f "${sql_file%.gz}" 2>/dev/null || true
        return 1
    fi

    # 清理
    rm -rf "$temp_dir"
    rm -f "${sql_file%.gz}" 2>/dev/null || true

    # 重启应用
    log_info "重启应用服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" start zhineng-bridge
}

restore_redis() {
    log_step "恢复 Redis"

    local rdb_file=""
    local temp_dir="/tmp/zhineng_restore_$$"

    if [[ "$BACKUP_FILE" == *.tar* ]]; then
        log_info "从完整备份中提取 Redis 数据..."

        mkdir -p "$temp_dir"
        extract_backup "$BACKUP_FILE" "$temp_dir"

        # 查找 RDB 文件
        rdb_file=$(find "$temp_dir" -name "redis_*.rdb*" -type f | head -n 1)

        if [ -z "$rdb_file" ]; then
            log_error "未找到 Redis 备份文件"
            rm -rf "$temp_dir"
            return 1
        fi

        # 如果是 gzip 文件，解压
        if [[ "$rdb_file" == *.gz ]]; then
            log_info "解压 RDB 文件..."
            gzip -d "$rdb_file"
            rdb_file="${rdb_file%.gz}"
        fi
    else
        rdb_file="$BACKUP_FILE"

        # 如果是 gzip 文件，解压
        if [[ "$rdb_file" == *.gz ]]; then
            log_info "解压 RDB 文件..."
            local temp_rdb="${rdb_file%.gz}"
            gunzip -c "$rdb_file" > "$temp_rdb"
            rdb_file="$temp_rdb"
        fi
    fi

    log_info "恢复 Redis 数据..."

    # 停止 Redis
    log_info "停止 Redis 服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" stop redis

    # 复制数据文件
    if $COMPOSE_CMD -f "$COMPOSE_FILE" cp "$rdb_file" zhineng-bridge-redis-prod:/data/dump.rdb; then
        log_success "Redis 数据恢复成功"
    else
        log_error "Redis 数据恢复失败"
        $COMPOSE_CMD -f "$COMPOSE_FILE" start redis
        rm -rf "$temp_dir"
        rm -f "${rdb_file%.gz}" 2>/dev/null || true
        return 1
    fi

    # 清理
    rm -rf "$temp_dir"
    rm -f "${rdb_file%.gz}" 2>/dev/null || true

    # 重启 Redis
    log_info "重启 Redis 服务..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" start redis
}

restore_config() {
    log_step "恢复配置文件"

    local tar_file=""
    local temp_dir="/tmp/zhineng_restore_$$"

    if [[ "$BACKUP_FILE" == *.tar* ]]; then
        log_info "从完整备份中提取配置..."

        mkdir -p "$temp_dir"
        extract_backup "$BACKUP_FILE" "$temp_dir"

        # 查找配置文件
        tar_file=$(find "$temp_dir" -name "config_*.tar*" -type f | head -n 1)

        if [ -z "$tar_file" ]; then
            log_error "未找到配置备份文件"
            rm -rf "$temp_dir"
            return 1
        fi

        # 如果是 gzip 文件，解压
        if [[ "$tar_file" == *.gz ]]; then
            log_info "解压配置文件..."
            gzip -d "$tar_file"
            tar_file="${tar_file%.gz}"
        fi
    else
        tar_file="$BACKUP_FILE"
    fi

    log_info "恢复配置文件..."

    # 备份当前配置
    local current_backup="${PROJECT_ROOT}/.env.prod.before_restore"
    if [ -f "${PROJECT_ROOT}/.env.prod" ]; then
        cp "${PROJECT_ROOT}/.env.prod" "$current_backup"
        log_info "当前配置已备份到: $current_backup"
    fi

    # 解压配置文件
    if tar -xf "$tar_file" -C "$PROJECT_ROOT"; then
        log_success "配置文件恢复成功"
    else
        log_error "配置文件恢复失败"
        rm -rf "$temp_dir"
        return 1
    fi

    # 清理
    rm -rf "$temp_dir"

    log_warning "配置文件已恢复，请检查并重启服务"
}

restore_full() {
    log_step "完整恢复"

    local temp_dir="/tmp/zhineng_restore_$$"

    log_info "从完整备份中恢复..."

    mkdir -p "$temp_dir"
    extract_backup "$BACKUP_FILE" "$temp_dir"

    # 恢复数据库
    local db_backup=$(find "$temp_dir" -name "zhineng_bridge_*.sql*" -type f | head -n 1)
    if [ -n "$db_backup" ]; then
        BACKUP_FILE="$db_backup" restore_database
    fi

    # 恢复 Redis
    local redis_backup=$(find "$temp_dir" -name "redis_*.rdb*" -type f | head -n 1)
    if [ -n "$redis_backup" ]; then
        BACKUP_FILE="$redis_backup" restore_redis
    fi

    # 恢复配置
    local config_backup=$(find "$temp_dir" -name "config_*.tar*" -type f | head -n 1)
    if [ -n "$config_backup" ]; then
        BACKUP_FILE="$config_backup" restore_config
    fi

    rm -rf "$temp_dir"
}

# ============================================================================
# 主流程
# ============================================================================

main() {
    log_step "智桥 (Zhineng-bridge) 数据恢复"
    log_info "恢复时间: $(date)"
    log_info "恢复类型: $RESTORE_TYPE"

    # 检查
    check_docker_compose
    check_backup_file
    check_running_services

    # 确认
    confirm_restore

    # 执行恢复
    case "$RESTORE_TYPE" in
        full)
            restore_full
            ;;
        db)
            restore_database
            ;;
        redis)
            restore_redis
            ;;
        config)
            restore_config
            ;;
        *)
            log_error "未知的恢复类型: $RESTORE_TYPE"
            exit 1
            ;;
    esac

    # 完成
    log_step "恢复完成"
    log_success "数据恢复操作成功完成"

    # 提示
    echo -e "\n${GREEN}建议操作:${NC}"
    echo "  - 验证数据: docker-compose -f docker-compose.prod.yml ps"
    echo "  - 查看日志: docker-compose -f docker-compose.prod.yml logs -f"
    echo "  - 检查应用: curl http://localhost:8000/health"
    echo "  - 如修改了配置，重启服务: docker-compose -f docker-compose.prod.yml restart"
}

# 运行主流程
main
