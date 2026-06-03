# 智桥配置使用指南

本文档演示如何使用智桥的配置功能来移除硬编码的 localhost 引用。

## 快速开始

### 开发环境（默认配置）

无需任何配置，直接启动：

```bash
python3 relay-server/start_server.py
```

服务器将使用默认值：
- 绑定地址：`0.0.0.0:8765`
- 客户端连接：`ws://localhost:8765`

访问 Web UI：
```
http://localhost:8000/web/ui/index.html
```

---

## 场景 1: 本地开发

### 后端配置

使用默认配置即可，无需额外设置。

### 前端配置

如果需要修改前端默认值，创建配置文件：

```bash
# 1. 复制示例文件
cp web/ui/config/config.js.example web/ui/config/config.js

# 2. 编辑配置文件
nano web/ui/config/config.js
```

示例配置：

```javascript
window.ZHINENG_BRIDGE_CONFIG = {
    WS_HOST: 'localhost',
    WS_PORT: 8765,
    THEME: 'light',
    LANGUAGE: 'zh-CN'
};
```

---

## 场景 2: 使用环境变量

适用于不想创建配置文件的情况，或用于快速测试。

### 方法 1: 命令行设置

```bash
# 设置环境变量并启动
export ZHINENG_BRIDGE_WS_HOST="my-server.example.com"
python3 relay-server/start_server.py
```

### 方法 2: 创建 .env 文件

创建 `.env` 文件：

```bash
# .env
ZHINENG_BRIDGE_WS_HOST=my-server.example.com
ZHINENG_BRIDGE_SERVER_PORT=9000
```

启动时自动加载：

```bash
python3 relay-server/start_server.py
```

### 方法 3: 使用 source 命令

```bash
# 创建配置脚本
cat > prod-env.sh << 'EOF'
export ZHINENG_BRIDGE_WS_HOST="prod-server.example.com"
export ZHINENG_BRIDGE_SERVER_PORT="9000"
export ZHINENG_BRIDGE_ENABLE_WSS="true"
EOF

# 加载配置并启动
source prod-env.sh
python3 relay-server/start_server.py
```

---

## 场景 3: 生产环境部署

### 步骤 1: 配置后端

创建 `.env.prod` 文件：

```bash
cat > .env.prod << 'EOF'
# 服务器配置
ZHINENG_BRIDGE_WS_HOST=api.yourdomain.com
ZHINENG_BRIDGE_SERVER_PORT=8765

# WSS 配置
ZHINENG_BRIDGE_ENABLE_WSS=true
ZHINENG_BRIDGE_CERT_FILE=/etc/ssl/certs/zhineng-bridge.crt
ZHINENG_BRIDGE_KEY_FILE=/etc/ssl/private/zhineng-bridge.key

# 数据库配置
ZHINENG_BRIDGE_DB_PG_HOST=db.yourdomain.com
ZHINENG_BRIDGE_DB_PG_PORT=5432
ZHINENG_BRIDGE_DB_PG_DATABASE=zhineng_bridge
ZHINENG_BRIDGE_DB_PG_USER=zhineng_bridge
ZHINENG_BRIDGE_DB_PG_PASSWORD=your_secure_password

# 安全配置
ZHINENG_BRIDGE_SECURITY_ENABLE_AUTH=true
ZHINENG_BRIDGE_SECURITY_SECRET_KEY=your_secret_key_here
EOF
```

### 步骤 2: 配置前端

创建 `web/ui/config/config.js` 文件：

```javascript
window.ZHINENG_BRIDGE_CONFIG = {
    // 生产服务器地址
    WS_HOST: 'api.yourdomain.com',
    WS_PORT: 8765,

    // 配置项
    AUTO_RECONNECT: true,
    RECONNECT_INTERVAL: 5,
    PING_INTERVAL: 10,
    OUTPUT_SCROLL: true,
    OUTPUT_MAX_LINES: 1000,
    COMMAND_HISTORY: true,
    THEME: 'light',
    LANGUAGE: 'zh-CN'
};
```

### 步骤 3: 部署

**选项 A: 直接启动**

```bash
source .env.prod
python3 relay-server/start_server.py
```

**选项 B: 使用 Docker Compose**

```bash
# 构建并启动
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 停止
docker-compose -f docker-compose.prod.yml down
```

**选项 C: 使用部署脚本**

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

---

## 场景 4: 多环境配置

### 目录结构

```
zhineng-bridge/
├── .env.dev          # 开发环境
├── .env.staging      # 测试环境
├── .env.prod         # 生产环境
└── web/ui/config/
    ├── dev.js        # 开发前端配置
    ├── staging.js    # 测试前端配置
    └── prod.js       # 生产前端配置
```

### 切换环境脚本

```bash
#!/bin/bash
# 切换环境

ENV=$1

if [ -z "$ENV" ]; then
    echo "用法: ./switch-env.sh [dev|staging|prod]"
    exit 1
fi

# 复制对应的环境变量文件
cp .env.$ENV .env

# 复制对应的前端配置
cp web/ui/config/$ENV.js web/ui/config/config.js

echo "✅ 已切换到 $ENV 环境"
echo "📋 当前配置:"
cat .env | grep -E "^(ZHINENG_BRIDGE_)="
```

