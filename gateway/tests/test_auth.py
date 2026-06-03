"""
鉴权单元测试
"""
import os
import pytest
from fastapi.testclient import TestClient
from gateway.app import create_app

TEST_API_KEY = os.environ.get("ZHIBRIDGE_API_KEY", "test_lpkey_1234567890abcdef")


class TestAuth:
    def setup_method(self):
        os.environ["ZHIBRIDGE_API_KEY"] = TEST_API_KEY
        # Must import fresh to pick up new env var
        import importlib
        import gateway.config as cfg
        importlib.reload(cfg)
        from gateway.app import create_app
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_missing_api_key_returns_401(self):
        resp = self.client.post("/v1/chat/completions", json={})
        assert resp.status_code == 401

    def test_short_api_key_returns_401(self):
        resp = self.client.post(
            "/v1/chat/completions",
            json={},
            headers={"X-API-Key": "short"}
        )
        assert resp.status_code == 401

    def test_wrong_api_key_returns_401(self):
        resp = self.client.post(
            "/v1/chat/completions",
            json={},
            headers={"X-API-Key": "lpk_a1b2c3d4e5f6g7h8i9j0k1l"}
        )
        assert resp.status_code == 401

    def test_correct_api_key_passes_gateway(self):
        resp = self.client.post(
            "/v1/chat/completions",
            json={},
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert resp.status_code != 401

    def test_internal_route_requires_auth(self):
        resp = self.client.get("/internal/lingtong_plus/api/status")
        assert resp.status_code == 401

    def test_internal_route_correct_key_passes(self):
        resp = self.client.get(
            "/internal/lingtong_plus/api/status",
            headers={"X-API-Key": TEST_API_KEY}
        )
        assert resp.status_code != 401