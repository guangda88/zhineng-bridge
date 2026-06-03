# 公网访问部署指南

**日期：** 2026-03-29
**目标：** 实现智桥(zhineng-bridge)的公网访问能力

---

## 📋 概述

本指南提供两种方案实现公网访问：
1. **方案A：内网穿透（frp）** - 快速，适合开发测试
2. **方案B：云服务器部署** - 稳定，适合生产环境

---

## 🚀 方案A：内网穿透（frp）

### 1. 准备工作

#### 需要的资源：
- **frp服务器**：需要有公网IP的服务器或购买frp服务
- **域名**（可选）：如果需要HTTPS

#### 已完成的工作：
✅ SSL证书已生成（自签名证书，用于测试）
✅ frp客户端配置已创建（`config/frpc.ini`）
✅ 本地nginx配置已创建（`nginx/nginx-local.conf`）
✅ 前端已支持wss://自动检测

---

### 2. 安装frp客户端

#### Linux/macOS:

```bash
# 下载frp客户端
cd /tmp
wget https://github.com/fatedier/frp/releases/download/v0.52.3/frp_0.52.3_linux_amd64.tar.gz
tar -xzf frp_0.52.3_linux_amd64.tar.gz
cd frp_0.52.3_linux_amd64

# 复制到系统路径
sudo cp frpc /usr/local/bin/
sudo chmod +x /usr/local/bin/frpc

# 验证安装
frpc --version
```

#### Windows:
```bash
# 下载Windows版本
https://github.com/fatedier/frp/releases/download/v0.52.3/frp_0.52.3_windows_amd64.zip

# 解压后使用frpc.exe
```

---

### 3. 配置frp客户端

编辑 `config/frpc.ini`：

```ini
[common]
# 服务器地址（需要用户提供）
server_addr = your_frp_server.com
server_port = 7000

# 认证令牌（需要用户提供）
token = your_frp_token

# 客户端ID
user = zhineng-bridge

[zhineng_bridge_http]
type = tcp
local_ip = 127.0.0.1
local_port = 8080
remote_port = 8080

[zhineng_bridge_https]
type = tcp
local_ip = 127.0.0.1
local_port = 443
remote_port = 443

[zhineng_bridge_websocket]
type = tcp
local_ip = 127.0.0.1
local_port = 8765
remote_port = 8765
```

---

### 4. 启动服务

#### 启动智桥服务：

```bash
# 终端1：启动relay server
cd /home/ai/zhibridge/relay-server
python3 start_server.py

# 终端2：启动session manager
cd /home/ai/zhibridge/phase1/session_manager
python3 start_manager.py

# 终端3：启动nginx（使用本地配置）
docker run -d \
  --name zhineng-nginx \
  -p 80:80 \
  -p 443:443 \
  -v /home/ai/zhibridge/nginx/nginx-local.conf:/etc/nginx/nginx.conf:ro \
  -v /home/ai/zhibridge/nginx/ssl:/etc/nginx/ssl:ro \
  -v /home/ai/zhibridge/web/ui:/app/web:ro \
  nginx:latest

# 终端4：启动frp客户端
frpc -c /home/ai/zhibridge/config/frpc.ini
```

#### 使用脚本一键启动：

```bash
# 创建启动脚本
cat > /home/ai/zhibridge/start_frpd.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 启动智桥服务（内网穿透模式）..."

# 启动relay server
echo "📡 启动relay server..."
cd /home/ai/zhibridge/relay-server
python3 start_server.py > /tmp/relay_server.log 2>&1 &
RELAY_PID=$!
echo "✅ Relay server PID: $RELAY_PID"

# 启动session manager
echo "🎛️  启动session manager..."
cd /home/ai/zhibridge/phase1/session_manager
python3 start_manager.py > /tmp/session_manager.log 2>&1 &
MGR_PID=$!
echo "✅ Session manager PID: $MGR_PID"

# 等待服务启动
sleep 3

# 启动nginx
echo "🌐 启动nginx..."
docker run -d \
  --name zhineng-nginx \
  --restart unless-stopped \
  -p 80:80 \
  -p 443:443 \
  -v /home/ai/zhibridge/nginx/nginx-local.conf:/etc/nginx/nginx.conf:ro \
  -v /home/ai/zhibridge/nginx/ssl:/etc/nginx/ssl:ro \
  -v /home/ai/zhibridge/web/ui:/app/web:ro \
  nginx:latest

# 启动frp客户端
echo "🔌 启动frp客户端..."
frpc -c /home/ai/zhibridge/config/frpc.ini > /tmp/frpc.log 2>&1 &
FRPC_PID=$!
echo "✅ FRP client PID: $FRPC_PID"

echo ""
echo "✅ 所有服务已启动！"
echo ""
echo "访问地址："
echo "  本地:   http://10.113.22.99:8080/web/ui/index.html"
echo "  公网:   http://your_frp_server.com:8080/web/ui/index.html"
echo "  HTTPS:  https://your_frp_server.com:443/web/ui/index.html"
echo ""
echo "日志查看："
echo "  Relay server: tail -f /tmp/relay_server.log"
echo "  Session mgr:  tail -f /tmp/session_manager.log"
echo "  FRP client:   tail -f /tmp/frpc.log"
echo ""

# 保存PID
echo $RELAY_PID > /tmp/relay_server.pid
echo $MGR_PID > /tmp/session_manager.pid
echo $FRPC_PID > /tmp/frpc.pid

EOF

chmod +x /home/ai/zhibridge/start_frpd.sh
```

