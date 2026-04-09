#!/bin/bash
# FRP配置助手

set -e

echo "============================================================"
echo "  智桥 (Zhineng-bridge) FRP 内网穿透配置助手"
echo "============================================================"
echo ""

# 检查配置文件
CONFIG_FILE="/home/ai/zhineng-bridge/config/frpc.ini"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

echo "请输入FRP服务器信息："
echo ""

# 获取服务器地址
read -p "FRP服务器地址 (server_addr): " SERVER_ADDR
if [ -z "$SERVER_ADDR" ]; then
    echo "❌ 服务器地址不能为空"
    exit 1
fi

# 获取服务器端口
read -p "FRP服务器端口 (默认7000): " SERVER_PORT
SERVER_PORT=${SERVER_PORT:-7000}

# 获取认证令牌
read -p "FRP认证令牌 (token): " TOKEN
if [ -z "$TOKEN" ]; then
    echo "❌ 认证令牌不能为空"
    exit 1
fi

echo ""
echo "配置信息："
echo "  服务器地址: $SERVER_ADDR"
echo "  服务器端口: $SERVER_PORT"
echo "  认证令牌: $TOKEN"
echo ""
read -p "确认配置？(y/n): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "取消配置"
    exit 0
fi

# 更新配置文件
echo ""
echo "更新配置文件..."

# 备份原配置
cp "$CONFIG_FILE" "${CONFIG_FILE}.backup"

# 更新配置
sed -i "s|^server_addr = .*|server_addr = $SERVER_ADDR|g" "$CONFIG_FILE"
sed -i "s|^server_port = .*|server_port = $SERVER_PORT|g" "$CONFIG_FILE"
sed -i "s|^token = .*|token = $TOKEN|g" "$CONFIG_FILE"

echo "✅ 配置已更新"
echo ""
echo "配置文件: $CONFIG_FILE"
echo "备份文件: ${CONFIG_FILE}.backup"
echo ""

# 检查frpc是否安装
if ! command -v frpc &> /dev/null; then
    echo "⚠️  frpc未安装"
    echo ""
    echo "安装方法："
    echo ""
    echo "  Linux/macOS:"
    echo "  wget https://github.com/fatedier/frp/releases/download/v0.52.3/frp_0.52.3_linux_amd64.tar.gz"
    echo "  tar -xzf frp_0.52.3_linux_amd64.tar.gz"
    echo "  sudo cp frp_0.52.3_linux_amd64/frpc /usr/local/bin/"
    echo "  sudo chmod +x /usr/local/bin/frpc"
    echo ""
else
    echo "✅ frpc已安装"
    echo ""
    echo "下一步："
    echo "  1. 启动nginx: docker run -d -p 443:443 -v /home/ai/zhineng-bridge/nginx/nginx-local.conf:/etc/nginx/nginx.conf:ro -v /home/ai/zhineng-bridge/nginx/ssl:/etc/nginx/ssl:ro -v /home/ai/zhineng-bridge/web/ui:/app/web:ro nginx:latest"
    echo "  2. 启动frpc: frpc -c $CONFIG_FILE"
    echo "  3. 测试访问: https://$SERVER_ADDR:443/web/ui/index.html"
fi

echo ""
echo "============================================================"
echo "  配置完成！"
echo "============================================================"
