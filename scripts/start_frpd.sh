#!/bin/bash
# 启动智桥服务（内网穿透模式）

set -e

echo "============================================================"
echo "  智桥 (Zhineng-bridge) 内网穿透模式启动"
echo "============================================================"
echo ""

# 检查FRP配置
FRP_CONFIG="/home/ai/zhineng-bridge/config/frpc.ini"
if [ ! -f "$FRP_CONFIG" ]; then
    echo "❌ FRP配置文件不存在: $FRP_CONFIG"
    echo ""
    echo "请先运行: ./scripts/setup_frp.sh"
    exit 1
fi

# 检查配置是否已填写
if grep -q "frp.example.com" "$FRP_CONFIG" || grep -q "your_frp_token_here" "$FRP_CONFIG"; then
    echo "❌ FRP配置未填写完整"
    echo ""
    echo "请先运行: ./scripts/setup_frp.sh"
    exit 1
fi

# 提取配置信息
SERVER_ADDR=$(grep "^server_addr" "$FRP_CONFIG" | awk '{print $3}')
echo "FRP服务器: $SERVER_ADDR"
echo ""

# 启动relay server
echo "📡 启动relay server..."
cd /home/ai/zhineng-bridge/relay-server
if [ -f .ws_server.pid ]; then
    PID=$(cat .ws_server.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Relay server已运行 (PID: $PID)"
    else
        rm -f .ws_server.pid
        python3 start_server.py > /tmp/relay_server.log 2>&1 &
        RELAY_PID=$!
        echo "✅ Relay server已启动 (PID: $RELAY_PID)"
        echo $RELAY_PID > .ws_server.pid
    fi
else
    python3 start_server.py > /tmp/relay_server.log 2>&1 &
    RELAY_PID=$!
    echo "✅ Relay server已启动 (PID: $RELAY_PID)"
    echo $RELAY_PID > .ws_server.pid
fi

# 启动session manager
echo "🎛️  启动session manager..."
cd /home/ai/zhineng-bridge/phase1/session_manager
if [ -f .session_manager.pid ]; then
    PID=$(cat .session_manager.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Session manager已运行 (PID: $PID)"
    else
        rm -f .session_manager.pid
        python3 start_manager.py > /tmp/session_manager.log 2>&1 &
        MGR_PID=$!
        echo "✅ Session manager已启动 (PID: $MGR_PID)"
        echo $MGR_PID > .session_manager.pid
    fi
else
    python3 start_manager.py > /tmp/session_manager.log 2>&1 &
    MGR_PID=$!
    echo "✅ Session manager已启动 (PID: $MGR_PID)"
    echo $MGR_PID > .session_manager.pid
fi

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 3

# 检查docker是否安装
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker未安装，跳过nginx启动"
    echo "请手动安装Docker并启动nginx"
else
    # 停止旧容器
    if docker ps -a | grep -q zhineng-nginx; then
        echo "🛑 停止旧nginx容器..."
        docker stop zhineng-nginx 2>/dev/null || true
        docker rm zhineng-nginx 2>/dev/null || true
    fi

    # 启动nginx
    echo "🌐 启动nginx..."
    docker run -d \
        --name zhineng-nginx \
        --restart unless-stopped \
        -p 80:80 \
        -p 443:443 \
        -v /home/ai/zhineng-bridge/nginx/nginx-local.conf:/etc/nginx/nginx.conf:ro \
        -v /home/ai/zhineng-bridge/nginx/ssl:/etc/nginx/ssl:ro \
        -v /home/ai/zhineng-bridge/web/ui:/app/web:ro \
        nginx:latest

    if [ $? -eq 0 ]; then
        echo "✅ Nginx已启动"
    else
        echo "❌ Nginx启动失败"
        exit 1
    fi
fi

# 等待nginx启动
echo "⏳ 等待nginx启动..."
sleep 3

# 检查frpc是否安装
if ! command -v frpc &> /dev/null; then
    echo ""
    echo "⚠️  frpc未安装"
    echo ""
    echo "安装命令："
    echo "  wget https://github.com/fatedier/frp/releases/download/v0.52.3/frp_0.52.3_linux_amd64.tar.gz"
    echo "  tar -xzf frp_0.52.3_linux_amd64.tar.gz"
    echo "  sudo cp frp_0.52.3_linux_amd64/frpc /usr/local/bin/"
    echo "  sudo chmod +x /usr/local/bin/frpc"
    echo ""
    echo "安装后手动启动: frpc -c $FRP_CONFIG"
else
    # 停止旧frpc进程
    if [ -f /tmp/frpc.pid ]; then
        PID=$(cat /tmp/frpc.pid)
        if ps -p $PID > /dev/null 2>&1; then
            echo "🛑 停止旧frpc进程..."
            kill $PID 2>/dev/null || true
        fi
        rm -f /tmp/frpc.pid
    fi

    # 启动frpc
    echo "🔌 启动frpc..."
    frpc -c "$FRP_CONFIG" > /tmp/frpc.log 2>&1 &
    FRPC_PID=$!
    echo $FRPC_PID > /tmp/frpc.pid

    if ps -p $FRPC_PID > /dev/null 2>&1; then
        echo "✅ FRP client已启动 (PID: $FRPC_PID)"
    else
        echo "❌ FRP client启动失败，查看日志: tail -f /tmp/frpc.log"
        exit 1
    fi
fi

# 等待frpc连接
echo "⏳ 等待FRP连接..."
sleep 5

echo ""
echo "============================================================"
echo "  ✅ 所有服务已启动！"
echo "============================================================"
echo ""
echo "访问地址："
echo "  本地HTTP:  http://10.113.22.99:8080/web/ui/index.html"
echo "  本地HTTPS: https://10.113.22.99/web/ui/index.html"
echo "  公网HTTP:  http://${SERVER_ADDR}:8080/web/ui/index.html"
echo "  公网HTTPS: https://${SERVER_ADDR}:443/web/ui/index.html"
echo ""
echo "服务状态："
echo "  Relay server:   $(cat /home/ai/zhineng-bridge/relay-server/.ws_server.pid 2>/dev/null || echo '未运行')"
echo "  Session manager: $(cat /home/ai/zhineng-bridge/phase1/session_manager/.session_manager.pid 2>/dev/null || echo '未运行')"
echo "  Nginx:          $(docker ps | grep zhineng-nginx | awk '{print $1}' || echo '未运行')"
echo "  FRP client:     $(cat /tmp/frpc.pid 2>/dev/null || echo '未运行')"
echo ""
echo "日志查看："
echo "  Relay server:   tail -f /tmp/relay_server.log"
echo "  Session manager: tail -f /tmp/session_manager.log"
echo "  Nginx:          docker logs -f zhineng-nginx"
echo "  FRP client:     tail -f /tmp/frpc.log"
echo ""
echo "测试命令："
echo "  本地测试:       curl https://10.113.22.99/health"
echo "  公网测试:       curl https://${SERVER_ADDR}/health"
echo ""
echo "停止所有服务:     ./scripts/stop_frpd.sh"
echo ""