使用：

```bash
./switch-env.sh dev      # 切换到开发环境
./switch-env.sh prod     # 切换到生产环境
```

---

## 配置项说明

### 后端环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ZHINENG_BRIDGE_HOST` | 服务器绑定地址 | `0.0.0.0` |
| `ZHINENG_BRIDGE_PORT` | 服务器端口 | `8765` |
| `ZHINENG_BRIDGE_WS_HOST` | WebSocket 客户端连接地址 | `localhost` |
| `ZHINENG_BRIDGE_ENABLE_WSS` | 启用 WSS | `false` |
| `ZHINENG_BRIDGE_CERT_FILE` | SSL 证书路径 | `None` |
| `ZHINENG_BRIDGE_KEY_FILE` | SSL 私钥路径 | `None` |

### 前端配置项

| 配置项 | 说明 | 默认值 | 类型 |
|--------|------|--------|------|
| `WS_HOST` | WebSocket 服务器地址 | `localhost` | string |
| `WS_PORT` | WebSocket 端口 | `8765` | number |
| `AUTO_RECONNECT` | 自动重连 | `true` | boolean |
| `RECONNECT_INTERVAL` | 重连间隔（秒） | `5` | number |
| `PING_INTERVAL` | 心跳间隔（秒） | `10` | number |
| `OUTPUT_SCROLL` | 自动滚动 | `true` | boolean |
| `OUTPUT_MAX_LINES` | 最大输出行数 | `1000` | number |
| `COMMAND_HISTORY` | 保存命令历史 | `true` | boolean |
| `THEME` | 主题 | `light` | string |
| `LANGUAGE` | 语言 | `zh-CN` | string |

---

## 验证配置

### 验证后端配置

```bash
python3 -c "
import sys
sys.path.insert(0, 'relay-server')
from config import settings
print('✅ 配置验证:')
print(f'   服务器绑定: {settings.server.host}:{settings.server.port}')
print(f'   客户端连接: {settings.server.ws_host}:{settings.server.port}')
print(f'   启用 WSS: {settings.server.enable_wss}')
"
```

### 验证前端配置

在浏览器控制台执行：

```javascript
console.log('✅ 前端配置:', window.ZHINENG_BRIDGE_CONFIG);
```

---

## 故障排查

### 问题 1: 连接失败

**症状**: 客户端无法连接到服务器

**解决方案**:

1. 检查后端配置：
```bash
python3 -c "
import sys
sys.path.insert(0, 'relay-server')
from config import settings
print(f'ws_host: {settings.server.ws_host}')
print(f'port: {settings.server.port}')
"
```

2. 检查前端配置：
```javascript
console.log('WS_HOST:', window.ZHINENG_BRIDGE_CONFIG?.WS_HOST);
console.log('WS_PORT:', window.ZHINENG_BRIDGE_CONFIG?.WS_PORT);
```

3. 确保前后端配置一致

### 问题 2: 环境变量未生效

**解决方案**:

1. 确认环境变量已设置：
```bash
echo $ZHINENG_BRIDGE_WS_HOST
```

2. 在启动前加载：
```bash
source .env
python3 relay-server/start_server.py
```

3. 检查 .env 文件格式（不要有空格）

### 问题 3: 前端配置未加载

**解决方案**:

1. 检查配置文件是否存在：
```bash
ls -la web/ui/config/config.js
```

2. 检查浏览器控制台错误

3. 确保配置文件语法正确（可以使用 JSON 验证工具）

---

## 最佳实践

### 1. 安全性

- ✅ 不要将 `.env` 文件提交到 Git
- ✅ 使用强密码和密钥
- ✅ 生产环境使用 HTTPS/WSS
- ✅ 定期更新 SSL 证书

### 2. 维护性

- ✅ 使用有意义的配置文件命名（`.env.prod`, `.env.staging`）
- ✅ 添加注释说明配置项用途
- ✅ 使用版本控制管理示例配置文件（`.env.example`）

### 3. 部署流程

- ✅ 在部署前验证配置
- ✅ 使用配置切换脚本
- ✅ 文档化所有环境变量
- ✅ 监控配置变更

---

## 演示脚本

项目包含以下演示脚本：

```bash
./demo_default_config.sh        # 默认配置演示
./demo_env_config.sh            # 环境变量配置演示
./demo_frontend_config.sh        # 前端配置演示
./demo_production_config.sh      # 生产环境配置演示
```

---

## 相关文档

- [本地主机移除总结](LOCALHOST_REMOVAL_SUMMARY.md)
- [生产部署指南](docs/PRODUCTION_DEPLOYMENT.md)
- [SSL 设置指南](docs/SSL_SETUP.md)
- [API 文档](docs/API.md)

---

## 支持

如有问题，请查看：
1. 项目文档：`docs/` 目录
2. 示例配置：`.env.example`, `web/ui/config/config.js.example`
3. 故障排查：本文档的"故障排查"部分
