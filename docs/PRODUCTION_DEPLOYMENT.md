# 智桥 (Zhineng-bridge) 生产环境部署指南

本指南提供智桥 (Zhineng-bridge) 在生产环境中完整部署的详细说明。

## 目录

1. [概述](#概述)
2. [前置要求](#前置要求)
3. [部署准备](#部署准备)
4. [部署步骤](#部署步骤)
5. [配置说明](#配置说明)
6. [监控和维护](#监控和维护)
7. [故障排查](#故障排查)
8. [性能优化](#性能优化)
9. [安全加固](#安全加固)
10. [备份和恢复](#备份和恢复)

---

## 概述

### 系统架构

智桥生产环境采用微服务架构，包含以下组件：

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (443/80)                        │
│                   反向代理 + SSL 终止                         │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────┬────────────┐
        │            │            │            │            │
┌───────▼──────┐ ┌───▼────┐ ┌────▼────┐ ┌────▼────┐ ┌─────▼─────┐
│    Main App   │ │Postgres│ │  Redis  │ │Prometheus│ │  Grafana  │
│  (8765/8000)  │ │(5432)  │ │ (6379)  │ │ (9090)   │ │  (3000)   │
└──────────────┘ └────────┘ └─────────┘ └─────────┘ └───────────┘
```

### 组件说明

| 组件 | 端口 | 说明 |
|------|------|------|
| Nginx | 80, 443 | 反向代理、SSL 终止、负载均衡 |
| Main App | 8000, 8765 | HTTP 服务器和 WebSocket 中继 |
| PostgreSQL | 5432 | 主数据库 |
| Redis | 6379 | 缓存和会话存储 |
| Prometheus | 9090 | 指标收集和存储 |
| Grafana | 3000 | 可视化和监控仪表板 |

### 资源需求

**最小配置**:
- CPU: 4 核
- 内存: 8GB
- 磁盘: 50GB

**推荐配置**:
- CPU: 8 核
- 内存: 16GB
- 磁盘: 100GB

**高可用配置**:
- CPU: 16 核
- 内存: 32GB
- 磁盘: 200GB
- 多服务器部署

---

## 前置要求

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 7+, Debian 10+)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.8+ (用于管理脚本)

### 网络要求

- 公网 IP 地址
- 域名 (推荐，用于 SSL 证书)
- 防火墙开放端口: 80, 443
- DNS 解析到服务器 IP

### 权限要求

- sudo 权限 (用于安装软件和配置系统)
- Docker 用户组访问权限

---

## 部署准备

### 1. 系统准备

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装必要工具
sudo apt-get install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    unzip \
    software-properties-common
```

### 2. 安装 Docker

**Ubuntu/Debian:**
```bash
# 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 仓库
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加当前用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker
```

**CentOS/RHEL:**
```bash
# 添加 Docker 仓库
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加当前用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker
```

### 3. 安装 Docker Compose

```bash
# 下载 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 添加执行权限
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

### 4. 配置防火墙

**UFW (Ubuntu/Debian):**
```bash
# 允许 SSH
sudo ufw allow 22/tcp

# 允许 HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

**firewalld (CentOS/RHEL):**
```bash
# 允许 SSH
sudo firewall-cmd --permanent --add-service=ssh

# 允许 HTTP/HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# 重载配置
sudo firewall-cmd --reload

# 查看状态
sudo firewall-cmd --list-all
```

### 5. 克隆项目

```bash
# 克隆仓库
git clone https://github.com/guangda88/zhineng-bridge.git
cd zhineng-bridge

# 或者从本地上传
# scp -r zhineng-bridge user@server:/home/ai/
```

---

## 部署步骤

### 步骤 1: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env.prod

# 编辑环境变量
vim .env.prod
```

**必须修改的变量**:
```bash
# 生成随机密钥 (至少 32 字符)
ZHINENG_BRIDGE_SECURITY_SECRET_KEY=$(openssl rand -hex 32)

# 生成数据库密码
POSTGRES_PASSWORD=$(openssl rand -hex 16)

# 生成 Redis 密码
REDIS_PASSWORD=$(openssl rand -hex 16)

# 生成 Grafana 密码
GRAFANA_ADMIN_PASSWORD=$(openssl rand -hex 16)

# 根据需要修改其他配置
GRAFANA_ROOT_URL=https://yourdomain.com
```

### 步骤 2: 配置 SSL 证书

参考 [SSL 证书设置指南](SSL_SETUP.md) 配置证书。

**快速配置 (Let's Encrypt)**:
```bash
# 停止 Nginx
docker-compose -f docker-compose.prod.yml stop nginx

# 获取证书
sudo certbot certonly --standalone \
  -d yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos

# 复制证书
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem

# 设置权限
chmod 644 nginx/ssl/cert.pem
chmod 600 nginx/ssl/key.pem

# 更新 Nginx 配置中的 server_name
vim nginx/nginx.conf

# 启用 WSS
sed -i 's/ZHINENG_BRIDGE_ENABLE_WSS=false/ZHINENG_BRIDGE_ENABLE_WSS=true/' .env.prod
```

### 步骤 3: 创建必要目录

```bash
# 创建备份目录
mkdir -p backups

# 创建 SSL 目录
mkdir -p nginx/ssl

# 创建日志目录
mkdir -p logs
```

### 步骤 4: 运行部署脚本

```bash
# 进入项目目录
cd /home/ai/zhineng-bridge

# 给脚本添加执行权限
chmod +x scripts/*.sh

# 运行部署脚本
./scripts/deploy.sh
```

部署脚本会自动完成以下操作:
1. 检查系统环境和依赖
2. 验证配置文件
3. 拉取 Docker 镜像
4. 构建应用镜像
5. 启动所有服务
6. 等待服务就绪
7. 显示部署信息

### 步骤 5: 验证部署

```bash
# 运行验证脚本
./scripts/verify_deployment.sh

# 手动检查服务状态
docker-compose -f docker-compose.prod.yml ps

# 检查日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 步骤 6: 配置自动启动

**使用 systemd**:
```bash
# 创建服务文件
sudo vim /etc/systemd/system/zhineng-bridge.service
```

内容:
```ini
[Unit]
Description=Zhineng Bridge Production
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ai/zhineng-bridge
ExecStart=/usr/local/bin/docker-compose -f /home/ai/zhineng-bridge/docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f /home/ai/zhineng-bridge/docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable zhineng-bridge.service
sudo systemctl start zhineng-bridge.service
sudo systemctl status zhineng-bridge.service
```

---

## 配置说明

### 环境变量配置

详细的环境变量说明请查看 `.env.prod` 文件中的注释。

**关键配置项**:

| 变量 | 说明 | 推荐值 |
|------|------|--------|
| `ZHINENG_BRIDGE_MAX_CONNECTIONS` | 最大并发连接数 | 500 |
| `ZHINENG_BRIDGE_SESSION_TIMEOUT` | 会话超时时间 (秒) | 7200 |
| `ZHINENG_BRIDGE_LOG_LEVEL` | 日志级别 | INFO |
| `ZHINENG_BRIDGE_SECURITY_ENABLE_AUTH` | 启用认证 | true |
| `ZHINENG_BRIDGE_SECURITY_ENABLE_RATE_LIMIT` | 启用速率限制 | true |

### Nginx 配置

Nginx 配置文件位于 `nginx/nginx.conf`。

**常用配置调整**:

1. **修改服务器名称**:
```nginx
server_name yourdomain.com www.yourdomain.com;
```

2. **调整速率限制**:
```nginx
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=20r/s;
limit_conn conn_limit 200;
```

3. **启用 Prometheus 访问**:
取消注释 Prometheus 代理块，并根据需要添加认证。

### Docker Compose 配置

生产环境配置文件为 `docker-compose.prod.yml`。

**资源限制调整**:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
    reservations:
      cpus: '2'
      memory: 2G
```

---

## 监控和维护

### Prometheus 指标

访问 Prometheus: `http://yourdomain.com/prometheus/`

**关键指标**:
- `zhineng_bridge_active_connections` - 活跃连接数
- `zhineng_bridge_total_sessions` - 总会话数
- `zhineng_bridge_request_duration` - 请求延迟
- `zhineng_bridge_error_count` - 错误计数

### Grafana 仪表板

访问 Grafana: `http://yourdomain.com/grafana/`

**首次登录**:
- 用户名: `admin`
- 密码: 查看 `.env.prod` 中的 `GRAFANA_ADMIN_PASSWORD`

**配置数据源**:
1. 进入 Configuration → Data Sources
2. 添加 Prometheus
3. URL: `http://prometheus:9090`

### 日志管理

**查看日志**:
```bash
# 所有服务
docker-compose -f docker-compose.prod.yml logs -f

# 特定服务
docker-compose -f docker-compose.prod.yml logs -f zhineng-bridge
docker-compose -f docker-compose.prod.yml logs -f postgres
docker-compose -f docker-compose.prod.yml logs -f nginx
```

**日志轮转**:
Docker 默认会轮转日志。如需自定义，创建 `/etc/docker/daemon.json`:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### 定期备份

**设置自动备份**:
```bash
# 编辑 crontab
crontab -e
```

添加以下行（每天凌晨 2 点备份）:
```cron
0 2 * * * /home/ai/zhineng-bridge/scripts/backup.sh -t full -k 7
```

---

## 故障排查

### 服务无法启动

**症状**: `docker-compose ps` 显示服务未运行

**解决方案**:
```bash
# 查看日志
docker-compose -f docker-compose.prod.yml logs [service-name]

# 检查配置
docker-compose -f docker-compose.prod.yml config

# 重新构建
docker-compose -f docker-compose.prod.yml build --no-cache [service-name]

# 重启服务
docker-compose -f docker-compose.prod.yml restart [service-name]
```

### 数据库连接失败

**症状**: 应用日志显示数据库连接错误

**解决方案**:
```bash
# 检查 PostgreSQL 状态
docker-compose -f docker-compose.prod.yml ps postgres
docker-compose -f docker-compose.prod.yml logs postgres

# 进入数据库容器
docker-compose -f docker-compose.prod.yml exec postgres psql -U zhineng -d zhineng_bridge

# 检查网络
docker-compose -f docker-compose.prod.yml exec zhineng-bridge ping postgres
```

### WebSocket 连接失败

**症状**: 浏览器无法建立 WSS 连接

**解决方案**:
```bash
# 检查 Nginx 配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# 检查 WebSocket 端口
netstat -tlnp | grep 8765

# 查看 Nginx 日志
docker-compose -f docker-compose.prod.yml logs nginx

# 测试连接
wscat -c ws://localhost:8765
```

### 性能问题

**症状**: 响应缓慢或高 CPU/内存使用

**解决方案**:
```bash
# 查看资源使用
docker stats

# 查看进程
docker-compose -f docker-compose.prod.yml top

# 检查数据库性能
docker-compose -f docker-compose.prod.yml exec postgres psql -U zhineng -d zhineng_bridge -c "SELECT * FROM pg_stat_activity;"

# 查看 Prometheus 指标
curl http://localhost:9090/metrics
```

### SSL 证书问题

参考 [SSL 证书设置指南](SSL_SETUP.md#故障排查)。

---

## 性能优化

### 应用层面优化

1. **调整连接池大小**:
```bash
# 在 .env.prod 中调整
ZHINENG_BRIDGE_MAX_CONNECTIONS=1000
```

2. **启用缓存**:
```bash
# Redis 已启用，确保配置正确
REDIS_PASSWORD=your-secure-password
```

3. **优化日志级别**:
```bash
# 生产环境使用 INFO 或 WARNING
ZHINENG_BRIDGE_LOG_LEVEL=WARNING
```

### 数据库优化

1. **调整 PostgreSQL 配置**:
```yaml
# 在 docker-compose.prod.yml 中添加
postgres:
  command: postgres -c max_connections=200 -c shared_buffers=256MB -c effective_cache_size=1GB
```

2. **定期清理**:
```bash
# 进入数据库
docker-compose -f docker-compose.prod.yml exec postgres psql -U zhineng -d zhineng_bridge

# 清理过期数据
DELETE FROM tokens WHERE expires_at < NOW();
VACUUM ANALYZE;
```

### Nginx 优化

1. **调整 worker 进程**:
```nginx
worker_processes auto;
worker_connections 4096;
```

2. **启用缓存**:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g;
```

### 系统层面优化

```bash
# 调整文件描述符限制
sudo vim /etc/security/limits.conf
# 添加:
* soft nofile 65535
* hard nofile 65535

# 调整内核参数
sudo vim /etc/sysctl.conf
# 添加:
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
```

---

## 安全加固

### 1. 网络安全

- 使用防火墙限制访问
- 仅开放必要的端口
- 使用 fail2ban 防止暴力破解

### 2. 应用安全

- 保持 Docker 镜像更新
- 定期更新依赖包
- 使用强密码和密钥

### 3. 数据安全

- 启用数据库加密
- 定期备份数据
- 限制数据库访问

### 4. 监控告警

设置 Prometheus 告警规则:

```yaml
groups:
  - name: zhineng_bridge_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(zhineng_bridge_error_count[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
```

---

## 备份和恢复

### 自动备份

使用提供的备份脚本:

```bash
# 完整备份
./scripts/backup.sh -t full -k 7

# 仅备份数据库
./scripts/backup.sh -t db

# 仅备份 Redis
./scripts/backup.sh -t redis
```

### 手动备份

**备份数据库**:
```bash
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U zhineng zhineng_bridge > backup.sql
```

**备份 Redis**:
```bash
docker-compose -f docker-compose.prod.yml exec -T redis redis-cli --raw SAVE
docker-compose -f docker-compose.prod.yml cp zhineng-bridge-redis-prod:/data/dump.rdb ./redis_backup.rdb
```

### 恢复备份

使用提供的恢复脚本:

```bash
# 恢复完整备份
./scripts/restore.sh backups/full_backup_20260301_120000.tar.gz

# 恢复数据库
./scripts/restore.sh -t db backups/db/zhineng_bridge_20260301.sql.gz
```

**手动恢复**:
```bash
# 恢复数据库
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U zhineng zhineng_bridge < backup.sql

# 恢复 Redis
docker-compose -f docker-compose.prod.yml stop redis
docker-compose -f docker-compose.prod.yml cp redis_backup.rdb zhineng-bridge-redis-prod:/data/dump.rdb
docker-compose -f docker-compose.prod.yml start redis
```

---

## 常见问题

### Q1: 如何更新应用？

```bash
# 拉取最新代码
git pull

# 运行更新脚本
./scripts/update.sh

# 或手动更新
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Q2: 如何增加存储空间？

```bash
# 停止服务
docker-compose -f docker-compose.prod.yml down

# 扩展 Docker volume (需要 Docker 插件)
# 或直接修改 docker-compose.prod.yml 中的 volume 配置

# 重启服务
docker-compose -f docker-compose.prod.yml up -d
```

### Q3: 如何查看性能指标？

访问 Grafana 仪表板: `http://yourdomain.com/grafana/`

或直接查询 Prometheus: `http://yourdomain.com/prometheus/`

### Q4: 如何配置域名？

1. 在 Nginx 配置中设置 `server_name`
2. 配置 DNS 解析
3. 获取 SSL 证书
4. 重启 Nginx

---

## 联系支持

如需帮助:

- 查看项目文档: [README.md](../README.md)
- 查看API文档: [API.md](API.md)
- 提交 Issue: [GitHub Issues](https://github.com/guangda88/zhineng-bridge/issues)
- 查看日志: `docker-compose logs -f`

---

**最后更新**: 2026-03-25
**版本**: 1.0.0
