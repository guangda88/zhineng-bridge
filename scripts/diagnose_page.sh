#!/bin/bash
# 智桥页面诊断脚本

echo "============================================================"
echo "  智桥页面问题诊断"
echo "============================================================"
echo ""

# 检查服务状态
echo "1️⃣  检查服务状态:"
echo "----------------------------------------"

if ps aux | grep -E "(relay-server|start_server.py)" | grep -v grep > /dev/null; then
    echo "✅ Relay Server 运行中"
else
    echo "❌ Relay Server 未运行"
fi

if ps aux | grep -E "(session-manager|start_manager.py)" | grep -v grep > /dev/null; then
    echo "✅ Session Manager 运行中"
else
    echo "❌ Session Manager 未运行"
fi

echo ""

# 检查端口
echo "2️⃣  检查端口状态:"
echo "----------------------------------------"

for port in 8080 8765; do
    if netstat -tlnp 2>/dev/null | grep ":${port} " > /dev/null; then
        echo "✅ 端口 ${port}: 开放"
    else
        echo "❌ 端口 ${port}: 关闭"
    fi
done

echo ""

# 检查HTTP访问
echo "3️⃣  测试HTTP访问:"
echo "----------------------------------------"

echo "测试: curl http://100.66.1.8:8080/health"
curl -s --connect-timeout 5 http://100.66.1.8:8080/health 2>&1 | head -5 || echo "❌ HTTP访问失败"

echo ""

# 检查WebSocket访问
echo "4️⃣  测试WebSocket访问:"
echo "----------------------------------------"

python3 -c "
import asyncio
import websockets
import json

async def test():
    try:
        async with websockets.connect('ws://100.66.1.8:8765') as ws:
            await ws.send(json.dumps({'type': 'ping'}))
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            print('✅ WebSocket连接成功')
            print(f'响应: {response}')
    except Exception as e:
        print(f'❌ WebSocket连接失败: {e}')

asyncio.run(test())
" 2>&1 || echo "❌ WebSocket测试失败"

echo ""

# 检查文件权限
echo "5️⃣  检查Web文件:"
echo "----------------------------------------"

if [ -f /home/ai/zhineng-bridge/web/ui/index.html ]; then
    echo "✅ index.html 存在"
    echo "   大小: $(stat -c%s /home/ai/zhineng-bridge/web/ui/index.html) 字节"
else
    echo "❌ index.html 不存在"
fi

if [ -f /home/ai/zhineng-bridge/web/ui/js/app.js ]; then
    echo "✅ app.js 存在"
    echo "   大小: $(stat -c%s /home/ai/zhineng-bridge/web/ui/js/app.js) 字节"
else
    echo "❌ app.js 不存在"
fi

echo ""

# 检查JavaScript文件
echo "6️⃣  检查JavaScript文件完整性:"
echo "----------------------------------------"

js_files=(
    "/home/ai/zhineng-bridge/web/ui/js/settings.js"
    "/home/ai/zhineng-bridge/web/ui/js/tools.js"
    "/home/ai/zhineng-bridge/web/ui/js/sessions.js"
    "/home/ai/zhineng-bridge/web/ui/js/client.js"
    "/home/ai/zhineng-bridge/web/ui/js/improvements.js"
    "/home/ai/zhineng-bridge/web/ui/js/app.js"
)

for file in "${js_files[@]}"; do
    if [ -f "$file" ]; then
        size=$(stat -c%s "$file")
        if [ $size -gt 1000 ]; then
            echo "✅ $(basename $file): ${size} 字节"
        else
            echo "⚠️  $(basename $file): ${size} 字节 (可能不完整)"
        fi
    else
        echo "❌ $(basename $file): 不存在"
    fi
done

echo ""

# 检查日志
echo "7️⃣  检查服务日志（最后20行）:"
echo "----------------------------------------"

if [ -f /tmp/relay_server.log ]; then
    echo "--- Relay Server 日志 ---"
    tail -5 /tmp/relay_server.log
else
    echo "ℹ️  Relay Server 日志文件不存在"
fi

echo ""

if [ -f /tmp/session_manager.log ]; then
    echo "--- Session Manager 日志 ---"
    tail -5 /tmp/session_manager.log
else
    echo "ℹ️  Session Manager 日志文件不存在"
fi

echo ""
echo "============================================================"
echo "  诊断完成"
echo "============================================================"
echo ""
echo "📋 可能的问题和解决方案:"
echo ""
echo "问题1: 页面显示但点击无反应"
echo "  可能原因: JavaScript未正确加载"
echo "  解决方案: 打开浏览器开发者工具 (F12) 查看Console标签页"
echo ""
echo "问题2: 显示'未连接'"
echo "  可能原因: WebSocket连接失败"
echo "  解决方案: 检查网络连接，测试WebSocket连接"
echo ""
echo "问题3: 资源加载失败"
echo "  可能原因: 文件路径错误或权限问题"
echo "  解决方案: 使用调试页面 http://100.66.1.8:8080/web/ui/debug-simple.html"
echo ""
echo "🔍 调试页面:"
echo "  http://100.66.1.8:8080/web/ui/debug-simple.html"
echo ""
echo "📱 浏览器调试:"
echo "  1. 打开 http://100.66.1.8:8080/web/ui/index.html"
echo "  2. 按F12打开开发者工具"
echo "  3. 查看Console标签页的错误信息"
echo "  4. 查看Network标签页的加载状态"
echo ""