---

### 5. 测试公网访问

```bash
# 在本地测试
curl https://10.113.22.99/health

# 在公网测试
curl https://your_frp_server.com/health

# 在手机浏览器测试
# 打开: https://your_frp_server.com:443/web/ui/index.html
```

---

### 6. 常见问题

**问题1：frp连接失败**
```bash
# 检查frp日志
tail -f /tmp/frpc.log

# 检查服务器地址和端口是否正确
# 检查token是否正确
# 检查防火墙是否允许
```

**问题2：HTTPS证书警告**
- 自签名证书会显示警告，这是正常的
- 浏览器选择"继续访问"
- 生产环境使用Let's Encrypt证书

**问题3：WebSocket连接失败**
```bash
# 检查nginx是否正确代理WebSocket
# 检查proxy_set_header Upgrade是否设置
# 查看nginx日志
docker logs zhineng-nginx
```

---

## ☁️ 方案B：云服务器部署

### 1. 购买云服务器

推荐配置：
- **CPU**: 2核
- **内存**: 4GB
- **带宽**: 5Mbps以上
- **系统**: Ubuntu 22.04 LTS

推荐服务商：
- 阿里云: https://www.aliyun.com
- 腾讯云: https://cloud.tencent.com
- AWS: https://aws.amazon.com/ec2

---

### 2. 安装依赖

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装Python 3
sudo apt-get install -y python3 python3-pip python3-venv

# 安装Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装Nginx
sudo apt-get install -y nginx certbot python3-certbot-nginx

# 安装项目依赖
cd /opt
sudo git clone https://github.com/guangda88/zhineng-bridge.git
cd zhineng-bridge
sudo pip3 install -r requirements.txt
```

---

### 3. 配置域名

```bash
# 购买域名并解析到云服务器IP
# 例如: zhineng-bridge.example.com -> 1.2.3.4

# 验证DNS解析
dig +short zhineng-bridge.example.com
```

---

### 4. 获取SSL证书

```bash
# 使用Let's Encrypt获取免费证书
sudo certbot --nginx -d zhineng-bridge.example.com

# 证书会自动配置到nginx
# 位置: /etc/letsencrypt/live/zhineng-bridge.example.com/
```

---

### 5. 配置Nginx

编辑 `/etc/nginx/sites-available/zhineng-bridge`：

```nginx
server {
    listen 80;
    server_name zhineng-bridge.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name zhineng-bridge.example.com;

    ssl_certificate /etc/letsencrypt/live/zhineng-bridge.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/zhineng-bridge.example.com/privkey.pem;

    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # WebSocket代理
    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }

    # HTTP服务
    location /health {
        proxy_pass http://127.0.0.1:8080;
    }

    # 静态文件
    location /web/ {
        alias /opt/zhineng-bridge/web/ui/;
        index index.html;
        try_files $uri $uri/ /web/index.html;
    }
}

# 启用配置
sudo ln -s /etc/nginx/sites-available/zhineng-bridge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

### 6. 启动服务

```bash
# 启动relay server
cd /opt/zhineng-bridge/relay-server
nohup python3 start_server.py > /var/log/relay_server.log 2>&1 &

# 启动session manager
cd /opt/zhineng-bridge/phase1/session_manager
nohup python3 start_manager.py > /var/log/session_manager.log 2>&1 &

# 检查服务
ps aux | grep python3
```

