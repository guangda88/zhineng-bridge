# Nginx 反向代理配置

本目录包含智桥 (Zhineng-bridge) 的 Nginx 反向代理配置文件。

## 目录结构

```
nginx/
├── nginx.conf      # 主 Nginx 配置文件
├── ssl/            # SSL 证书目录 (需要手动放置证书)
│   ├── cert.pem    # SSL 证书文件
│   └── key.pem     # SSL 私钥文件
└── README.md       # 本文件
```

## 功能特性

### 1. WebSocket 代理支持
- 完整支持 WebSocket 升级
- 长连接超时配置 (3600秒)
- 专用 WebSocket 连接限制

### 2. SSL/TLS 终止
- 支持 TLS 1.2 和 TLS 1.3
- 现代加密套件
- OCSP Stapling
- HSTS 安全头

### 3. 速率限制
- 一般请求: 10 req/s (burst 20)
- WebSocket 连接: 5 conn/s (burst 10)
- 并发连接限制: 100 conn/IP

### 4. 安全头
- Strict-Transport-Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Content-Security-Policy
- Referrer-Policy

### 5. 性能优化
- Gzip 压缩
- Keep-alive 连接
- 缓冲区优化
- HTTP/2 支持

### 6. 日志记录
- 主访问日志 (`/var/log/nginx/access.log`)
- WebSocket 访问日志 (`/var/log/nginx/websocket_access.log`)
- Prometheus 访问日志 (`/var/log/nginx/prometheus_access.log`)
- Grafana 访问日志 (`/var/log/nginx/grafana_access.log`)
- 错误日志 (`/var/log/nginx/error.log`)

## 代理端点

| 端点 | 目标服务 | 说明 |
|------|---------|------|
| `/` | WebSocket:8765 | WebSocket 中继服务器 |
| `/health` | HTTP:8000 | 健康检查端点 |
| `/metrics` | HTTP:8000 | Prometheus 指标 |
| `/docs` | HTTP:8000 | Swagger API 文档 |
| `/oauth2` | HTTP:8000 | OAuth2 回调 |
| `/web/` | 本地文件 | Web UI 静态文件 |
| `/prometheus/` | Prometheus:9090 | Prometheus 仪表板 (可选) |
| `/grafana/` | Grafana:3000 | Grafana 仪表板 (可选) |

## SSL 证书配置

### 使用 Let's Encrypt (推荐)

1. 安装 certbot:
```bash
sudo apt-get update
sudo apt-get install certbot
```

2. 生成证书:
```bash
sudo certbot certonly --standalone -d your-domain.com
```

3. 复制证书到 ssl 目录:
```bash
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /home/ai/zhineng-bridge/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /home/ai/zhineng-bridge/nginx/ssl/key.pem
```

4. 设置正确的权限:
```bash
sudo chmod 644 /home/ai/zhineng-bridge/nginx/ssl/cert.pem
sudo chmod 600 /home/ai/zhineng-bridge/nginx/ssl/key.pem
```

5. 自动续期 (添加到 crontab):
```bash
sudo crontab -e
# 添加以下行 (每月1号凌晨3点检查续期)
0 3 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /home/ai/zhineng-bridge/nginx/ssl/cert.pem && cp /etc/letsencrypt/live/your-domain.com/privkey.pem /home/ai/zhineng-bridge/nginx/ssl/key.pem && docker-compose restart nginx
```

### 使用自签名证书 (仅用于测试)

生成自签名证书:
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /home/ai/zhineng-bridge/nginx/ssl/key.pem \
  -out /home/ai/zhineng-bridge/nginx/ssl/cert.pem \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=ZhinengBridge/CN=localhost"
```

## 配置自定义

### 修改服务器名称

编辑 `nginx.conf`，修改 `server_name`:
```nginx
server_name your-domain.com www.your-domain.com;
```

### 调整速率限制

修改限制区域:
```nginx
# 每秒请求数
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=20r/s;
# 并发连接数
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

# 在 location 中应用
limit_req zone=general_limit burst=30 nodelay;
limit_conn conn_limit 200;
```

### 启用 Prometheus 基本认证

1. 生成密码文件:
```bash
sudo apt-get install apache2-utils
sudo htpasswd -c /home/ai/zhineng-bridge/nginx/.htpasswd admin
```

2. 取消注释 nginx.conf 中的认证配置:
```nginx
location /prometheus/ {
    auth_basic "Prometheus Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    # ...
}
```

### 禁用 Grafana 代理

如果不需要通过 Nginx 代理 Grafana，注释掉相应的 location 块:
```nginx
# location /grafana/ {
#     ...
# }
```

## 测试配置

在启动前测试配置:
```bash
docker-compose -f docker-compose.prod.yml run --rm nginx nginx -t
```

## 查看日志

查看 Nginx 日志:
```bash
# 主访问日志
docker-compose logs -f nginx

# WebSocket 日志
docker-compose exec nginx tail -f /var/log/nginx/websocket_access.log

# 错误日志
docker-compose exec nginx tail -f /var/log/nginx/error.log
```

## 故障排查

### 1. WebSocket 连接失败

检查 Nginx 错误日志:
```bash
docker-compose exec nginx tail -f /var/log/nginx/error.log
```

常见问题:
- 检查 `proxy_set_header Upgrade` 和 `proxy_set_header Connection` 是否正确
- 确认超时时间足够长 (`proxy_read_timeout`, `proxy_send_timeout`)
- 验证后端服务是否正常运行

### 2. SSL 证书问题

检查证书文件:
```bash
docker-compose exec nginx ls -la /etc/nginx/ssl/
docker-compose exec nginx cat /etc/nginx/ssl/cert.pem
```

验证证书有效期:
```bash
openssl x509 -enddate -noout -in /home/ai/zhineng-bridge/nginx/ssl/cert.pem
```

### 3. 速率限制触发

如果遇到 503 错误，可能触发了速率限制:
- 查看限制区域统计: `docker-compose exec nginx cat /var/log/nginx/error.log | grep limit_req`
- 调整限制参数
- 增加 burst 值

### 4. 502 Bad Gateway

检查后端服务状态:
```bash
docker-compose ps
docker-compose logs zhineng-bridge
```

## 性能优化建议

1. **调整 worker_processes**: 通常设置为 `auto` 让 Nginx 自动选择
2. **调整 worker_connections**: 根据预期并发数调整 (默认 2048)
3. **启用 HTTP/2**: 已启用，提高页面加载速度
4. **使用 CDN**: 对于静态资源，考虑使用 CDN
5. **启用缓存**: 对 API 响应考虑添加缓存层

## 安全建议

1. **定期更新证书**: 设置自动续期
2. **使用强加密套件**: 配置已使用现代加密套件
3. **限制访问**: 对管理端点添加 IP 白名单或认证
4. **监控日志**: 定期检查访问日志，发现异常活动
5. **隐藏 Nginx 版本**: 已配置 `server_tokens off`
6. **使用 WAF**: 考虑添加 Web 应用防火墙

## 参考资源

- [Nginx 官方文档](https://nginx.org/en/docs/)
- [WebSocket 代理指南](https://nginx.org/en/docs/http/websocket.html)
- [SSL/TLS 配置最佳实践](https://wiki.mozilla.org/Security/Server_Side_TLS)
- [Nginx 性能调优](https://www.nginx.com/blog/tuning-nginx/)

---

**注意**: 生产环境部署前，请务必:
1. 使用有效的 SSL 证书
2. 根据实际需求调整配置参数
3. 测试所有端点是否正常工作
4. 设置监控和告警
5. 准备备份和恢复方案
