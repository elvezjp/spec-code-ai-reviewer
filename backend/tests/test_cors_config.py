"""CORS 設定のテスト。

この API は認証がないため、CORS の許可範囲がブラウザ経由の到達可否を
そのまま決める。以下の2点を検証する。

- 既定（CORS_ORIGINS 未設定）ではローカル開発用オリジンのみを許可し、
  任意のサイトからは応答を読めないこと
- 全許可を明示した場合に認証情報を許可しないこと。オリジンを限定して
  いない状態で認証情報を許可すると、Starlette は
  Access-Control-Allow-Origin にリクエスト元 Origin をそのまま返し、
  任意のサイトが資格情報付きで応答を読めてしまう
"""

import importlib

import pytest
from fastapi.testclient import TestClient

EVIL_ORIGIN = "https://evil.example.com"
DEV_ORIGIN = "http://localhost:5173"


def _load_app(monkeypatch, cors_origins: str | None):
    """CORS_ORIGINS を差し替えて app モジュールを読み直す。"""
    if cors_origins is None:
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("CORS_ORIGINS", cors_origins)
    import app.main

    return importlib.reload(app.main).app


class TestCorsDefault:
    """CORS_ORIGINS 未設定時の既定挙動。"""

    def test_default_rejects_arbitrary_origin(self, monkeypatch):
        """既定では任意のサイトに許可を返さない。"""
        client = TestClient(_load_app(monkeypatch, None))
        res = client.get("/health", headers={"Origin": EVIL_ORIGIN})

        assert res.headers.get("access-control-allow-origin") is None

    def test_default_rejects_arbitrary_origin_preflight(self, monkeypatch):
        """プリフライトでも既定で任意のサイトを拒否する。"""
        client = TestClient(_load_app(monkeypatch, None))
        res = client.options(
            "/api/review",
            headers={
                "Origin": EVIL_ORIGIN,
                "Access-Control-Request-Method": "POST",
            },
        )

        assert res.headers.get("access-control-allow-origin") is None

    def test_default_allows_local_dev_origin(self, monkeypatch):
        """既定でローカル開発サーバーからは許可する。"""
        client = TestClient(_load_app(monkeypatch, None))
        res = client.get("/health", headers={"Origin": DEV_ORIGIN})

        assert res.headers.get("access-control-allow-origin") == DEV_ORIGIN
        assert res.headers.get("access-control-allow-credentials") == "true"

    def test_empty_value_is_treated_as_unset(self, monkeypatch):
        """空文字を設定した場合も既定として扱う（全許可に落とさない）。"""
        client = TestClient(_load_app(monkeypatch, "   "))
        res = client.get("/health", headers={"Origin": EVIL_ORIGIN})

        assert res.headers.get("access-control-allow-origin") is None


class TestCorsCredentials:
    def test_wildcard_does_not_allow_credentials(self, monkeypatch):
        """全許可を明示した場合は認証情報を許可しない。"""
        client = TestClient(_load_app(monkeypatch, "*"))
        res = client.get("/health", headers={"Origin": EVIL_ORIGIN})

        assert res.headers.get("access-control-allow-credentials") is None

    def test_wildcard_does_not_echo_arbitrary_origin(self, monkeypatch):
        """全許可時に任意 Origin をそのまま返さない（返すなら '*' のみ）。"""
        client = TestClient(_load_app(monkeypatch, "*"))
        res = client.get("/health", headers={"Origin": EVIL_ORIGIN})

        allow_origin = res.headers.get("access-control-allow-origin")
        assert allow_origin != EVIL_ORIGIN
        assert allow_origin in (None, "*")

    def test_explicit_origin_still_allows_credentials(self, monkeypatch):
        """オリジンを限定していれば認証情報を許可する（既存挙動を維持）。"""
        allowed = "https://app.example.com"
        client = TestClient(_load_app(monkeypatch, allowed))
        res = client.get("/health", headers={"Origin": allowed})

        assert res.headers.get("access-control-allow-origin") == allowed
        assert res.headers.get("access-control-allow-credentials") == "true"

    def test_explicit_origin_rejects_other_origins(self, monkeypatch):
        """限定時に別 Origin へ許可を返さない。"""
        client = TestClient(_load_app(monkeypatch, "https://app.example.com"))
        res = client.get("/health", headers={"Origin": EVIL_ORIGIN})

        assert res.headers.get("access-control-allow-origin") != EVIL_ORIGIN


@pytest.fixture(autouse=True)
def _restore_app_module():
    """他テストへの影響を避けるため、最後に既定状態で読み直す。"""
    yield
    import app.main

    importlib.reload(app.main)
