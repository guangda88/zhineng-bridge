# 配置快速参考

## 🚀 30秒快速启动

### 开发环境
```bash
python3 relay-server/start_server.py
# 访问: http://localhost:8000/web/ui/index.html
```

### 生产环境
```bash
# 1. 设置环境变量
export ZHINENG_BRIDGE_WS_HOST="api.yourdomain.com"

# 2. 启动服务器
python3 relay-server/start_server.py
```

---

## 📝 常用配置

### 后端环境变量

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `ZHINENG_BRIDGE_WS_HOST` | `localhost` | WebSocket 服务器地址（客户端连接用） |
| `ZHINENG_BRIDGE_SERVER_PORT` | `8765` | 服务器端口 |
| `ZHINENG_BRIDGE_ENABLE_WSS` | `false` | 启用 WSS (WebSocket Secure) |

### 前端配置（web/ui/config/config.js）

```javascript
window.ZHINENG_BRIDGE_CONFIG = {
    WS_HOST: 'localhost',    // WebSocket 服务器地址
    WS_PORT: 8765,           // 端口号
    THEME: 'light',          // 主题: light 或 dark
    LANGUAGE: 'zh-CN'        // 语言: zh-CN 或 en-US
};
```

---

## 🔧 配置方法

### 方法 1: 命令行（临时）
```bash
export ZHINENG_BRIDGE_WS_HOST="my-server.com"
python3 relay-server/start_server.py
```

### 方法 2: .env 文件（推荐）
```bash
# 创建 .env 文件
cat > .env << 'EOF'
ZHINENG_BRIDGE_WS_HOST=my-server.com
ZHINENG_BRIDGE_SERVER_PORT=8765
EOF

# 启动服务器（自动加载 .env）
python3 relay-server/start_server.py
```

### 方法 3: 前端配置文件（Web UI）
```bash
# 1. 复制示例文件
cp web/ui/config/config.js.example web/ui/config/config.js

# 2. 编辑配置
nano web/ui/config/config.js
```

---

## ✅ 验证配置

### 检查后端配置
```bash
python3 -c "
import sys
sys.path.insert(0, 'relay-server')
from config import settings
print(f'✅ ws_host: {settings.server.ws_host}')
print(f'✅ port: {settings.server.port}')
"
```

### 检查前端配置
在浏览器控制台：
```javascript
console.log(window.ZHINENG_BRIDGE_CONFIG);
```

---

## 🌟 典型场景

### 场景 1: 本地开发
```bash
# 无需配置，使用默认值
python3 relay-server/start_server.py
```

### 场景 2: 内网服务器
```bash
export ZHINENG_BRIDGE_WS_HOST="192.168.1.100"
python3 relay-server/start_server.py
```

### 场景 3: 公网部署
```bash
# .env
ZHINENG_BRIDGE_WS_HOST="api.example.com"
ZHINENG_BRIDGE_SERVER_PORT=8765
ZHINENG_BRIDGE_ENABLE_WSS=true

# 启动
python3 relay-server/start_server.py
```

### 场景 4: Docker 部署
```bash
# docker-compose.prod.yml
services:
  zhineng-bridge:
    environment:
      - ZHINENG_BRIDGE_WS_HOST=api.example.com
      - ZHINENG_BRIDGE_SERVER_PORT=8765

# 启动
docker-compose -f docker-compose.prod.yml up -d
```

---

## ⚠️ 常见问题

### Q: 修改了环境变量但不生效？
**A**: 确保在启动前加载环境变量：
```bash
source .env
python3 relay-server/start_server.py
```

### Q: 前端显示连接失败？
**A**: 检查浏览器控制台，确保前后端配置一致：
- 后端 `ZHINENG_BRIDGE_WS_HOST` 应等于前端 `WS_HOST`
- 后端 `ZHINENG_BRIDGE_SERVER_PORT` 应等于前端 `WS_PORT`

### Q: 想用不同的端口？
**A**:
```bash
export ZHINENG_BRIDGE_SERVER_PORT=9000
python3 relay-server/start_server.py
```

---

## 📚 更多信息

- [完整配置指南](CONFIGURATION_GUIDE.md)
- [本地主机移除总结](LOCALHOST_REMOVAL_SUMMARY.md)
- [生产部署指南](docs/PRODUCTION_DEPLOYMENT.md)
