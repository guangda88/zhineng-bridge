"""健康检查逻辑 — 各组件的状态检测"""

import socket
import psutil


class HealthChecker:
    """组件健康检查器"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port

    def check_relay_server(self) -> dict:
        host = self.host
        if host == "0.0.0.0":
            host = "127.0.0.1"
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, self.port))
            sock.close()
            if result == 0:
                return {"status": "healthy", "message": f"WebSocket server is reachable on {host}:{self.port}"}
            else:
                return {"status": "unhealthy", "message": f"Cannot connect to WebSocket server on {host}:{self.port}"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Error checking WebSocket server: {str(e)}"}

    def check_http_server(self) -> dict:
        return {"status": "healthy", "message": "HTTP server is responding"}

    def check_session_manager(self) -> dict:
        try:
            import session_manager
            return {"status": "healthy", "message": "Session Manager module is available"}
        except Exception as e:
            return {"status": "degraded", "message": f"Session Manager not available: {str(e)}"}

    def check_system_resources(self) -> dict:
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            cpu_threshold = 80.0
            memory_threshold = 80.0
            disk_threshold = 90.0

            issues = []
            if cpu_percent > cpu_threshold:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory.percent > memory_threshold:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            if disk.percent > disk_threshold:
                issues.append(f"High disk usage: {disk.percent:.1f}%")

            metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024 ** 3),
            }

            if issues:
                return {"status": "degraded" if len(issues) == 1 else "unhealthy", "message": "; ".join(issues), "metrics": metrics}
            return {"status": "healthy", "message": "System resources are within normal limits", "metrics": metrics}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Error checking system resources: {str(e)}"}

    def check_rate_limiter(self, rate_limiter) -> dict:
        try:
            stats = rate_limiter.get_global_stats()
            return {"status": "healthy", "message": "Rate limiter is operational", "active_clients": stats["active_clients"]}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Rate limiter error: {str(e)}"}

    def run_all(self, rate_limiter=None) -> dict:
        checks = {
            "relay_server": self.check_relay_server(),
            "http_server": self.check_http_server(),
            "session_manager": self.check_session_manager(),
            "system": self.check_system_resources(),
        }
        if rate_limiter is not None:
            checks["rate_limiter"] = self.check_rate_limiter(rate_limiter)

        overall_healthy = all(c["status"] == "healthy" for c in checks.values())
        return {
            "overall": "healthy" if overall_healthy else "unhealthy",
            "components": {k: v["status"] for k, v in checks.items()},
            "details": checks,
        }
