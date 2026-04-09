#!/bin/bash
# 服务日志监视脚本

echo "================================================================================"
echo "🔍 zhineng-bridge 服务监视"
echo "================================================================================"
echo ""

# 检查服务进程
echo "📊 服务进程状态:"
echo "----------------------------------------"
ps aux | grep -E "(start_server|start_manager)" | grep -v grep | awk '{print "  PID: "$2" | CMD: "$11" "$12}'
echo ""

# 检查端口监听
echo "🌐 端口监听状态:"
echo "----------------------------------------"
for port in 8765 8000; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "  ✅ 端口 $port: 监听中"
        lsof -i :$port | grep LISTEN
    else
        echo "  ❌ 端口 $port: 未监听"
    fi
done
echo ""

# 检查日志文件
echo "📝 日志文件位置:"
echo "----------------------------------------"
log_dirs=(
    "/home/ai/zhineng-bridge/logs"
    "/home/ai/.zhineng-bridge/logs"
    "/tmp"
)

for log_dir in "${log_dirs[@]}"; do
    if [ -d "$log_dir" ]; then
        log_files=$(find "$log_dir" -name "*.log" -o -name "*zhineng*" 2>/dev/null | head -5)
        if [ -n "$log_files" ]; then
            echo "  📂 $log_dir:"
            echo "$log_files" | sed 's/^/    /'
        fi
    fi
done
echo ""

# 显示服务健康状态
echo "💚 服务健康检查:"
echo "----------------------------------------"
# WebSocket 服务器健康检查
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✅ Health Check Server (port 8000): 正常"
    curl -s http://localhost:8000/health | head -10 | sed 's/^/    /'
else
    echo "  ❌ Health Check Server (port 8000): 不可用"
fi

if curl -s http://localhost:8000/status > /dev/null 2>&1; then
    echo ""
    echo "  ✅ Status Endpoint:"
    curl -s http://localhost:8000/status | head -20 | sed 's/^/    /'
fi
echo ""

echo "================================================================================"
echo "🔍 实时日志监视 (Ctrl+C 退出)"
echo "================================================================================"
echo ""

# 实时监视日志
echo "📡 监视中... (按 Ctrl+C 停止)"
echo ""

while true; do
    clear
    echo "================================================================================"
    echo "🔍 zhineng-bridge 服务监视 - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "================================================================================"
    echo ""

    # 进程状态
    echo "📊 进程状态:"
    echo "----------------------------------------"
    ps aux | grep -E "(start_server|start_manager)" | grep -v grep | awk '{
        printf "  PID: %-8s | CPU: %-5s | MEM: %-5s | %s\n", $2, $3"%", $4"%", $11" "$12
    }'
    echo ""

    # 端口状态
    echo "🌐 端口状态:"
    echo "----------------------------------------"
    for port in 8765 8000; do
        if lsof -i :$port > /dev/null 2>&1; then
            pid=$(lsof -i :$port | grep LISTEN | awk '{print $2}')
            echo "  ✅ 端口 $port (PID: $pid): 监听中"
        else
            echo "  ❌ 端口 $port: 未监听"
        fi
    done
    echo ""

    # 最近的活动日志（如果有）
    echo "📝 最近活动:"
    echo "----------------------------------------"
    echo "  (等待服务生成日志...)"
    echo ""

    sleep 2
done