---

### 7. 配置systemd服务

创建 `/etc/systemd/system/zhineng-bridge.service`：

```ini
[Unit]
Description=Zhineng Bridge AI Tool Connector
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/zhineng-bridge
ExecStart=/usr/bin/python3 /opt/zhineng-bridge/relay-server/start_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable zhineng-bridge
sudo systemctl start zhineng-bridge
sudo systemctl status zhineng-bridge
```

---

### 8. 设置自动续期证书

```bash
# Certbot会自动设置续期任务
# 验证续期配置
sudo certbot renew --dry-run

# 查看定时任务
sudo systemctl list-timers | grep certbot
```

---

## 🔒 安全建议

### 1. 配置防火墙

```bash
# UFW防火墙
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. 启用认证

编辑 `/home/ai/zhibridge/.env`：

```bash
ZHINENG_BRIDGE_SECURITY_ENABLE_AUTH=true
ZHINENG_BRIDGE_SECURITY_SECRET_KEY=your_secret_key_here
```

### 3. 配置速率限制

已在nginx配置中启用，可根据需要调整：

```nginx
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=websocket_limit:10m rate=5r/s;
```

### 4. 日志监控

```bash
# 查看访问日志
sudo tail -f /var/log/nginx/access.log

# 查看错误日志
sudo tail -f /var/log/nginx/error.log

# 设置日志轮转
sudo logrotate /etc/logrotate.d/nginx
```

---

## 📊 性能优化

### 1. 调整系统参数

编辑 `/etc/sysctl.conf`：

```bash
# 网络优化
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30

# 应用配置
sudo sysctl -p
```

### 2. 调整Nginx配置

```nginx
worker_processes auto;
worker_connections 4096;
keepalive_timeout 65;
client_max_body_size 20M;
```

### 3. 启用缓存

```nginx
# 静态资源缓存
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## 📱 移动端测试

### iOS Safari:

1. 访问 `https://zhineng-bridge.example.com/web/ui/index.html`
2. 点击分享 → "添加到主屏幕"
3. 测试离线访问
4. 测试推送通知
5. 测试WebSocket连接

### Android Chrome:

1. 访问 `https://zhineng-bridge.example.com/web/ui/index.html`
2. 菜单 → "安装应用"或"添加到主屏幕"
3. 测试PWA功能
4. 测试后台运行
5. 测试推送通知

---

## 📝 部署检查清单

### 开发环境（内网穿透）：
- [ ] frp服务器已配置
- [ ] frpc已安装
- [ ] config/frpc.ini已配置
- [ ] SSL证书已生成
- [ ] nginx已启动
- [ ] relay server已启动
- [ ] session manager已启动
- [ ] frpc已启动
- [ ] 公网访问测试通过
- [ ] WebSocket连接测试通过

### 生产环境（云服务器）：
- [ ] 云服务器已购买
- [ ] 域名已解析
- [ ] Docker已安装
- [ ] Nginx已安装
- [ ] SSL证书已获取
- [ ] Nginx已配置
- [ ] 服务已启动
- [ ] systemd服务已配置
- [ ] 防火墙已配置
- [ ] 速率限制已配置
- [ ] 日志监控已设置
- [ ] 性能优化已完成
- [ ] 备份策略已制定
- [ ] 监控告警已配置

---

## 🆘 故障排查

### 查看日志

```bash
# 服务日志
tail -f /var/log/relay_server.log
tail -f /var/log/session_manager.log

# Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 系统日志
sudo journalctl -u zhineng-bridge -f
```

### 常见问题

**Q: HTTPS证书过期？**
```bash
# 手动续期
sudo certbot renew
sudo systemctl reload nginx
```

**Q: WebSocket连接频繁断开？**
```bash
# 检查proxy_read_timeout
# 检查心跳机制
# 检查防火墙设置
```

**Q: 推送通知不工作？**
```bash
# 检查VAPID密钥配置
# 检查Service Worker注册
# 检查浏览器权限
```

---

## 📚 参考资源

- [frp官方文档](https://github.com/fatedier/frp)
- [Nginx WebSocket代理](https://nginx.org/en/docs/http/websocket.html)
- [Let's Encrypt](https://letsencrypt.org/)
- [PWA最佳实践](https://web.dev/progressive-web-apps/)

---

**最后更新：** 2026-03-29
**维护者：** Crush AI Assistant
