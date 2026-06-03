# 智桥 Docker 部署指南

本指南介绍如何使用 Docker 和 Docker Compose 部署智桥（Zhineng-bridge）。

---

## 目录

- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [配置](#配置)
- [服务端点](#服务端点)
- [日志](#日志)
- [故障排除](#故障排除)
- [生产部署](#生产部署)

---

## 前置要求

- Docker 20.10+
- Docker Compose 2.0+

检查版本：

```bash
docker --version
docker-compose --version
```

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/guangda88/zhineng-bridge.git
cd zhineng-bridge
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件根据需要修改配置
```

### 3. 使用 Docker Compose 启动

```bash
docker-compose up -d
```

### 4. 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f zhineng-bridge
```

### 5. 停止服务

```bash
docker-compose down
```

---

## 配置

### 环境变量

通过 `.env` 文件或环境变量配置服务。

关键配置项：

```bash
# 服务器配置
ZHINENG_BRIDGE_HOST=0.0.0.0
ZHINENG_BRIDGE_PORT=8765
ZHINENG_BRIDGE_MAX_CONNECTIONS=100

# 日志配置
ZHINENG_BRIDGE_LOG_LEVEL=INFO
ZHINENG_BRIDGE_LOG_FORMAT=json

# 安全配置
ZHINENG_BRIDGE_SECURITY_ENABLE_AUTH=false
ZHINENG_BRIDGE_SECURITY_ENABLE_RATE_LIMIT=true
```

完整配置选项请参考 [`.env.example`](../.env.example)。

### 端口映射

默认端口映射：

| 容器端口 | 主机端口 | 服务 |
|-----------|----------|------|
| 8765 | 8765 | WebSocket Relay Server |
| 8000 | 8000 | HTTP Server (Health Check) |

修改 `docker-compose.yml` 中的 `ports` 配置来更改端口映射。

---

## 服务端点

启动后，可以访问以下端点：

### Web UI

```
http://localhost:8000/web/ui/index.html
```

### WebSocket

```
ws://localhost:8765
```

### 健康检查

```
http://localhost:8000/health
```

### 指标

```
http://localhost:8000/metrics
```

### 状态

```
http://localhost:8000/status
```

---

## 日志

### 查看日志

```bash
# 实时日志
docker-compose logs -f zhineng-bridge

# 最近 100 行
docker-compose logs --tail=100 zhineng-bridge
```

### 日志卷

日志存储在 Docker 卷中：

```bash
docker volume ls
# zhineng-bridge_zhineng-bridge-logs
```

查看日志文件：

```bash
docker exec -it zhineng-bridge ls -la /var/log/zhineng-bridge/
```

---

## 故障排除

### 容器无法启动

检查日志：

```bash
docker-compose logs zhineng-bridge
```

常见问题：

1. **端口已被占用**
   ```
   Error: bind: address already in use
   ```
   解决：修改 `docker-compose.yml` 中的端口映射

2. **权限问题**
   ```
   Permission denied
   ```
   解决：确保 Docker 有访问权限

### 服务健康检查失败

检查服务状态：

```bash
docker-compose ps
```

如果健康检查失败，检查：

```bash
# 测试健康检查端点
curl http://localhost:8000/health
```

### 查看容器内部

```bash
# 进入容器
docker exec -it zhineng-bridge bash

# 查看进程
ps aux

# 查看网络
netstat -tlnp
```

### 重启服务

```bash
# 重启单个服务
docker-compose restart zhineng-bridge

# 重启所有服务
docker-compose restart
```

---

## 生产部署

### 使用 HTTPS/WSS

要启用安全连接，需要：

1. **获取 SSL 证书**

   使用 Let's Encrypt（免费）或购买证书。

2. **配置环境变量**

   ```bash
   ZHINENG_BRIDGE_ENABLE_WSS=true
   ZHINENG_BRIDGE_CERT_FILE=/path/to/cert.pem
   ZHINENG_BRIDGE_KEY_FILE=/path/to/key.pem
   ```

3. **挂载证书**

   在 `docker-compose.yml` 中添加：

   ```yaml
   volumes:
     - /path/to/certs:/certs:ro
   ```

4. **更新环境变量**

   ```bash
   ZHINENG_BRIDGE_CERT_FILE=/certs/cert.pem
   ZHINENG_BRIDGE_KEY_FILE=/certs/key.pem
   ```

### 使用 Redis（可选）

对于生产环境，可以使用 Redis 作为消息队列。

取消注释 `docker-compose.yml` 中的 Redis 服务：

```yaml
redis:
  image: redis:7-alpine
  container_name: zhineng-bridge-redis
  ports:
    - "6379:6379"
  volumes:
    - redis-data:/data
  networks:
    - zhineng-bridge-net
  restart: unless-stopped
```

### 使用 PostgreSQL（可选）

对于生产数据库，使用 PostgreSQL。

取消注释 `docker-compose.yml` 中的 PostgreSQL 服务：

```yaml
postgres:
  image: postgres:15-alpine
  container_name: zhineng-bridge-postgres
  environment:
    - POSTGRES_DB=zhineng_bridge
    - POSTGRES_USER=zhineng
    - POSTGRES_PASSWORD=your_secure_password
  ports:
    - "5432:5432"
  volumes:
    - postgres-data:/var/lib/postgresql/data
  networks:
    - zhineng-bridge-net
  restart: unless-stopped
```

更新 `.env` 文件：

```bash
ZHINENG_BRIDGE_DB_ENABLE_SQLITE=false
ZHINENG_BRIDGE_DB_PG_HOST=postgres
ZHINENG_BRIDGE_DB_PG_PORT=5432
ZHINENG_BRIDGE_DB_PG_DATABASE=zhineng_bridge
ZHINENG_BRIDGE_DB_PG_USER=zhineng
ZHINENG_BRIDGE_DB_PG_PASSWORD=your_secure_password
```

### 使用 Prometheus 和 Grafana（可选）

对于监控，使用 Prometheus 和 Grafana。

取消注释 `docker-compose.yml` 中的相关服务。

访问 Grafana：`http://localhost:3000`
默认用户名：`admin`
默认密码：`admin`（首次登录后更改）

---

## Docker 命令参考

### 构建镜像

```bash
# 构建镜像
docker-compose build

# 重新构建（不使用缓存）
docker-compose build --no-cache
```

### 启动服务

```bash
# 前台启动
docker-compose up

# 后台启动
docker-compose up -d

# 启动特定服务
docker-compose up zhineng-bridge
```

### 停止服务

```bash
# 停止并删除容器
docker-compose down

# 停止并删除容器和卷
docker-compose down -v

# 停止但保留容器
docker-compose stop
```

### 更新服务

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

### 清理

```bash
# 清理停止的容器
docker container prune

# 清理未使用的镜像
docker image prune -a

# 清理未使用的卷
docker volume prune

# 清理所有
docker system prune -a --volumes
```

---

## 安全建议

1. **更改默认端口**
   - 修改端口映射以避免常见端口

2. **使用强密码**
   - 为 PostgreSQL 设置强密码

3. **启用认证**
   - 设置 `ZHINENG_BRIDGE_SECURITY_ENABLE_AUTH=true`

4. **启用 WSS**
   - 生产环境必须使用 TLS/SSL

5. **限制网络访问**
   - 使用防火墙规则限制访问

6. **定期更新**
   - 定期更新 Docker 镜像

7. **日志监控**
   - 监控日志以检测异常活动

---

## 性能优化

1. **增加资源限制**

   在 `docker-compose.yml` 中添加：

   ```yaml
   services:
     zhineng-bridge:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
           reservations:
             cpus: '1'
             memory: 1G
   ```

2. **使用多个实例**

   使用 Docker Swarm 或 Kubernetes 进行水平扩展。

3. **启用压缩**

   ```bash
   ZHINENG_BRIDGE_ENABLE_COMPRESSION=true
   ```

---

## 备份和恢复

### 备份

```bash
# 备份日志
docker run --rm \
  -v zhineng-bridge_zhineng-bridge-logs:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/logs-backup.tar.gz -C /data .

# 备份 PostgreSQL（如果使用）
docker exec zhineng-bridge-postgres \
  pg_dump -U zhineng zhineng_bridge > backup.sql
```

### 恢复

```bash
# 恢复日志
docker run --rm \
  -v zhineng-bridge_zhineng-bridge-logs:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/logs-backup.tar.gz -C /data

# 恢复 PostgreSQL（如果使用）
docker exec -i zhineng-bridge-postgres \
  psql -U zhineng zhineng_bridge < backup.sql
```

---

## 支持

- **文档**: [docs/](../docs/)
- **GitHub**: https://github.com/guangda88/zhineng-bridge
- **Issues**: https://github.com/guangda88/zhineng-bridge/issues

---

**最后更新**: 2026-03-25
