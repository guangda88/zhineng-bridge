#!/bin/bash
# 停止智桥服务（内网穿透模式）

echo "============================================================"
echo "  停止智桥服务（内网穿透模式）"
echo "============================================================"
echo ""

# 停止FRP client
if [ -f /tmp/frpc.pid ]; then
    PID=$(cat /tmp/frpc.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "🛑 停止FRP client (PID: $PID)..."
        kill $PID
        sleep 1
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️  强制停止FRP client..."
            kill -9 $PID
        fi
        echo "✅ FRP client已停止"
    fi
    rm -f /tmp/frpc.pid
fi

# 停止Nginx
if command -v docker &> /dev/null; then
    if docker ps | grep -q zhineng-nginx; then
        echo "🛑 停止Nginx容器..."
        docker stop zhineng-nginx
        docker rm zhineng-nginx
        echo "✅ Nginx已停止"
    fi
fi

# 停止Session Manager
if [ -f /home/ai/zhineng-bridge/phase1/session_manager/.session_manager.pid ]; then
    PID=$(cat /home/ai/zhineng-bridge/phase1/session_manager/.session_manager.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "🛑 停止Session Manager (PID: $PID)..."
        kill $PID
        sleep 1
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️  强制停止Session Manager..."
            kill -9 $PID
        fi
        echo "✅ Session Manager已停止"
    fi
    rm -f /home/ai/zhineng-bridge/phase1/session_manager/.session_manager.pid
fi

# 停止Relay Server
if [ -f /home/ai/zhineng-bridge/relay-server/.ws_server.pid ]; then
    PID=$(cat /home/ai/zhineng-bridge/relay-server/.ws_server.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "🛑 停止Relay Server (PID: $PID)..."
        kill $PID
        sleep 1
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️  强制停止Relay Server..."
            kill -9 $PID
        fi
        echo "✅ Relay Server已停止"
    fi
    rm -f /home/ai/zhineng-bridge/relay-server/.ws_server.pid
fi

echo ""
echo "============================================================"
echo "  ✅ 所有服务已停止"
echo "============================================================"
echo ""
