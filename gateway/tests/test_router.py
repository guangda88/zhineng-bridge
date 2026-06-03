"""
路由单元测试
"""
import os
import importlib
import pytest
from fastapi.testclient import TestClient

TEST_KEY = "test-api-key-for-gateway-tests-1234567890"


class TestRouter:
    def setup_method(self):
        os.environ["ZHIBRIDGE_API_KEY"] = TEST_KEY
        import gateway.config as cfg
        importlib.reload(cfg)
        from gateway.app import create_app
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_health_check(self):
        """测试健康检查端点"""
        resp = self.client.get("/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "zhibridge"
        assert data["version"] == "2.1.0"

    def test_missing_api_key(self):
        """测试缺少API Key"""
        resp = self.client.post("/v1/chat/completions", json={})
        assert resp.status_code == 401

    def test_sensitive_backend_unencrypted_rejected(self):
        """敏感后端(linghealth)未加密请求被拒绝"""
        resp = self.client.post(
            "/projects/linghealth/api/v1/records",
            json={"patient_id": "123"},
            headers={"X-API-Key": TEST_KEY},
        )
        assert resp.status_code == 400
        assert resp.json()["error"] == "encryption_required"

    def test_sensitive_backend_encrypted_passes_gateway(self):
        """敏感后端(linghealth)带加密头通过网关鉴权层（后端返回401/200决定最终结果）"""
        resp = self.client.post(
            "/projects/linghealth/api/v1/records",
            json={"ciphertext": "base64encoded"},
            headers={"X-API-Key": TEST_KEY, "X-Encrypted": "true"},
        )
        # 不返回401说明通过网关鉴权+加密检查，具体业务由后端决定
        assert resp.status_code != 400

    def test_sensitive_backend_law_unencrypted_rejected(self):
        """敏感后端(linglaw)未加密请求被拒绝"""
        resp = self.client.post(
            "/projects/linglaw/api/v1/consult",
            json={"question": "contract review"},
            headers={"X-API-Key": TEST_KEY},
        )
        assert resp.status_code == 400
        assert resp.json()["error"] == "encryption_required"

    def test_non_sensitive_backend_passes_without_encryption(self):
        """非敏感后端(lingvision)无需加密即可通过网关鉴权层"""
        resp = self.client.post(
            "/projects/lingvision/api/v1/diagnose",
            json={"image_url": "test"},
            headers={"X-API-Key": TEST_KEY},
        )
        # 不返回400说明不要求加密，具体业务由后端决定
        assert resp.status_code != 400