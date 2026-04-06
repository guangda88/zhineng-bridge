"""HTTP 请求处理器 — 路由与响应"""

import json
import mimetypes
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from health.checks import HealthChecker
from health.root_page import ROOT_HTML

from config import settings
from rate_limit import rate_limiter
from metrics import get_metrics
from logger import get_logger
from file_api import FileAPI
from push_service import PushService

logger = get_logger(__name__)

file_api = FileAPI(base_dir="/home/ai/zhineng-bridge")
push_service = PushService()


class HealthCheckHandler(BaseHTTPRequestHandler):
    """健康检查请求处理器"""

    def _set_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    # ---- routing ----

    def do_GET(self):
        routes = {
            "/": self.handle_root,
            "/health": self.handle_health_check,
            "/metrics": self.handle_metrics,
            "/prometheus": self.handle_prometheus_metrics,
            "/status": self.handle_status,
            "/docs": self.handle_docs,
            "/openapi.yaml": self.handle_openapi_spec,
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        elif self.path.startswith("/web/"):
            self.handle_static_file()
        elif self.path.startswith("/api/files/"):
            self.handle_file_api()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def do_POST(self):
        if self.path.startswith("/api/notifications/"):
            self.handle_push_api()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass

    # ---- health check ----

    def handle_health_check(self):
        checker = HealthChecker(host=settings.server.host, port=settings.server.port)
        result = checker.run_all(rate_limiter=rate_limiter)
        status_code = 200 if result["overall"] == "healthy" else 503
        health_status = {
            "status": result["overall"],
            "service": "zhineng-bridge",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "components": result["components"],
            "details": result["details"],
        }
        self._set_headers(status_code)
        self.wfile.write(json.dumps(health_status, indent=2).encode())

    # ---- metrics ----

    def handle_metrics(self):
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
                    {"global_minute_tokens": rate_limit_stats["global_minute_tokens"], "global_hour_tokens": rate_limit_stats["global_hour_tokens"]}
                    if rate_limit_stats["algorithm"] == "token_bucket"
                    else {"global_minute_requests": rate_limit_stats["global_minute_requests"], "global_hour_requests": rate_limit_stats["global_hour_requests"]}
                ),
            },
            "other_metrics": {"websocket_connections": 0, "active_sessions": 0, "messages_sent": 0, "messages_received": 0, "errors": 0, "uptime_seconds": 0},
        }
        self._set_headers(200)
        self.wfile.write(json.dumps(metrics, indent=2).encode())

    def handle_prometheus_metrics(self):
        try:
            prometheus_metrics = get_metrics()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(prometheus_metrics)
        except Exception as e:
            logger.error(f"Error serving Prometheus metrics: {e}", exc_info=True)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ---- status / docs ----

    def handle_status(self):
        status = {
            "service": "zhineng-bridge",
            "version": "1.0.0",
            "configuration": {"host": settings.server.host, "port": settings.server.port, "max_connections": settings.server.max_connections, "log_level": settings.server.log_level},
            "features": {
                "authentication_enabled": settings.security.enable_auth,
                "rate_limiting_enabled": settings.security.enable_rate_limit,
                "compression_enabled": settings.server.enable_compression,
                "wss_enabled": settings.server.enable_wss,
            },
        }
        self._set_headers(200)
        self.wfile.write(json.dumps(status, indent=2).encode())

    def handle_docs(self):
        try:
            docs_path = Path(__file__).parent.parent.parent / "docs" / "swagger-ui.html"
            if docs_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(docs_path, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Documentation not found"}).encode())
        except Exception as e:
            logger.error(f"Error serving docs: {e}", exc_info=True)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def handle_openapi_spec(self):
        try:
            openapi_path = Path(__file__).parent.parent.parent / "docs" / "openapi.yaml"
            if openapi_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/yaml; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                with open(openapi_path, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "OpenAPI specification not found"}).encode())
        except Exception as e:
            logger.error(f"Error serving OpenAPI spec: {e}", exc_info=True)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ---- root page ----

    def handle_root(self):
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(ROOT_HTML.encode("utf-8"))
        except Exception as e:
            logger.error(f"Error serving root page: {e}", exc_info=True)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ---- static files ----

    def handle_static_file(self):
        try:
            request_path = self.path.lstrip("/web/")
            if "?" in request_path:
                request_path = request_path.split("?")[0]

            web_dir = Path(__file__).parent.parent.parent / "web"
            file_path = (web_dir / request_path).resolve()
            web_dir = web_dir.resolve()

            if not str(file_path).startswith(str(web_dir)):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Access denied"}).encode())
                return

            if file_path.is_dir():
                file_path = file_path / "index.html"

            if not file_path.exists():
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "File not found"}).encode())
                return

            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type is None:
                mime_type = "application/octet-stream"

            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            if mime_type in ["text/css", "text/javascript", "application/javascript"]:
                self.send_header("Cache-Control", "public, max-age=86400")
            else:
                self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()

            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        except Exception as e:
            logger.error(f"Error serving static file {self.path}: {e}", exc_info=True)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ---- file API ----

    def handle_file_api(self):
        try:
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            sub_handlers = {
                "/api/files/read": self._handle_file_read,
                "/api/files/search": self._handle_file_search,
                "/api/files/stats": self._handle_file_stats,
                "/api/files/list": self._handle_file_list,
            }
            handler = sub_handlers.get(parsed.path)
            if handler:
                handler(query)
            else:
                self._send_json_response(404, {"error": "Not found"})
        except Exception as e:
            logger.error(f"Error handling file API request: {e}", exc_info=True)
            self._send_json_response(500, {"type": "error", "message": str(e), "code": 500})

    def _handle_file_read(self, query):
        file_path = query.get("path", [None])[0]
        if not file_path:
            self._send_json_response(400, {"type": "error", "message": "Missing 'path' parameter", "code": 400})
            return
        try:
            validated_path = file_api._validate_path(file_path)
            if not validated_path.is_file():
                self._send_json_response(404, {"type": "error", "message": f"Not a file: {file_path}", "code": 404})
                return
            file_api._check_file_permissions(validated_path)

            cache_key = str(validated_path)
            if cache_key in file_api.cache:
                mtime = validated_path.stat().st_mtime
                cached = file_api.cache[cache_key]
                if cached["mtime"] == mtime:
                    self._send_json_response(200, cached["data"])
                    return

            try:
                with open(validated_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except UnicodeDecodeError:
                self._send_json_response(400, {"type": "error", "message": "Cannot read binary file", "code": 400})
                return

            stat = validated_path.stat()
            mime_type, _ = mimetypes.guess_type(str(validated_path))
            data = {"type": "file_content", "path": str(validated_path), "content": content, "metadata": {"size": stat.st_size, "modified": stat.st_mtime, "mime_type": mime_type or "text/plain", "extension": validated_path.suffix}}
            file_api.cache[cache_key] = {"mtime": stat.st_mtime, "data": data}
            self._send_json_response(200, data)
        except ValueError as e:
            self._send_json_response(400, {"type": "error", "message": str(e), "code": 400})
        except PermissionError as e:
            self._send_json_response(403, {"type": "error", "message": str(e), "code": 403})

    def _handle_file_search(self, query):
        query_param = query.get("query", [""])[0]
        search_path = query.get("path", ["/home/ai/zhineng-bridge"])[0]
        limit = int(query.get("limit", [50])[0])
        offset = int(query.get("offset", [0])[0])
        if not query_param:
            self._send_json_response(400, {"type": "error", "message": "Missing 'query' parameter", "code": 400})
            return
        try:
            import re
            validated_path = file_api._validate_path(search_path)
            if not validated_path.exists():
                self._send_json_response(404, {"type": "error", "message": f"Search path does not exist: {search_path}", "code": 404})
                return
            query_pattern = re.compile(re.escape(query_param), re.IGNORECASE)
            results = []
            count = 0
            for fp in validated_path.rglob("*"):
                if fp.is_file() and query_pattern.search(fp.name):
                    if count >= offset and len(results) < limit:
                        try:
                            st = fp.stat()
                            results.append({"path": str(fp), "name": fp.name, "size": st.st_size, "modified": st.st_mtime, "extension": fp.suffix})
                        except OSError:
                            pass
                    count += 1
            self._send_json_response(200, {"type": "search_results", "query": query_param, "path": search_path, "results": results, "count": len(results), "total": count, "limit": limit, "offset": offset})
        except ValueError as e:
            self._send_json_response(400, {"type": "error", "message": str(e), "code": 400})

    def _handle_file_stats(self, query):
        file_path = query.get("path", [None])[0]
        if not file_path:
            self._send_json_response(400, {"type": "error", "message": "Missing 'path' parameter", "code": 400})
            return
        try:
            validated_path = file_api._validate_path(file_path)
            if not validated_path.exists():
                self._send_json_response(404, {"type": "error", "message": f"File not found: {file_path}", "code": 404})
                return
            st = validated_path.stat()
            mime_type, _ = mimetypes.guess_type(str(validated_path))
            data = {"type": "file_stats", "path": str(validated_path), "name": validated_path.name, "size": st.st_size, "modified": st.st_mtime, "created": st.st_ctime, "is_file": validated_path.is_file(), "is_dir": validated_path.is_dir(), "extension": validated_path.suffix, "mime_type": mime_type or ("inode/directory" if validated_path.is_dir() else "application/octet-stream")}
            if validated_path.is_dir():
                fc, dc = 0, 0
                for item in validated_path.iterdir():
                    if item.is_file():
                        fc += 1
                    elif item.is_dir():
                        dc += 1
                data["directory"] = {"file_count": fc, "dir_count": dc}
            self._send_json_response(200, data)
        except ValueError as e:
            self._send_json_response(400, {"type": "error", "message": str(e), "code": 400})

    def _handle_file_list(self, query):
        list_path = query.get("path", ["/home/ai/zhineng-bridge"])[0]
        recursive = query.get("recursive", ["false"])[0].lower() == "true"
        limit = int(query.get("limit", [100])[0])
        offset = int(query.get("offset", [0])[0])
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
            items = validated_path.rglob("*") if recursive else validated_path.iterdir()
            for item in items:
                if count >= offset and len(files) < limit:
                    try:
                        st = item.stat()
                        files.append({"path": str(item.relative_to(validated_path)), "name": item.name, "size": st.st_size, "modified": st.st_mtime, "is_file": item.is_file(), "is_dir": item.is_dir(), "extension": item.suffix})
                    except OSError:
                        pass
                count += 1
            files.sort(key=lambda x: (not x["is_dir"], x["name"]))
            self._send_json_response(200, {"type": "file_list", "path": list_path, "recursive": recursive, "files": files, "count": len(files), "total": count, "limit": limit, "offset": offset})
        except ValueError as e:
            self._send_json_response(400, {"type": "error", "message": str(e), "code": 400})

    # ---- push API ----

    def handle_push_api(self):
        try:
            parsed = urlparse(self.path)
            content_length = int(self.headers.get("Content-Length", 0))
            request_body = self.rfile.read(content_length)
            try:
                data = json.loads(request_body.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_json_response(400, {"type": "error", "message": "Invalid JSON", "code": 400})
                return

            import asyncio

            class MockRequest:
                def __init__(self, body):
                    self._body = body
                async def json(self):
                    return self._body

            routes = {
                "/api/notifications/subscribe": (push_service.subscribe, 201),
                "/api/notifications/unsubscribe": (push_service.unsubscribe, 200),
                "/api/notifications/send": (push_service.send_notification, 200),
            }
            entry = routes.get(parsed.path)
            if not entry:
                self._send_json_response(404, {"error": "Not found"})
                return

            handler_fn, default_status = entry
            response = asyncio.run(handler_fn(MockRequest(data)))

            if hasattr(response, "status"):
                status = response.status
                body = response.body if hasattr(response, "body") else b""
            else:
                status = default_status
                body = json.dumps(response).encode() if isinstance(response, (dict, list)) else b""

            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            logger.error(f"Error handling push API request: {e}", exc_info=True)
            self._send_json_response(500, {"type": "error", "message": str(e), "code": 500})
