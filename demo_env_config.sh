#!/bin/bash
# 演示环境变量配置使用

echo "=========================================="
echo "演示 2: 环境变量配置（生产环境）"
echo "=========================================="
echo ""

echo "📋 设置环境变量:"
export ZHINENG_BRIDGE_WS_HOST="prod-server.example.com"
export ZHINENG_BRIDGE_SERVER_PORT="9000"
echo "   ZHINENG_BRIDGE_WS_HOST=$ZHINENG_BRIDGE_WS_HOST"
echo "   ZHINENG_BRIDGE_SERVER_PORT=$ZHINENG_BRIDGE_SERVER_PORT"
echo ""

echo "🧪 验证配置..."
python3 -c "
import sys
sys.path.insert(0, 'relay-server')
from config import settings
print(f'✅ 配置已加载:')
print(f'   Server host (bind): {settings.server.host}')
print(f'   Server ws_host (client): {settings.server.ws_host}')
print(f'   Server port: {settings.server.port}')
"
echo ""

echo "🚀 启动服务器..."
echo "   服务器将绑定到: 0.0.0.0:9000"
echo "   客户端连接地址: ws://prod-server.example.com:9000"
echo ""
echo "命令: python3 relay-server/start_server.py"
echo ""
echo "=========================================="
echo ""
