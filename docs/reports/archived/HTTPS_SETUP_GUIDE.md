# 智桥 HTTPS 配置指南

本文档介绍如何为智桥设置 HTTPS 支持。

## 为什么需要 HTTPS？

推送通知（Web Push API）**必须**在 HTTPS 下工作。只有 `localhost` 是例外（但也有限制）。

## 开发环境 - 自签名证书

### 1. 生成自签名证书

项目提供了一个自动生成脚本：

```bash
./scripts/generate-https-certs.sh [证书目录] [证书名称] [有效期天数]
```

示例：
```bash
./scripts/generate-https-certs.sh
# 使用默认值：~/.zhineng-bridge/certs, zhineng-bridge, 365 天
```

这将生成：
- `zhineng-bridge.crt` - 证书文件
- `zhineng-bridge.key` - 私钥文件
- `zhineng-bridge.p12` - PKCS#12 格式（某些浏览器需要）

### 2. 配置服务器使用 HTTPS

修改 `relay-server/start_server.py`：

```python
import ssl
from pathlib import Path

# 证书路径
cert_dir = Path.home() / ".zhineng-bridge/certs"
cert_file = cert_dir / "zhineng-bridge.crt"
key_file = cert_dir / "zhineng-bridge.key"

# 创建 SSL 上下文
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(str(cert_file), str(key_file))

# 启动 HTTPS 服务器
server = AIRelayServer(host="0.0.0.0", port=8766)
# 在 server.start() 中使用 ssl_context
```

或者使用环境变量配置：
```bash
export ZHINENG_BRIDGE_HTTPS_CERT_PATH="$HOME/.zhineng-bridge/certs/zhineng-bridge.crt"
export ZHINENG_BRIDGE_HTTPS_KEY_PATH="$HOME/.zhineng-bridge/certs/zhineng-bridge.key"
```

### 3. 信任自签名证书（浏览器）

#### Chrome / Edge

1. 访问 `chrome://settings/certificates`
2. 切换到 "受信任的根证书颁发机构" 标签
3. 点击 "导入"
4. 选择 `zhineng-bridge.crt`
5. 重启浏览器

#### Firefox

1. 访问 `about:preferences#privacy`
2. 点击 "安全" -> "查看证书"
3. 切换到 "证书颁发机构" 标签
4. 点击 "导入"
5. 选择 `zhineng-bridge.crt`
6. 勾选 "信任此 CA 来标识网站"
7. 点击 "确定"

### 4. 访问 HTTPS

```
https://<你的IP>:8766/web/ui/index.html
```

**第一次访问**：浏览器会显示安全警告，点击 "高级" -> "继续访问"。

## 生产环境 - Let's Encrypt

### 1. 安装 Certbot

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot

# CentOS/RHEL
sudo yum install certbot
```

### 2. 获取证书

```bash
# 使用 DNS 验证（推荐）
sudo certbot certonly --manual --preferred-challenges dns -d zhineng-bridge.com

