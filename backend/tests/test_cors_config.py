"""CORS 設定のテスト。

オリジンを限定していない状態で認証情報を許可すると、Starlette は
Access-Control-Allow-Origin にリクエスト元 Origin をそのまま返す。
その結果、任意のサイトがこの API に資格情報付きで到達し、応答を
読めてしまうため、全許可時は認証情報を許可しないことを検証する。
"""

import importlib

import pytest
from fastapi.testclient import TestClient

EVIL_ORIGIN = "https://evil.example.com"


def _load_app(monkeypatch, cors_origins: str | None):
    """CORS_ORIGINS を差し替えて app モジュールを読み直す。"""
    if cors_origins is None:
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("CORS_ORIGINS", cors_origins)
    import app.main

    return importlib.reload(app.main).app


class TestCorsCredentials:
    def test_wildcard_does_not_allow_credentials(self, monkeypatch):
        """既定（全許可）では認証情報を許可しない。"""
        client = TestClient(_load_app(monkeypatch, None))
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
