"""
集成测试
"""
import pytest
from fastapi.testclient import TestClient
from gateway.app import create_app


class TestIntegration:
    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_metrics_endpoint(self):
        """测试Prometheus指标端点"""
        resp = self.client.get("/metrics")
        assert resp.status_code == 200

    def test_podcast_endpoint_no_auth(self):
        """测试播客端点无需鉴权"""
        resp = self.client.get("/api/podcast/episodes")
        assert resp.status_code == 200
        assert "episodes" in resp.json()