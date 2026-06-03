#!/bin/bash
set -e

echo "🚀 Starting zhineng-bridge services..."

# 等待几秒确保所有依赖就绪
sleep 2

# 如果启用 WSS 但证书不存在，生成开发证书
if [ "${ZHINENG_BRIDGE_ENABLE_WSS:-false}" = "true" ]; then
    echo "🔒 WSS enabled, checking certificates..."
    CERT_FILE="${ZHINENG_BRIDGE_CERT_FILE:-/app/certs/cert.pem}"
    KEY_FILE="${ZHINENG_BRIDGE_KEY_FILE:-/app/certs/key.pem}"

    if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
        echo "📜 Generating self-signed SSL certificates..."
        mkdir -p /app/certs
        python3 -c "from relay_server.ssl import setup_development_certificates; setup_development_certificates()"
        echo "✅ SSL certificates generated"
    else
        echo "✅ SSL certificates found"
    fi

    # 设置环境变量
    export ZHINENG_BRIDGE_CERT_FILE="$CERT_FILE"
    export ZHINENG_BRIDGE_KEY_FILE="$KEY_FILE"

    # 确定协议
    WS_PROTOCOL="wss"
    echo "🔐 WSS enabled"
else
    # 确定协议
    WS_PROTOCOL="ws"
    echo "📡 WSS disabled, using plain WebSocket"
fi

# 在后台启动 Health Check Server
echo "🏥 Starting Health Check Server on port 8000..."
cd /app/relay-server && python3 health_check.py &
HEALTH_PID=$!

# 等待健康检查服务器启动
sleep 1

# 检查健康检查服务器是否运行
if kill -0 $HEALTH_PID 2>/dev/null; then
    echo "✅ Health Check Server started (PID: $HEALTH_PID)"
else
    echo "❌ Health Check Server failed to start"
    exit 1
fi

# 在后台启动 Relay Server
echo "📡 Starting Relay Server on port ${ZHINENG_BRIDGE_PORT:-8765}..."
cd /app/relay-server && python3 start_server.py &
RELAY_PID=$!

# 等待进程启动
sleep 2

# 检查进程是否运行
if kill -0 $RELAY_PID 2>/dev/null; then
    echo "✅ Relay Server started (PID: $RELAY_PID)"
else
    echo "❌ Relay Server failed to start"
    exit 1
fi

echo ""
echo "📊 Service Status:"
echo "  - Health Check:  http://0.0.0.0:8000/health"
echo "  - Relay Server:  ${WS_PROTOCOL}://0.0.0.0:${ZHINENG_BRIDGE_PORT:-8765}"
echo "  - Metrics:       http://0.0.0.0:8000/metrics"
echo "  - Status:        http://0.0.0.0:8000/status"

if [ "${ZHINENG_BRIDGE_ENABLE_WSS:-false}" = "true" ]; then
    echo "  - Security:      🔒 TLS/SSL enabled"
    echo "  - Certificate:   ${ZHINENG_BRIDGE_CERT_FILE}"
fi

echo ""
echo "✨ All services started successfully!"
echo ""

# 保持容器运行
wait $RELAY_PID $HEALTH_PID
