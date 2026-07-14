"""v0.8.3 セキュリティ修正のテスト

- CORS: 未設定時は開発用オリジンのみ許可（全許可デフォルトの廃止）
- アップロードファイル名のサニタイズ（パストラバーサル防止）
"""

from fastapi.testclient import TestClient

from app.main import app
from app.routers.split import _safe_filename

client = TestClient(app)


class TestCorsDefaults:
    """CORSデフォルト設定のテスト"""

    def test_dev_origin_allowed(self):
        """未設定時、ローカル開発オリジンは許可される"""
        response = client.options(
            "/api/convert/available-tools",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert (
            response.headers.get("access-control-allow-origin")
            == "http://localhost:5173"
        )

    def test_unknown_origin_not_allowed(self):
        """未設定時、外部オリジンは許可されない（全許可デフォルトの廃止）"""
        response = client.options(
            "/api/convert/available-tools",
            headers={
                "Origin": "https://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" not in response.headers


class TestSafeFilename:
    """_safe_filename() のテスト"""

    def test_plain_filename(self):
        assert _safe_filename("design.md", "input.md") == "design.md"

    def test_path_traversal_removed(self):
        assert _safe_filename("../../etc/passwd", "input.md") == "passwd"

    def test_absolute_path_removed(self):
        assert _safe_filename("/tmp/evil.py", "input.txt") == "evil.py"

    def test_none_falls_back_to_default(self):
        assert _safe_filename(None, "input.md") == "input.md"

    def test_empty_after_sanitize_falls_back_to_default(self):
        assert _safe_filename("../", "input.md") == "input.md"


class TestSplitApiWithTraversalFilename:
    """パストラバーサル的なファイル名でも分割APIが安全に処理できる"""

    def test_split_markdown_with_traversal_filename(self):
        response = client.post(
            "/api/split/markdown",
            json={
                "filename": "../../outside.md",
                "content": "# 見出し1\n\n本文です。\n\n## 見出し2\n\n本文2です。\n",
                "maxDepth": 2,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["parts"]) >= 1


class TestHealthCheck:
    """/health エンドポイントのテスト（v0.8.3でマウント順を修正）"""

    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.8.3"
