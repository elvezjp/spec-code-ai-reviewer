"""baseUrl 検証（SSRF 対策）のテスト。

この API は認証なしで公開されるため、baseUrl を検証しないと、
サーバーを踏み台にして内部ネットワークやクラウドのメタデータ
エンドポイントへ到達できてしまう。
"""

import socket

import pytest

from app.models.schemas import LLMConfig
from app.url_guard import ALLOW_PRIVATE_ENV, validate_llm_base_url

# 実 DNS を引かないよう、遮断対象はリテラル IP で指定する
BLOCKED_URLS = [
    "http://169.254.169.254/latest/meta-data/",  # クラウドのメタデータ
    "http://127.0.0.1:8000/v1",  # ループバック
    "http://10.0.0.5/v1",  # プライベート
    "http://192.168.1.10/v1",  # プライベート
    "http://172.16.0.1/v1",  # プライベート
    "http://[::1]:8000/v1",  # IPv6 ループバック
    "http://0.0.0.0/v1",  # 未指定アドレス
]


@pytest.fixture(autouse=True)
def _deny_private_by_default(monkeypatch):
    monkeypatch.delenv(ALLOW_PRIVATE_ENV, raising=False)


class TestBlockedTargets:
    @pytest.mark.parametrize("url", BLOCKED_URLS)
    def test_internal_addresses_are_rejected(self, url):
        with pytest.raises(ValueError, match="内部ネットワーク"):
            validate_llm_base_url(url)

    @pytest.mark.parametrize("url", ["file:///etc/passwd", "gopher://x/1", "ftp://x/"])
    def test_non_http_schemes_are_rejected(self, url):
        with pytest.raises(ValueError, match="http"):
            validate_llm_base_url(url)

    def test_missing_host_is_rejected(self):
        with pytest.raises(ValueError, match="ホスト名"):
            validate_llm_base_url("http:///v1")

    def test_unresolvable_host_is_rejected(self, monkeypatch):
        """解決できない宛先は許可しない（fail closed）。"""

        def _fail(*args, **kwargs):
            raise socket.gaierror("not resolvable")

        monkeypatch.setattr(socket, "getaddrinfo", _fail)
        with pytest.raises(ValueError, match="解決できません"):
            validate_llm_base_url("https://nonexistent.invalid/v1")


class TestAllowedTargets:
    @pytest.mark.parametrize("value", [None, "", "   "])
    def test_unset_is_allowed(self, value):
        """未指定は各プロバイダーの既定エンドポイントを使う意味なので許可。"""
        validate_llm_base_url(value)

    def test_public_host_is_allowed(self, monkeypatch):
        def _public(*args, **kwargs):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]

        monkeypatch.setattr(socket, "getaddrinfo", _public)
        validate_llm_base_url("https://api.moonshot.cn/v1")

    @pytest.mark.parametrize("url", BLOCKED_URLS)
    def test_env_var_opts_into_private(self, monkeypatch, url):
        """ローカル LLM 利用時は明示的に許可できる。"""
        monkeypatch.setenv(ALLOW_PRIVATE_ENV, "1")
        validate_llm_base_url(url)

    def test_env_var_false_still_blocks(self, monkeypatch):
        monkeypatch.setenv(ALLOW_PRIVATE_ENV, "0")
        with pytest.raises(ValueError):
            validate_llm_base_url("http://127.0.0.1:8000/v1")


class TestLLMConfigIntegration:
    """モデル側で検証しているので、どの経路から来ても塞がれる。"""

    def test_config_rejects_internal_base_url(self):
        with pytest.raises(ValueError, match="内部ネットワーク"):
            LLMConfig(
                provider="openai",
                model="gpt-4",
                apiKey="sk-test",
                baseUrl="http://169.254.169.254/latest/meta-data/",
            )

    def test_config_without_base_url_is_unaffected(self):
        config = LLMConfig(provider="openai", model="gpt-4", apiKey="sk-test")
        assert config.baseUrl is None

    def test_config_accepts_public_base_url(self, monkeypatch):
        def _public(*args, **kwargs):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]

        monkeypatch.setattr(socket, "getaddrinfo", _public)
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            apiKey="sk-test",
            baseUrl="https://api.moonshot.cn/v1",
        )
        assert config.baseUrl == "https://api.moonshot.cn/v1"
