"""ヘルスチェックAPIのテスト

テストケース:
- UT-HLT-001: GET /api/health - 正常レスポンス
- UT-HLT-002: GET /health - 正常レスポンス（既存互換）
- UT-HLT-003: 両エンドポイントが同一レスポンスを返すこと
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthAPI:
    def test_ut_hlt_001_api_health(self):
        """UT-HLT-001: GET /api/health が正常レスポンスを返す"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_ut_hlt_002_root_health(self):
        """UT-HLT-002: GET /health が正常レスポンスを返す（既存互換）"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_ut_hlt_003_same_response(self):
        """UT-HLT-003: 両エンドポイントが同一レスポンスを返す"""
        response_api = client.get("/api/health")
        response_root = client.get("/health")
        assert response_api.json() == response_root.json()
