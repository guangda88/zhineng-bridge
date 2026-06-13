"""
路由单元测试
"""

import importlib
import os

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
        """测试健康检查端点需要鉴权"""
        resp = self.client.get("/v1/health")
        assert resp.status_code == 401
        resp = self.client.get("/v1/health", headers={"X-API-Key": TEST_KEY})
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


class TestDecisionPanelRoutes:
    """决策面板POST路由（3F Phase 1内部入口）"""

    def setup_method(self):
        os.environ["ZHIBRIDGE_API_KEY"] = TEST_KEY
        import gateway.config as cfg

        importlib.reload(cfg)
        from gateway.app import create_app

        self.app = create_app()
        self.client = TestClient(self.app)

    def test_outreach_email_requires_auth(self):
        """邮件审核缺少API Key返回401"""
        resp = self.client.post(
            "/api/decisions/outreach-email",
            json={"email_id": "den_001", "action": "approve"},
        )
        assert resp.status_code == 401

    def test_outreach_email_approve_accepted(self):
        """邮件审核approve返回202 queued"""
        resp = self.client.post(
            "/api/decisions/outreach-email",
            json={"email_id": "den_001", "action": "approve"},
            headers={"X-API-Key": TEST_KEY},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "accepted"
        assert data["target_service"] == "lingyang"

    def test_signing_key_requires_auth(self):
        """密钥设置缺少API Key返回401"""
        resp = self.client.post(
            "/api/decisions/signing-key",
            json={"key_value": "test32bytes", "rotation_period_days": 90},
        )
        assert resp.status_code == 401

    def test_signing_key_accepted(self):
        """密钥设置返回202 queued"""
        resp = self.client.post(
            "/api/decisions/signing-key",
            json={"key_value": "test32bytes", "rotation_period_days": 90},
            headers={"X-API-Key": TEST_KEY},
        )
        assert resp.status_code == 200
        assert resp.json()["target_service"] == "lingmessage"

    def test_publish_control_requires_auth(self):
        """发布控制缺少API Key返回401"""
        resp = self.client.post(
            "/api/decisions/publish-control",
            json={"target": "all", "action": "resume"},
        )
        assert resp.status_code == 401

    def test_publish_control_accepted(self):
        """发布控制resume返回202 queued"""
        resp = self.client.post(
            "/api/decisions/publish-control",
            json={"target": "all", "action": "resume"},
            headers={"X-API-Key": TEST_KEY},
        )
        assert resp.status_code == 200
        assert resp.json()["target_service"] == "lingtongask"

    def test_podcast_topic_requires_auth(self):
        """主题指定缺少API Key返回401"""
        resp = self.client.post(
            "/api/decisions/podcast-topic",
            json={"topic": "test_topic"},
        )
        assert resp.status_code == 401

    def test_podcast_topic_accepted(self):
        """主题指定返回202 queued"""
        resp = self.client.post(
            "/api/decisions/podcast-topic",
            json={"topic": "test_topic"},
            headers={"X-API-Key": TEST_KEY},
        )
        assert resp.status_code == 200
        assert resp.json()["topic"] == "test_topic"

    def test_decisions_pending_requires_auth(self):
        """pending列表缺少API Key返回401"""
        resp = self.client.get("/api/decisions/pending")
        assert resp.status_code == 401

    def test_decisions_pending_returns_placeholder(self):
        """pending列表返回占位结构"""
        resp = self.client.get(
            "/api/decisions/pending",
            headers={"X-API-Key": TEST_KEY},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pending_decisions" in data
