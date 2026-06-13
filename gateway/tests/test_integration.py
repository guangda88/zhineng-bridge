"""
集成测试
"""

import importlib
import os

from fastapi.testclient import TestClient

TEST_KEY = "test-api-key-for-gateway-tests-1234567890"


class TestIntegration:
    def setup_method(self):
        self.app = create_app_with_key()
        self.client = TestClient(self.app)

    def test_metrics_endpoint(self):
        """测试Prometheus指标端点需要鉴权"""
        resp = self.client.get("/metrics")
        assert resp.status_code == 401
        resp = self.client.get("/metrics", headers={"X-API-Key": TEST_KEY})
        assert resp.status_code == 200

    def test_podcast_endpoint_requires_auth(self):
        """测试播客端点需要鉴权 (R14-001 P1-3修复)"""
        resp = self.client.get("/api/podcast/episodes")
        assert resp.status_code == 401

    def test_urgent_request_passes_gateway(self):
        """urgent请求通过网关鉴权层"""
        resp = self.client.post(
            "/projects/lingvision/api/v1/diagnose",
            json={"image_url": "test"},
            headers={"X-API-Key": TEST_KEY, "X-Priority": "urgent"},
        )
        assert resp.status_code != 400
        assert resp.status_code != 401

    def test_normal_request_without_priority(self):
        """无X-Priority头的请求正常处理"""
        resp = self.client.post(
            "/projects/lingvision/api/v1/diagnose",
            json={"image_url": "test"},
            headers={"X-API-Key": TEST_KEY},
        )
        assert resp.status_code != 401

    def test_metrics_include_sdth_counters(self):
        """metrics端点包含SDTH指标"""
        resp = self.client.get("/metrics", headers={"X-API-Key": TEST_KEY})
        assert resp.status_code == 200
        text = resp.text
        assert "zhibridge_urgent_requests_total" in text
        assert "zhibridge_latency_gap_seconds" in text


class TestPathWhitelist:
    def setup_method(self):
        self.app = create_app_with_key()
        self.client = TestClient(self.app)

    def test_internal_allowed_path(self):
        """白名单内路径通过"""
        resp = self.client.get(
            "/internal/lingzhi/health",
            headers={"X-API-Key": TEST_KEY},
        )
        assert resp.status_code != 403

    def test_internal_denied_path(self):
        """白名单外路径被403"""
        resp = self.client.get(
            "/internal/lingzhi/admin/config",
            headers={"X-API-Key": TEST_KEY},
        )
        assert resp.status_code == 403
        assert resp.json()["error"] == "path_not_allowed"

    def test_internal_unknown_backend(self):
        """未知后端返回404"""
        resp = self.client.get(
            "/internal/nonexistent/health",
            headers={"X-API-Key": TEST_KEY},
        )
        assert resp.status_code == 404

    def test_internal_subpath_allowed(self):
        """白名单路径的子路径也通过（前缀匹配）"""
        resp = self.client.get(
            "/internal/lingzhi/api/v1/search?q=test",
            headers={"X-API-Key": TEST_KEY},
        )
        assert resp.status_code != 403


def create_app_with_key():
    os.environ["ZHIBRIDGE_API_KEY"] = TEST_KEY
    import gateway.config as cfg

    importlib.reload(cfg)
    from gateway.app import create_app

    return create_app()