# 或使用 HTTP 验证（需要服务器在 80 端口可访问）
sudo certbot certonly --webroot -w /var/www/html -d zhineng-bridge.com
```

### 3. 配置 Nginx（推荐）

```nginx
server {
    listen 443 ssl http2;
    server_name zhineng-bridge.com;

    ssl_certificate /etc/letsencrypt/live/zhineng-bridge.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/zhineng-bridge.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # WebSocket 代理
    location / {
        proxy_pass http://127.0.0.1:8766;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 特定配置
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # 推送通知 API
    location /api/notifications/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# HTTP 自动重定向到 HTTPS
server {
    listen 80;
    server_name zhineng-bridge.com;
    return 301 https://$server_name$request_uri;
}
```

### 4. 配置 Apache

```apache
<VirtualHost *:443>
    ServerName zhineng-bridge.com

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/zhineng-bridge.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/zhineng-bridge.com/privkey.pem

    # WebSocket 代理
    ProxyPreserveHost On
    ProxyRequests Off

    ProxyPass / ws://127.0.0.1:8766/
    ProxyPassReverse / ws://127.0.0.1:8766/

    # WebSocket 特定配置
    SSLProxyEngine on
    ProxyTimeout 3600
</VirtualHost>

# HTTP 重定向
<VirtualHost *:80>
    ServerName zhineng-bridge.com
    Redirect permanent / https://zhineng-bridge.com/
</VirtualHost>
```

### 5. 自动续期

```bash
sudo certbot renew --dry-run
# 如果测试成功，添加到 crontab
sudo crontab -e

# 添加（每天凌晨 2 点检查续期）
0 2 * * * certbot renew --quiet && systemctl reload nginx
```

## 移动设备 HTTPS 配置

### Android

1. 将 `zhineng-bridge.crt` 传输到设备
2. 设置 -> 安全 -> 加密与凭据 -> 安装证书 -> CA 证书
3. 选择证书文件
4. 为证书命名（如 "智桥开发"）
5. 选择 "VPN 和应用" 用途
6. 输入 PIN 码确认

### iOS

iOS 不支持手动添加根证书到系统信任存储。开发环境需要：
1. 使用真实的 HTTPS 证书（如 Ngrok、LocalTunnel）
2. 或使用 iOS 模拟器测试

**推荐方案**：使用内网穿透工具进行 HTTPS 代理

## 内网穿透工具（开发测试）

### Ngrok

```bash
# 安装 ngrok
brew install ngrok  # macOS
# 或从 https://ngrok.com 下载

# 启动 HTTPS 隧道
ngrok http 8766

# 访问: https://xxxx-xxxx.ngrok.io/web/ui/index.html
```

### LocalTunnel

```bash
# 安装
npm install -g localtunnel

# 启动
lt --port 8766

# 访问: https://xxxx.loca.lt/web/ui/index.html
```

### Cloudflare Tunnel

```bash
# 安装 cloudflared
brew install cloudflared

# 启动
cloudflared tunnel --url http://localhost:8766
```

## 检查 HTTPS 配置

使用以下工具检查 SSL 配置：

```bash
# 检查 SSL 证书
openssl s_client -connect localhost:8766 -showcerts

# 在线 SSL 测试
# https://www.ssllabs.com/ssltest/
```

## 故障排除

### 问题 1：证书不受信任
- 确保已将证书添加到浏览器的受信任根证书颁发机构
- 重启浏览器

### 问题 2：WebSocket 连接失败
- 检查代理配置是否正确转发 Upgrade 头
- 确认 `proxy_read_timeout` 和 `proxy_send_timeout` 设置足够大

### 问题 3：推送通知不工作
- 确认使用 HTTPS（或 localhost）
- 检查 VAPID 公钥是否正确配置
- 查看浏览器控制台是否有错误

### 问题 4：证书过期
```bash
# 开发环境：重新生成证书
./scripts/generate-https-certs.sh

# 生产环境：使用 Let's Encrypt 续期
sudo certbot renew
```

## 安全提示

1. **永远不要**将私钥（`.key` 文件）提交到版本控制
2. 生产环境务必使用 Let's Encrypt 或其他 CA 的证书
3. 定期更新 SSL/TLS 协议和密码套件配置
4. 使用 HSTS (HTTP Strict Transport Security) 强制 HTTPS
5. 定期检查 SSL Labs 评分并优化

## 证书路径配置

确保环境变量正确配置：

```bash
# 开发环境（自签名证书）
export ZHINENG_BRIDGE_HTTPS_CERT_PATH="$HOME/.zhineng-bridge/certs/zhineng-bridge.crt"
export ZHINENG_BRIDGE_HTTPS_KEY_PATH="$HOME/.zhineng-bridge/certs/zhineng-bridge.key"

# 生产环境（Let's Encrypt）
export ZHINENG_BRIDGE_HTTPS_CERT_PATH="/etc/letsencrypt/live/zhineng-bridge.com/fullchain.pem"
export ZHINENG_BRIDGE_HTTPS_KEY_PATH="/etc/letsencrypt/live/zhineng-bridge.com/privkey.pem"
```

## 相关文档

- [推送通知开发计划](./PWA_DEVELOPMENT_PLAN_V2.md)
- [移动端测试指南](./MOBILE_TESTING_GUIDE.md)
- [VAPID 规范](https://datatracker.ietf.org/doc/html/rfc8292)
