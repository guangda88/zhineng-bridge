#!/bin/bash

GATEWAY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$GATEWAY_DIR/gateway.pid"
LOG_FILE="$GATEWAY_DIR/gateway.log"
MEFRPC_PID_FILE="$GATEWAY_DIR/mefrpc.pid"
MEFRPC_LOG_FILE="$GATEWAY_DIR/mefrpc.log"
MEFRPC_BIN="/home/ai/bin/mefrpc"
MEFRPC_TOKEN="${MEFRPC_TOKEN:-}"
MEFRPC_PROXY="${MEFRPC_PROXY:-173459}"

# Load ZHIBRIDGE_* env vars from .env
if [ -f /home/ai/zhibridge/.env ]; then
    while IFS='=' read -r key val; do
        [ -z "$key" ] && continue
        case "$key" in \#*) continue ;; esac
        export "$key=$val"
    done < <(grep -v '^#' /home/ai/zhibridge/.env | grep -v '^$')
fi

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "智桥网关已在运行 (PID: $(cat $PID_FILE))"
        else
            cd /home/ai/zhibridge
            PYTHONPATH=/home/ai/zhibridge python3 -m gateway.app >> "$LOG_FILE" 2>&1 &
            echo $! > "$PID_FILE"
            echo "智桥网关已启动 (PID: $!)"
            echo "端口: 8767"
            echo "日志: $LOG_FILE"
        fi
        if [ -f "$MEFRPC_PID_FILE" ] && kill -0 $(cat "$MEFRPC_PID_FILE") 2>/dev/null; then
            echo "MEFRP隧道已在运行 (PID: $(cat $MEFRPC_PID_FILE))"
        else
            $MEFRPC_BIN -t $MEFRPC_TOKEN -p $MEFRPC_PROXY -n --skip-cert-verify >> "$MEFRPC_LOG_FILE" 2>&1 &
            echo $! > "$MEFRPC_PID_FILE"
            echo "MEFRP隧道已启动 (PID: $!)"
            echo "公网: https://101.133.233.101:40001"
        fi
        ;;
    stop)
        if [ -f "$MEFRPC_PID_FILE" ]; then
            kill $(cat "$MEFRPC_PID_FILE") 2>/dev/null
            rm -f "$MEFRPC_PID_FILE"
            echo "MEFRP隧道已停止"
        else
            echo "MEFRP隧道未运行"
        fi
        if [ -f "$PID_FILE" ]; then
            kill $(cat "$PID_FILE") 2>/dev/null
            rm -f "$PID_FILE"
            echo "智桥网关已停止"
        else
            echo "智桥网关未运行"
        fi
        ;;
    restart)
        $0 stop
        sleep 1
        $0 start
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "智桥网关运行中 (PID: $(cat $PID_FILE))"
            echo "健康检查: https://localhost:8767/v1/health"
        else
            echo "智桥网关未运行"
        fi
        if [ -f "$MEFRPC_PID_FILE" ] && kill -0 $(cat "$MEFRPC_PID_FILE") 2>/dev/null; then
            echo "MEFRP隧道运行中 (PID: $(cat $MEFRPC_PID_FILE))"
            echo "公网: https://101.133.233.101:40001"
        else
            echo "MEFRP隧道未运行"
        fi
        ;;
    test)
        cd "$GATEWAY_DIR"
        PYTHONPATH=. python3 -m pytest gateway/tests/ -v
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|test}"
        exit 1
        ;;
esac
