#!/bin/bash

GATEWAY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$GATEWAY_DIR/gateway.pid"
LOG_FILE="$GATEWAY_DIR/gateway.log"

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "智桥网关已在运行 (PID: $(cat $PID_FILE))"
            exit 0
        fi
        PYTHONPATH=/home/ai/zhibridge python3 -m gateway.app >> "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "智桥网关已启动 (PID: $!)"
        echo "端口: 8767"
        echo "日志: $LOG_FILE"
        ;;
    stop)
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
            echo "健康检查: http://localhost:8767/v1/health"
        else
            echo "智桥网关未运行"
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
