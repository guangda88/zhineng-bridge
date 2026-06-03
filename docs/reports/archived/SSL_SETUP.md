# SSL/TLS 证书设置指南

本指南提供智桥 (Zhineng-bridge) 生产环境 SSL/TLS 证书的配置说明。

## 目录

1. [概述](#概述)
2. [使用 Let's Encrypt (推荐)](#使用-lets-encrypt-推荐)
3. [使用自签名证书](#使用自签名证书)
4. [使用商业证书](#使用商业证书)
5. [证书续期](#证书续期)
6. [故障排查](#故障排查)
7. [安全最佳实践](#安全最佳实践)

---

## 概述

### 为什么需要 SSL/TLS？

- **安全性**: 加密所有通信，防止中间人攻击
- **WebSocket Secure (WSS)**: 浏览器要求安全连接
- **信任**: 用户信任有 HTTPS 的网站
- **合规**: 许多行业要求加密通信
- **SEO**: 搜索引擎优先索引 HTTPS 网站

### 证书类型

| 类型 | 说明 | 适用场景 |
|------|------|---------|
| Let's Encrypt | 免费自动化证书 | 公网域名 |
| 自签名证书 | 自己生成的证书 | 开发测试 |
| 商业证书 | 付费 CA 签发 | 生产环境（可选） |

### 证书文件要求

智桥需要以下证书文件：

- **证书文件**: `nginx/ssl/cert.pem` - 包含服务器证书和中间证书
- **私钥文件**: `nginx/ssl/key.pem` - 服务器私钥

---

## 使用 Let's Encrypt (推荐)

Let's Encrypt 提供免费、自动化、开放的 SSL/TLS 证书。

### 前置要求

1. **域名**: 必须有公网可访问的域名
2. **DNS 解析**: 域名已解析到服务器 IP
3. **防火墙**: 80 和 443 端口开放
4. **权限**: 服务器有 sudo 权限

### 安装 Certbot

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install certbot
```

**CentOS/RHEL:**
```bash
sudo yum install epel-release
sudo yum install certbot
```

**macOS:**
```bash
brew install certbot
```

### 获取证书

#### 方法 1: Standalone 模式 (临时停止 Nginx)

```bash
# 停止 Nginx
docker-compose -f docker-compose.prod.yml stop nginx

# 获取证书
sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos

# 重新启动 Nginx
docker-compose -f docker-compose.prod.yml start nginx
```

#### 方法 2: Webroot 模式 (推荐，无需停止服务)

```bash
# 获取证书（使用 Nginx 的 webroot）
sudo certbot certonly --webroot \
  -w /var/www/certbot \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email your-email@example.com \
  --agree-tos

# 如果 /var/www/certbot 不存在，创建它
sudo mkdir -p /var/www/certbot
sudo chown -R www-data:www-data /var/www/certbot  # Ubuntu
# sudo chown -R nginx:nginx /var/www/certbot  # CentOS
```

#### 方法 3: DNS 验证 (支持通配符证书)

```bash
# 获取通配符证书
sudo certbot certonly --manual \
  -d "*.yourdomain.com" \
  -d "yourdomain.com" \
  --preferred-challenges dns \
  --email your-email@example.com \
  --agree-tos

# 按照提示添加 DNS TXT 记录
# 等待 DNS 传播后继续
```

### 安装证书到智桥

```bash
# 复制证书到项目目录
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /home/ai/zhibridge/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /home/ai/zhibridge/nginx/ssl/key.pem

# 设置正确的权限
sudo chmod 644 /home/ai/zhibridge/nginx/ssl/cert.pem
sudo chmod 600 /home/ai/zhibridge/nginx/ssl/key.pem

# 更新 Docker Compose 权限
sudo chown -R $USER:$USER /home/ai/zhibridge/nginx/ssl/
```

### 更新 Nginx 配置

编辑 `nginx/nginx.conf`，更新 `server_name`:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    # ... 其他配置
}
```

### 重启服务

```bash
# 重启 Nginx
docker-compose -f docker-compose.prod.yml restart nginx

# 验证证书
curl -I https://yourdomain.com
```

---

## 使用自签名证书

自签名证书适用于开发和测试环境，不适用于生产环境。

### 生成自签名证书

```bash
# 进入项目目录
cd /home/ai/zhibridge

# 创建 SSL 目录
mkdir -p nginx/ssl

# 生成自签名证书（有效期 365 天）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=ZhinengBridge/CN=localhost"

# 设置权限
chmod 644 nginx/ssl/cert.pem
chmod 600 nginx/ssl/key.pem
```

### 生成高级自签名证书

如果需要更详细的证书信息：

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=ZhinengBridge/OU=Development/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1"
```

### 更新环境变量

编辑 `.env.prod`:

```bash
# 启用 WSS
ZHINENG_BRIDGE_ENABLE_WSS=true
```

### 重启服务

```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### 浏览器警告

使用自签名证书时，浏览器会显示安全警告：

- **Chrome/Edge**: 点击"高级" → "继续访问"
- **Firefox**: 点击"高级" → "接受风险并继续"
- **Safari**: 点击"详细信息" → "访问此网站"

---

## 使用商业证书

如果使用商业 CA（如 DigiCert、Comodo、GlobalSign），按照 CA 提供的指南操作。

### 一般步骤

1. **生成 CSR (证书签名请求)**:
```bash
openssl req -new -newkey rsa:2048 -nodes \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/csr.pem \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=ZhinengBridge/CN=yourdomain.com"
```

2. **提交 CSR 到 CA**: 将 `nginx/ssl/csr.pem` 内容提交到 CA

3. **下载证书**: 下载 CA 签发的证书文件

4. **安装证书**:
```bash
# 证书文件
cp your-certificate.pem nginx/ssl/cert.pem

# 如果有中间证书，需要合并
cat your-certificate.pem intermediate-ca.pem > nginx/ssl/cert.pem

# 设置权限
chmod 644 nginx/ssl/cert.pem
chmod 600 nginx/ssl/key.pem
```

---

## 证书续期

### Let's Encrypt 自动续期

#### 使用 cron 定时任务

```bash
# 编辑 crontab
sudo crontab -e
```

添加以下行（每月1号凌晨3点检查续期）:

```cron
0 3 1 * * certbot renew --quiet --post-hook "cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /home/ai/zhibridge/nginx/ssl/cert.pem && cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /home/ai/zhibridge/nginx/ssl/key.pem && docker-compose -f /home/ai/zhibridge/docker-compose.prod.yml restart nginx"
```

#### 使用 systemd timer (推荐)

创建服务文件 `/etc/systemd/system/certbot-renew.service`:

```ini
[Unit]
Description=Certbot Renewal Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/certbot renew --quiet --post-hook "cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /home/ai/zhibridge/nginx/ssl/cert.pem && cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /home/ai/zhibridge/nginx/ssl/key.pem && docker-compose -f /home/ai/zhibridge/docker-compose.prod.yml restart nginx"
```

创建定时器文件 `/etc/systemd/system/certbot-renew.timer`:

```ini
[Unit]
Description=Certbot Renewal Timer

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

启用定时器:

```bash
sudo systemctl daemon-reload
sudo systemctl enable certbot-renew.timer
sudo systemctl start certbot-renew.timer
sudo systemctl status certbot-renew.timer
```

### 手动续期

```bash
# 测试续期
sudo certbot renew --dry-run

# 实际续期
sudo certbot renew

# 续期后重启 Nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### 自签名证书续期

```bash
# 生成新证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=ZhinengBridge/CN=localhost"

# 重启服务
docker-compose -f docker-compose.prod.yml restart nginx
```

---

## 故障排查

### 问题 1: 证书验证失败

**症状**: 浏览器显示"证书无效"或"证书不信任"

**解决方案**:
```bash
# 检查证书文件
openssl x509 -in nginx/ssl/cert.pem -text -noout

# 检查证书有效期
openssl x509 -in nginx/ssl/cert.pem -enddate -noout

# 检查证书和私钥是否匹配
openssl x509 -noout -modulus -in nginx/ssl/cert.pem | openssl md5
openssl rsa -noout -modulus -in nginx/ssl/key.pem | openssl md5
# 两个输出应该相同
```

### 问题 2: Nginx 启动失败

**症状**: Nginx 容器无法启动

**解决方案**:
```bash
# 查看日志
docker-compose logs nginx

# 测试配置
docker-compose -f docker-compose.prod.yml run --rm nginx nginx -t

# 检查文件权限
ls -la nginx/ssl/
# 应该是: cert.pem 644, key.pem 600
```

### 问题 3: WebSocket 连接失败

**症状**: WSS 连接无法建立

**解决方案**:
1. 检查 Nginx 配置中的 `proxy_set_header` 设置
2. 确认 `proxy_http_version 1.1` 已设置
3. 检查超时设置 (`proxy_read_timeout`, `proxy_send_timeout`)
4. 验证 SSL 证书链完整

### 问题 4: Let's Encrypt 验证失败

**症状**: certbot 验证失败

**解决方案**:
```bash
# 检查 DNS 解析
nslookup yourdomain.com
dig yourdomain.com

# 检查端口开放
sudo netstat -tlnp | grep -E ':(80|443)'

# 检查防火墙
sudo ufw status
sudo iptables -L -n

# 尝试从外部访问
curl http://yourdomain.com/.well-known/acme-challenge/test
```

### 问题 5: 证书过期

**症状**: 浏览器显示"证书已过期"

**解决方案**:
```bash
# 检查证书过期时间
openssl x509 -in nginx/ssl/cert.pem -enddate -noout

# 续期证书
sudo certbot renew
# 或重新生成自签名证书

# 重启服务
docker-compose -f docker-compose.prod.yml restart nginx
```

---

## 安全最佳实践

### 1. 保护私钥文件

```bash
# 确保私钥文件权限正确
chmod 600 nginx/ssl/key.pem

# 不要将私钥提交到 Git
echo "nginx/ssl/" >> .gitignore
echo "*.pem" >> .gitignore
echo "*.key" >> .gitignore
```

### 2. 使用强加密套件

Nginx 配置已包含现代加密套件:

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:...';
```

### 3. 启用 HSTS

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### 4. 定期更新证书

- Let's Encrypt 证书有效期 90 天
- 设置自动续期
- 定期检查证书状态

### 5. 监控证书过期

设置告警，在证书过期前通知:

```bash
# 检查脚本
#!/bin/bash
EXPIRY=$(openssl x509 -enddate -noout -in /path/to/cert.pem | cut -d= -f2)
EXPIRY_DATE=$(date -d "$EXPIRY" +%s)
CURRENT_DATE=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_DATE - $CURRENT_DATE) / 86400 ))

if [ $DAYS_LEFT -lt 30 ]; then
    echo "警告: 证书将在 $DAYS_LEFT 天后过期"
    # 发送通知邮件或其他告警
fi
```

### 6. 使用 OCSP Stapling

提高 SSL 握手性能:

```nginx
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /path/to/chain.pem;
```

---

## 证书检查工具

### 在线工具

- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/) - 全面的 SSL 评估
- [Qualys SSL Checker](https://www.sslshopper.com/ssl-checker.html) - 快速检查
- [DigiCert SSL Installation Checker](https://www.digicert.com/help/) - 诊断工具

### 命令行工具

```bash
# 检查 SSL 连接
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# 检查证书信息
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com | openssl x509 -noout -text

# 测试 TLS 版本
openssl s_client -connect yourdomain.com:443 -tls1_2
openssl s_client -connect yourdomain.com:443 -tls1_3

# 检查 OCSP
openssl ocsp -issuer chain.pem -cert cert.pem -url http://ocsp.example.com
```

---

## 参考

- [Let's Encrypt 文档](https://letsencrypt.org/docs/)
- [Nginx SSL 配置](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

---

## 获取帮助

如果遇到问题:

1. 查看 Nginx 日志: `docker-compose logs -f nginx`
2. 检查证书有效性
3. 查看 [故障排查](#故障排查) 部分
4. 参考 [官方文档](https://letsencrypt.org/docs/)
5. 在项目仓库提交 Issue

---

**最后更新**: 2026-03-25
**版本**: 1.0.0
