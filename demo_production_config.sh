#!/bin/bash
# 创建生产环境配置示例

echo "=========================================="
echo "演示 4: 创建生产环境配置"
echo "=========================================="
echo ""

echo "🌐 场景: 部署到生产服务器"
echo "   服务器地址: api.zhineng-bridge.com"
echo "   WebSocket 端口: 8765"
echo "   启用 HTTPS/WSS"
echo ""

# 1. 创建后端环境变量文件
echo "📝 创建后端环境变量文件 (.env.prod)..."
cat > .env.prod << 'EOF'
# 智桥生产环境配置
# ======================================

# 服务器配置
ZHINENG_BRIDGE_WS_HOST=api.zhineng-bridge.com
ZHINENG_BRIDGE_SERVER_PORT=8765

# 启用 WSS (WebSocket Secure)
ZHINENG_BRIDGE_ENABLE_WSS=true
ZHINENG_BRIDGE_CERT_FILE=/etc/ssl/certs/zhineng-bridge.crt
ZHINENG_BRIDGE_KEY_FILE=/etc/ssl/private/zhineng-bridge.key

# 数据库配置（生产环境使用 PostgreSQL）
ZHINENG_BRIDGE_DB_PG_HOST=db.zhineng-bridge.com
ZHINENG_BRIDGE_DB_PG_PORT=5432
ZHINENG_BRIDGE_DB_PG_DATABASE=zhineng_bridge
ZHINENG_BRIDGE_DB_PG_USER=zhineng_bridge
ZHINENG_BRIDGE_DB_PG_PASSWORD=CHANGE_THIS_PASSWORD

# 安全配置
ZHINENG_BRIDGE_SECURITY_ENABLE_AUTH=true
ZHINENG_BRIDGE_SECURITY_AUTH_TYPE=token
ZHINENG_BRIDGE_SECURITY_SECRET_KEY=CHANGE_THIS_SECRET_KEY

# 监控配置
ZHINENG_BRIDGE_MONITORING_ENABLE_PROMETHEUS=true
ZHINENG_BRIDGE_MONITORING_ENABLE_HEALTH_CHECK=true
EOF

echo "✅ 已创建: .env.prod"
echo ""

# 2. 创建前端配置文件
echo "📝 创建前端配置文件 (web/ui/config/config.js)..."
cat > web/ui/config/config.js << 'EOF'
/**
 * 智桥生产环境配置
 *
 * 此配置文件用于生产环境部署
 */

window.ZHINENG_BRIDGE_CONFIG = {
    // WebSocket 服务器配置
    WS_HOST: 'api.zhineng-bridge.com',  // 生产服务器地址
    WS_PORT: 8765,                       // WebSocket 端口

    // 自动重连配置
    AUTO_RECONNECT: true,
    RECONNECT_INTERVAL: 5,  // 重连间隔（秒）

    // 心跳配置
    PING_INTERVAL: 10,  // 心跳间隔（秒）

    // 输出显示配置
    OUTPUT_SCROLL: true,      // 新输出时自动滚动到底部
    OUTPUT_MAX_LINES: 1000,  // 终端最大显示行数

    // 命令历史配置
    COMMAND_HISTORY: true,  // 保存命令历史记录

    // UI 配置
    THEME: 'light',      // 应用主题: 'light' 或 'dark'
    LANGUAGE: 'zh-CN'   // 应用界面语言: 'zh-CN' 或 'en-US'
};
EOF

echo "✅ 已创建: web/ui/config/config.js"
echo ""

# 3. 显示配置摘要
echo "📋 配置摘要:"
echo ""
echo "后端配置 (.env.prod):"
echo "   - WebSocket 服务器: api.zhineng-bridge.com:8765"
echo "   - 启用 WSS: 是"
echo "   - 数据库: PostgreSQL"
echo "   - 启用认证: 是"
echo "   - 启用 Prometheus: 是"
echo ""
echo "前端配置 (web/ui/config/config.js):"
echo "   - 连接地址: ws://api.zhineng-bridge.com:8765"
echo "   - 主题: light"
echo "   - 语言: zh-CN"
echo ""

# 4. 提供部署命令
echo "🚀 部署命令:"
echo ""
echo "1. 启动生产服务器:"
echo "   source .env.prod && python3 relay-server/start_server.py"
echo ""
echo "2. 或使用 Docker Compose:"
echo "   docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "3. 访问 Web UI:"
echo "   http://localhost:8000/web/ui/index.html"
echo ""

# 5. 安全警告
echo "⚠️  安全警告:"
echo "   在部署前必须修改以下配置:"
echo "   - .env.prod 中的数据库密码"
echo "   - .env.prod 中的 SECRET_KEY"
echo "   - 确保证书文件路径正确"
echo ""

echo "=========================================="
echo ""
