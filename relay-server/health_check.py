#!/usr/bin/env python3
"""
HTTP 健康检查服务器
提供健康检查端点和静态文件服务
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import sys
import socket
import psutil
import mimetypes
from pathlib import Path
from datetime import datetime

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))
session_manager_path = Path(__file__).parent.parent / "phase1" / "session_manager"
sys.path.insert(0, str(session_manager_path))

from config import settings
from rate_limit import rate_limiter
from metrics import get_metrics, start_metrics_updater
from logger import get_logger
from file_api import FileAPI
from push_service import PushService

logger = get_logger(__name__)

# 初始化 PWA 服务
file_api = FileAPI(base_dir='/home/ai/zhineng-bridge')
push_service = PushService()


class HealthCheckHandler(BaseHTTPRequestHandler):
    """健康检查请求处理器"""

    def _set_headers(self, status_code=200):
        """设置响应头"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_GET(self):
        """处理 GET 请求"""
        if self.path == '/' or self.path == '':
            self.handle_root()
        elif self.path == '/health':
            self.handle_health_check()
        elif self.path == '/metrics':
            self.handle_metrics()
        elif self.path == '/prometheus':
            self.handle_prometheus_metrics()
        elif self.path == '/status':
            self.handle_status()
        elif self.path == '/docs':
            self.handle_docs()
        elif self.path == '/openapi.yaml':
            self.handle_openapi_spec()
        elif self.path.startswith('/web/'):
            self.handle_static_file()
        elif self.path.startswith('/api/files/'):
            self.handle_file_api()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def do_POST(self):
        """处理 POST 请求"""
        if self.path.startswith('/api/notifications/'):
            self.handle_push_api()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def handle_health_check(self):
        """处理健康检查请求"""
        # 检查各组件的健康状态
        components = {}
        overall_healthy = True

        # 检查 WebSocket 中继服务器
        relay_server_status = self.check_relay_server()
        components["relay_server"] = relay_server_status["status"]
        if relay_server_status["status"] != "healthy":
            overall_healthy = False

        # 检查 HTTP 服务器（自身）
        http_server_status = self.check_http_server()
        components["http_server"] = http_server_status["status"]
        if http_server_status["status"] != "healthy":
            overall_healthy = False

        # 检查 Session Manager
        session_manager_status = self.check_session_manager()
        components["session_manager"] = session_manager_status["status"]
        if session_manager_status["status"] != "healthy":
            overall_healthy = False

        # 检查系统资源
        system_status = self.check_system_resources()
        components["system"] = system_status["status"]
        if system_status["status"] != "healthy":
            overall_healthy = False

        # 检查速率限制器
        rate_limiter_status = self.check_rate_limiter()
        components["rate_limiter"] = rate_limiter_status["status"]
        if rate_limiter_status["status"] != "healthy":
            overall_healthy = False

        health_status = {
            "status": "healthy" if overall_healthy else "unhealthy",
            "service": "zhineng-bridge",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "components": components,
            "details": {
                "relay_server": relay_server_status,
                "http_server": http_server_status,
                "session_manager": session_manager_status,
                "system": system_status,
                "rate_limiter": rate_limiter_status
            }
        }

        status_code = 200 if overall_healthy else 503
        self._set_headers(status_code)
        self.wfile.write(json.dumps(health_status, indent=2).encode())

    def check_relay_server(self) -> dict:
        """检查 WebSocket 中继服务器"""
        try:
            # 尝试连接到 WebSocket 服务器端口
            host = settings.server.host
            port = settings.server.port

            # 如果 host 是 '0.0.0.0'，尝试连接到 localhost
            if host == '0.0.0.0':
                host = '127.0.0.1'

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return {
                    "status": "healthy",
                    "message": f"WebSocket server is reachable on {host}:{port}"
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"Cannot connect to WebSocket server on {host}:{port}"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Error checking WebSocket server: {str(e)}"
            }

    def check_http_server(self) -> dict:
        """检查 HTTP 服务器（自身）"""
        try:
            # 如果能响应此请求，HTTP 服务器就是健康的
            return {
                "status": "healthy",
                "message": "HTTP server is responding"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"HTTP server error: {str(e)}"
            }

    def check_session_manager(self) -> dict:
        """检查 Session Manager"""
        try:
            # 检查 Session Manager 模块是否可导入
            from session_manager import SessionManager

            return {
                "status": "healthy",
                "message": "Session Manager module is available"
            }
        except Exception as e:
            return {
                "status": "degraded",
                "message": f"Session Manager not available: {str(e)}"
            }

    def check_system_resources(self) -> dict:
        """检查系统资源"""
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=0.5)
            # 内存使用情况
            memory = psutil.virtual_memory()
            # 磁盘使用情况
            disk = psutil.disk_usage('/')

            # 定义阈值
            cpu_threshold = 80.0  # 80%
            memory_threshold = 80.0  # 80%
            disk_threshold = 90.0  # 90%

            issues = []
            if cpu_percent > cpu_threshold:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory.percent > memory_threshold:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            if disk.percent > disk_threshold:
                issues.append(f"High disk usage: {disk.percent:.1f}%")

            if issues:
                return {
                    "status": "degraded" if len(issues) == 1 else "unhealthy",
                    "message": "; ".join(issues),
                    "metrics": {
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "memory_available_mb": memory.available / (1024 * 1024),
                        "disk_percent": disk.percent,
                        "disk_free_gb": disk.free / (1024 ** 3)
                    }
                }
            else:
                return {
                    "status": "healthy",
                    "message": "System resources are within normal limits",
                    "metrics": {
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "memory_available_mb": memory.available / (1024 * 1024),
                        "disk_percent": disk.percent,
                        "disk_free_gb": disk.free / (1024 ** 3)
                    }
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Error checking system resources: {str(e)}"
            }

    def check_rate_limiter(self) -> dict:
        """检查速率限制器"""
        try:
            # 尝试获取速率限制器统计信息
            stats = rate_limiter.get_global_stats()
            return {
                "status": "healthy",
                "message": "Rate limiter is operational",
                "active_clients": stats["active_clients"]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Rate limiter error: {str(e)}"
            }

    def handle_metrics(self):
        """处理指标请求"""
        # 获取速率限制统计信息
        rate_limit_stats = rate_limiter.get_global_stats()

        metrics = {
            "service": "zhineng-bridge",
            "rate_limiting": {
                "enabled": settings.security.enable_rate_limit,
                "algorithm": rate_limit_stats["algorithm"],
                "requests_per_minute": rate_limit_stats["requests_per_minute"],
                "requests_per_hour": rate_limit_stats["requests_per_hour"],
                "active_clients": rate_limit_stats["active_clients"],
                **(
                    {
                        "global_minute_tokens": rate_limit_stats["global_minute_tokens"],
                        "global_hour_tokens": rate_limit_stats["global_hour_tokens"],
                    }
                    if rate_limit_stats["algorithm"] == "token_bucket"
                    else {
                        "global_minute_requests": rate_limit_stats[
                            "global_minute_requests"
                        ],
                        "global_hour_requests": rate_limit_stats[
                            "global_hour_requests"
                        ],
                    }
                ),
            },
            "other_metrics": {
                "websocket_connections": 0,
                "active_sessions": 0,
                "messages_sent": 0,
                "messages_received": 0,
                "errors": 0,
                "uptime_seconds": 0,
            },
        }

        self._set_headers(200)
        self.wfile.write(json.dumps(metrics, indent=2).encode())

    def handle_prometheus_metrics(self):
        """处理 Prometheus 指标请求"""
        try:
            # Get Prometheus metrics in text format
            prometheus_metrics = get_metrics()

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(prometheus_metrics)
        except Exception as e:
            logger.error(f"Error serving Prometheus metrics: {e}", exc_info=True)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def handle_status(self):
        """处理状态请求"""
        status = {
            "service": "zhineng-bridge",
            "version": "1.0.0",
            "configuration": {
                "host": settings.server.host,
                "port": settings.server.port,
                "max_connections": settings.server.max_connections,
                "log_level": settings.server.log_level
            },
            "features": {
                "authentication_enabled": settings.security.enable_auth,
                "rate_limiting_enabled": settings.security.enable_rate_limit,
                "compression_enabled": settings.server.enable_compression,
                "wss_enabled": settings.server.enable_wss
            }
        }

        self._set_headers(200)
        self.wfile.write(json.dumps(status, indent=2).encode())

    def handle_docs(self):
        """处理 Swagger UI 文档请求"""
        try:
            docs_path = Path(__file__).parent.parent / 'docs' / 'swagger-ui.html'
            if docs_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(docs_path, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Documentation not found"}).encode())
        except Exception as e:
            print(f"❌ Error serving docs: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def handle_openapi_spec(self):
        """处理 OpenAPI 规范请求"""
        try:
            openapi_path = Path(__file__).parent.parent / 'docs' / 'openapi.yaml'
            if openapi_path.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'text/yaml; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(openapi_path, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "OpenAPI specification not found"}).encode())
        except Exception as e:
            print(f"❌ Error serving OpenAPI spec: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def handle_root(self):
        """处理根路径请求"""
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智桥 (Zhineng-Bridge) - 健康检查服务器</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 800px;
            width: 100%;
            padding: 40px;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .logo {
            font-size: 48px;
            margin-bottom: 10px;
        }
        h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        .version {
            color: #666;
            font-size: 14px;
        }
        .endpoints {
            display: grid;
            gap: 15px;
            margin-bottom: 30px;
        }
        .endpoint {
            display: flex;
            align-items: center;
            padding: 15px 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }
        .endpoint:hover {
            background: #e9ecef;
            transform: translateX(5px);
        }
        .endpoint a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            flex: 1;
        }
        .endpoint a:hover {
            color: #764ba2;
        }
        .method {
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 15px;
        }
        .description {
            color: #666;
            font-size: 14px;
            margin-left: 10px;
        }
        .footer {
            text-align: center;
            color: #999;
            font-size: 14px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
        }
        .footer a {
            color: #667eea;
            text-decoration: none;
        }
        .status {
            display: inline-block;
            padding: 6px 16px;
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🌉</div>
            <h1>智桥 (Zhineng-Bridge)</h1>
            <div class="version">版本 1.0.0 | 跨平台实时同步和通信 SDK</div>
            <div class="status">✅ 服务运行正常</div>
        </div>

        <h2 style="color: #333; margin-bottom: 20px;">📡 可用端点</h2>
        <div class="endpoints">
            <div class="endpoint">
                <span class="method">GET</span>
                <a href="/health">/health</a>
                <span class="description">健康检查</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <a href="/status">/status</a>
                <span class="description">服务状态和配置</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <a href="/metrics">/metrics</a>
                <span class="description">性能指标</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <a href="/prometheus">/prometheus</a>
                <span class="description">Prometheus 指标</span>
            </div>
            <div class="endpoint" style="background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);">
                <span class="method">GET</span>
                <a href="/docs" style="color: #764ba2;">/docs</a>
                <span class="description">📘 API 文档 (Swagger UI)</span>
            </div>
            <div class="endpoint">
                <span class="method">GET</span>
                <a href="/openapi.yaml">/openapi.yaml</a>
                <span class="description">OpenAPI 规范</span>
            </div>
        </div>

        <h2 style="color: #333; margin-bottom: 20px;">📚 相关资源</h2>
        <div class="endpoints">
            <div class="endpoint">
                <span class="method">DOC</span>
                <a href="/docs" style="color: #764ba2;">API 文档</a>
                <span class="description">交互式 API 文档</span>
            </div>
            <div class="endpoint">
                <span class="method">WEB</span>
                <a href="http://100.66.1.8:8000/web/ui/index.html" target="_blank">Web UI</a>
                <span class="description">智桥 Web 界面</span>
            </div>
        </div>

        <div class="footer">
            <p>支持 8 个 AI 编码工具：Crush, Claude Code, iFlow CLI, Cursor, Trae, Droid, OpenClaw, GitHub Copilot</p>
            <p style="margin-top: 10px;">
                <a href="https://github.com/guangda88/zhineng-bridge" target="_blank">GitHub</a> | 
                <a href="http://zhinenggitea.iepose.cn/guangda/zhineng-bridge" target="_blank">Gitea</a>
            </p>
        </div>
    </div>
</body>
</html>
        """
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error serving root page: {e}", exc_info=True)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def handle_static_file(self):
        """处理静态文件请求"""
        try:
            # 获取请求的路径并移除 /web 前缀
            request_path = self.path.lstrip('/web/')

            # 移除查询参数（例如 ?v=2026032902）
            if '?' in request_path:
                request_path = request_path.split('?')[0]

            # 构建完整的文件系统路径
            web_dir = Path(__file__).parent.parent / 'web'
            file_path = web_dir / request_path

            # 安全检查：确保文件在 web 目录下
            file_path = file_path.resolve()
            web_dir = web_dir.resolve()
            if not str(file_path).startswith(str(web_dir)):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Access denied"}).encode())
                return

            # 如果路径是目录，尝试提供 index.html
            if file_path.is_dir():
                file_path = file_path / 'index.html'

            # 检查文件是否存在
            if not file_path.exists():
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "File not found"}).encode())
                return

            # 根据 MIME 类型发送响应
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type is None:
                mime_type = 'application/octet-stream'

            self.send_response(200)
            self.send_header('Content-Type', f'{mime_type}; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'public, max-age=3600')

            # 对于 CSS 和 JS，添加额外的缓存控制
            if mime_type in ['text/css', 'text/javascript', 'application/javascript']:
                self.send_header('Cache-Control', 'public, max-age=86400')

            self.end_headers()

            # 发送文件内容
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())

        except Exception as e:
            logger.error(f"Error serving static file {self.path}: {e}", exc_info=True)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def handle_file_api(self):
        """处理文件 API 请求"""
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)

            # 路由到具体的处理器
            if parsed.path == '/api/files/read':
                self._handle_file_read(query)
            elif parsed.path == '/api/files/search':
                self._handle_file_search(query)
            elif parsed.path == '/api/files/stats':
                self._handle_file_stats(query)
            elif parsed.path == '/api/files/list':
                self._handle_file_list(query)
            else:
                self._send_json_response(404, {"error": "Not found"})

        except Exception as e:
            logger.error(f"Error handling file API request: {e}", exc_info=True)
            self._send_json_response(500, {"type": "error", "message": str(e), "code": 500})

    def _handle_file_read(self, query):
        """处理文件读取 API"""
        file_path = query.get('path', [None])[0]
        if not file_path:
            self._send_json_response(400, {"type": "error", "message": "Missing 'path' parameter", "code": 400})
            return

        try:
            validated_path = file_api._validate_path(file_path)

            if not validated_path.is_file():
                self._send_json_response(404, {"type": "error", "message": f"Not a file: {file_path}", "code": 404})
                return

            file_api._check_file_permissions(validated_path)

            # 检查缓存
            cache_key = str(validated_path)
            if cache_key in file_api.cache:
                mtime = validated_path.stat().st_mtime
                cached = file_api.cache[cache_key]
                if cached['mtime'] == mtime:
                    self._send_json_response(200, cached['data'])
                    return

            # 读取文件内容
            try:
                with open(validated_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except UnicodeDecodeError:
                self._send_json_response(400, {"type": "error", "message": "Cannot read binary file", "code": 400})
                return

            # 获取文件元数据
            import mimetypes
            stat = validated_path.stat()
            mime_type, _ = mimetypes.guess_type(str(validated_path))

            data = {
                "type": "file_content",
                "path": str(validated_path),
                "content": content,
                "metadata": {
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "mime_type": mime_type or "text/plain",
                    "extension": validated_path.suffix
                }
            }

            # 缓存结果
            file_api.cache[cache_key] = {
                'mtime': stat.st_mtime,
                'data': data
            }

            self._send_json_response(200, data)

        except ValueError as e:
            self._send_json_response(400, {"type": "error", "message": str(e), "code": 400})
        except PermissionError as e:
            self._send_json_response(403, {"type": "error", "message": str(e), "code": 403})

    def _handle_file_search(self, query):
        """处理文件搜索 API"""
        query_param = query.get('query', [''])[0]
        search_path = query.get('path', ['/home/ai/zhineng-bridge'])[0]
        limit = int(query.get('limit', [50])[0])
        offset = int(query.get('offset', [0])[0])

        if not query_param:
            self._send_json_response(400, {"type": "error", "message": "Missing 'query' parameter", "code": 400})
            return

        try:
            validated_path = file_api._validate_path(search_path)

            if not validated_path.exists():
                self._send_json_response(404, {"type": "error", "message": f"Search path does not exist: {search_path}", "code": 404})
                return

            import re
            query_pattern = re.compile(re.escape(query_param), re.IGNORECASE)

            results = []
            count = 0

            for file_path in validated_path.rglob('*'):
                if file_path.is_file():
                    if query_pattern.search(file_path.name):
                        if count >= offset and len(results) < limit:
                            try:
                                stat = file_path.stat()
                                results.append({
                                    "path": str(file_path),
                                    "name": file_path.name,
                                    "size": stat.st_size,
                                    "modified": stat.st_mtime,
                                    "extension": file_path.suffix
                                })
                            except OSError:
                                pass
                        count += 1

            data = {
                "type": "search_results",
                "query": query_param,
                "path": search_path,
                "results": results,
                "count": len(results),
                "total": count,
                "limit": limit,
                "offset": offset
            }

            self._send_json_response(200, data)

        except ValueError as e:
            self._send_json_response(400, {"type": "error", "message": str(e), "code": 400})

    def _handle_file_stats(self, query):
        """处理文件统计 API"""
        file_path = query.get('path', [None])[0]
        if not file_path:
            self._send_json_response(400, {"type": "error", "message": "Missing 'path' parameter", "code": 400})
            return

        try:
            validated_path = file_api._validate_path(file_path)

            if not validated_path.exists():
                self._send_json_response(404, {"type": "error", "message": f"File not found: {file_path}", "code": 404})
                return

            import mimetypes
            stat = validated_path.stat()
            mime_type, _ = mimetypes.guess_type(str(validated_path))

            data = {
                "type": "file_stats",
                "path": str(validated_path),
                "name": validated_path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "is_file": validated_path.is_file(),
                "is_dir": validated_path.is_dir(),
                "extension": validated_path.suffix,
                "mime_type": mime_type or ("inode/directory" if validated_path.is_dir() else "application/octet-stream")
            }

            if validated_path.is_dir():
                file_count = 0
                dir_count = 0
                for _ in validated_path.iterdir():
                    if _.is_file():
                        file_count += 1
                    elif _.is_dir():
                        dir_count += 1
                data['directory'] = {
                    "file_count": file_count,
                    "dir_count": dir_count
                }

            self._send_json_response(200, data)

        except ValueError as e:
            self._send_json_response(400, {"type": "error", "message": str(e), "code": 400})

    def _handle_file_list(self, query):
        """处理文件列表 API"""
        list_path = query.get('path', ['/home/ai/zhineng-bridge'])[0]
        recursive = query.get('recursive', ['false'])[0].lower() == 'true'
        limit = int(query.get('limit', [100])[0])
        offset = int(query.get('offset', [0])[0])

        try:
            validated_path = file_api._validate_path(list_path)

            if not validated_path.exists():
                self._send_json_response(404, {"type": "error", "message": f"Directory not found: {list_path}", "code": 404})
                return

            if not validated_path.is_dir():
                self._send_json_response(400, {"type": "error", "message": f"Not a directory: {list_path}", "code": 400})
                return

            files = []
            count = 0

            if recursive:
                for file_path in validated_path.rglob('*'):
                    if count >= offset and len(files) < limit:
                        try:
                            stat = file_path.stat()
                            files.append({
                                "path": str(file_path.relative_to(validated_path)),
                                "name": file_path.name,
                                "size": stat.st_size,
                                "modified": stat.st_mtime,
                                "is_file": file_path.is_file(),
                                "is_dir": file_path.is_dir(),
                                "extension": file_path.suffix
                            })
                        except OSError:
                            pass
                    count += 1
            else:
                for item in validated_path.iterdir():
                    if count >= offset and len(files) < limit:
                        try:
                            stat = item.stat()
                            files.append({
                                "path": str(item.relative_to(validated_path)),
                                "name": item.name,
                                "size": stat.st_size,
                                "modified": stat.st_mtime,
                                "is_file": item.is_file(),
                                "is_dir": item.is_dir(),
                                "extension": item.suffix
                            })
                        except OSError:
                            pass
                    count += 1

            files.sort(key=lambda x: (not x['is_dir'], x['name']))

            data = {
                "type": "file_list",
                "path": list_path,
                "recursive": recursive,
                "files": files,
                "count": len(files),
                "total": count,
                "limit": limit,
                "offset": offset
            }

            self._send_json_response(200, data)

        except ValueError as e:
            self._send_json_response(400, {"type": "error", "message": str(e), "code": 400})

    def handle_push_api(self):
        """处理推送服务 API 请求"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.path)

            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            request_body = self.rfile.read(content_length)

            # 解析 JSON
            import json
            try:
                data = json.loads(request_body.decode('utf-8'))
            except json.JSONDecodeError:
                self._send_json_response(400, {"type": "error", "message": "Invalid JSON", "code": 400})
                return

            # 推送订阅
            if parsed.path == '/api/notifications/subscribe':
                import asyncio
                async def subscribe():
                    class MockRequest:
                        def __init__(self, body):
                            self._body = body

                        async def json(self):
                            return self._body

                    return await push_service.subscribe(MockRequest(data))

                response = asyncio.run(subscribe())

                if hasattr(response, 'status'):
                    status = response.status
                    body = response.body if hasattr(response, 'body') else b''
                else:
                    status = 201
                    body = json.dumps(response).encode() if isinstance(response, (dict, list)) else b''

                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(body)

            # 推送取消订阅
            elif parsed.path == '/api/notifications/unsubscribe':
                import asyncio
                async def unsubscribe():
                    class MockRequest:
                        def __init__(self, body):
                            self._body = body

                        async def json(self):
                            return self._body

                    return await push_service.unsubscribe(MockRequest(data))

                response = asyncio.run(unsubscribe())

                if hasattr(response, 'status'):
                    status = response.status
                    body = response.body if hasattr(response, 'body') else b''
                else:
                    status = 200
                    body = json.dumps(response).encode() if isinstance(response, (dict, list)) else b''

                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(body)

            # 发送推送通知
            elif parsed.path == '/api/notifications/send':
                import asyncio
                async def send():
                    class MockRequest:
                        def __init__(self, body):
                            self._body = body

                        async def json(self):
                            return self._body

                    return await push_service.send_notification(MockRequest(data))

                response = asyncio.run(send())

                if hasattr(response, 'status'):
                    status = response.status
                    body = response.body if hasattr(response, 'body') else b''
                else:
                    status = 200
                    body = json.dumps(response).encode() if isinstance(response, (dict, list)) else b''

                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(body)

            else:
                self._send_json_response(404, {"error": "Not found"})

        except Exception as e:
            logger.error(f"Error handling push API request: {e}", exc_info=True)
            self._send_json_response(500, {"type": "error", "message": str(e), "code": 500})

    def _send_json_response(self, status_code, data):
        """发送 JSON 响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        """处理 OPTIONS 请求（CORS 预检）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        """抑制默认日志输出"""
        # 重写以抑制默认的日志输出
        pass


def main():
    """主函数"""
    port = 8080

    print(f"🏥 Health Check Server starting on port {port}")
    print(f"   Health endpoint:        http://{settings.server.ws_host}:{port}/health")
    print(f"   Metrics endpoint:       http://{settings.server.ws_host}:{port}/metrics")
    print(f"   Prometheus metrics:     http://{settings.server.ws_host}:{port}/prometheus")
    print(f"   Status endpoint:       http://{settings.server.ws_host}:{port}/status")
    print(f"   API Docs:              http://{settings.server.ws_host}:{port}/docs")
    print(f"   OpenAPI Spec:          http://{settings.server.ws_host}:{port}/openapi.yaml")
    print()

    # Start metrics updater
    print("📊 Starting metrics updater...")
    start_metrics_updater(interval=5)
    print("   Metrics will be updated every 5 seconds")
    print()

    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"✅ Health Check Server is running")
    print(f"   Listening on http://0.0.0.0:{port}")
    print()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Health Check Server stopped")
        server.shutdown()


if __name__ == "__main__":
    main()
