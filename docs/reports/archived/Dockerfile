FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY relay-server/ ./relay-server/
COPY phase1/ ./phase1/
COPY phase3/ ./phase3/
COPY phase4/ ./phase4/
COPY web/ ./web/
COPY optimization/ ./optimization/

# 创建非 root 用户和必要目录
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser \
    && mkdir -p /home/appuser/.zhineng-bridge/tmp \
    && chown -R appuser:appuser /app /home/appuser

# 暴露端口
EXPOSE 8000 8765

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV ZHINENG_BRIDGE_HOST=0.0.0.0
ENV ZHINENG_BRIDGE_PORT=8765

# 启动脚本
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 切换到非 root 用户
USER appuser

# 启动服务
ENTRYPOINT ["docker-entrypoint.sh"]
