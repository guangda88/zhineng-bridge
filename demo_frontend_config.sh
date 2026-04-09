#!/bin/bash
# 演示前端配置

echo "=========================================="
echo "演示 3: 前端 Web UI 配置"
echo "=========================================="
echo ""

echo "📂 配置文件位置: web/ui/config/config.js"
echo ""

echo "📋 检查当前配置..."
if [ -f "web/ui/config/config.js" ]; then
    echo "✅ 配置文件已存在:"
    cat web/ui/config/config.js
else
    echo "⚠️  配置文件不存在，使用默认配置"
    echo ""
    echo "📄 默认配置值（从 window.ZHINENG_BRIDGE_CONFIG）:"
    echo "   WS_HOST: localhost"
    echo "   WS_PORT: 8765"
    echo "   AUTO_RECONNECT: true"
    echo "   THEME: light"
    echo "   LANGUAGE: zh-CN"
    echo ""
    echo "📝 创建生产配置文件..."
    cp web/ui/config/config.js.example web/ui/config/config.js
    echo "✅ 已创建: web/ui/config/config.js"
    echo ""
    echo "📖 编辑配置文件以自定义设置:"
    echo "   nano web/ui/config/config.js"
    echo "   或"
    echo "   vim web/ui/config/config.js"
fi
echo ""

echo "=========================================="
echo ""
