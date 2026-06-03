# 部署指南

## 本地开发

```bash
# 1. 安装依赖
pip install websockets aiohttp structlog

# 2. 启动 WebSocket 中继服务器
cd relay-server
python3 start_server.py

# 3. 启动会话管理器
cd phase1/session_manager
python3 start_manager.py

# 4. 访问 Web UI
# http://localhost:8000/web/ui/index.html
```

## Docker 部署

```bash
# 构建镜像
docker build -t zhineng-bridge:latest .

# 运行
docker run -d \
  -p 8765:8765 \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -e SECRET_KEY=your-secret-key \
  zhineng-bridge:latest
```

## Kubernetes 部署

项目包含完整的 K8s 清单（`k8s/` 目录）：

```bash
# 按顺序应用
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

### 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `WS_PORT` | 8765 | WebSocket 端口 |
| `HTTP_PORT` | 8080 | HTTP API 端口 |
| `DB_PATH` | data/zhineng.db | SQLite 数据库路径 |
| `SECRET_KEY` | — | JWT 签名密钥（生产环境必须设置） |
| `LOG_LEVEL` | INFO | 日志级别 |

### HPA 自动扩缩容

默认配置：
- 最小副本：2
- 最大副本：10
- CPU 阈值：70%
- 内存阈值：80%

## 部署脚本

```bash
# 部署
./scripts/deploy.sh

# 回滚到上一版本
./scripts/deploy.sh -r
```

## 监控

### 健康检查

```bash
curl http://localhost:8080/health
```

### 日志

使用 structlog 结构化日志，支持 JSON 输出。

### 性能监控

`phase4/monitoring/` 提供性能仪表板，监控：
- 页面加载时间
- WebSocket 延迟
- 内存使用
- FPS
- 会话创建耗时

## 备份

```bash
# 备份数据库
cp data/zhineng.db backups/zhineng-$(date +%Y%m%d).db
```

## 安全注意事项

1. 生产环境必须设置 `SECRET_KEY`
2. 启用 HTTPS（通过 Ingress 或反向代理）
3. 定期更新依赖
4. 使用防火墙限制端口访问
5. 启用 2FA 保护管理员账户
