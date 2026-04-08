"""健康检查服务器入口点

保持向后兼容: python3 health_check.py 仍然可用。
新代码请使用: python3 -m health
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "phase1" / "session_manager"))

from http.server import HTTPServer
from health.handlers import HealthCheckHandler
from config import settings
from metrics import start_metrics_updater


def main():
    port = 8080

    print(f"🏥 Health Check Server starting on port {port}")
    print(f"   Health endpoint:        http://{settings.server.ws_host}:{port}/health")
    print(f"   Metrics endpoint:       http://{settings.server.ws_host}:{port}/metrics")
    print(f"   Prometheus metrics:     http://{settings.server.ws_host}:{port}/prometheus")
    print(f"   Status endpoint:       http://{settings.server.ws_host}:{port}/status")
    print(f"   API Docs:              http://{settings.server.ws_host}:{port}/docs")
    print(f"   OpenAPI Spec:          http://{settings.server.ws_host}:{port}/openapi.yaml")
    print()

    print("📊 Starting metrics updater...")
    start_metrics_updater(interval=5)
    print("   Metrics will be updated every 5 seconds")
    print()

    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print("✅ Health Check Server is running")
    print(f"   Listening on http://0.0.0.0:{port}")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Health Check Server stopped")
        server.shutdown()


if __name__ == "__main__":
    main()
