#!/bin/bash
# 演示默认配置使用

echo "=========================================="
echo "演示 1: 默认配置（开发环境）"
echo "=========================================="
echo ""

cd relay-server

echo "📋 当前环境变量（未设置）:"
echo "   ZHINENG_BRIDGE_WS_HOST: 未设置（使用默认值 localhost）"
echo "   ZHINENG_BRIDGE_SERVER_PORT: 未设置（使用默认值 8765）"
echo ""

echo "🚀 启动服务器..."
echo "   服务器将绑定到: 0.0.0.0:8765"
echo "   客户端连接地址: ws://localhost:8765"
echo ""
echo "命令: python3 start_server.py"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""
echo "=========================================="
echo ""

# 实际启动命令（注释掉，仅作演示）
# python3 start_server.py
