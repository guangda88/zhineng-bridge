"""
代理模块单元测试

注：httpx.AsyncClient mock复杂，留待后续集成测试覆盖。
"""
import pytest
from fastapi.testclient import TestClient
from gateway.app import create_app


class TestProxyRoutes:
    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_chat_completions_requires_auth(self):
        """测试chat/completions端点需要鉴权"""
        resp = self.client.post("/v1/chat/completions", json={"prompt": "test"})
        assert resp.status_code == 401

    def test_knowledge_query_requires_auth(self):
        """测试知识查询端点需要鉴权"""
        resp = self.client.post("/api/knowledge/query", json={"query": "test"})
        assert resp.status_code == 401