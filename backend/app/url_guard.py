"""LLM 接続先 URL の検証（SSRF 対策）。

`baseUrl` は OpenAI 互換 API に接続するための正規の設定項目だが、
API が認証なしで公開されているため、値を検証しないと、この
サーバーを踏み台にして到達先を任意に指定できてしまう。特にクラウド上では
インスタンスメタデータ（169.254.169.254）から資格情報を読み出す経路になる。

ここでは名前解決した上で、内部向けアドレスへの接続を既定で拒否する。
ローカル LLM をあえて使う構成のために、環境変数での明示的な許可を用意する。
"""

from __future__ import annotations

import ipaddress
import os
import socket
from urllib.parse import urlparse

#: 内部アドレスへの接続を許可する環境変数。ローカル LLM 利用時に設定する。
ALLOW_PRIVATE_ENV = "LLM_ALLOW_PRIVATE_BASE_URL"

_TRUTHY = {"1", "true", "yes", "on"}


def allow_private_targets() -> bool:
    """内部アドレスへの接続が明示的に許可されているか。"""
    return os.getenv(ALLOW_PRIVATE_ENV, "").strip().lower() in _TRUTHY


def _is_internal(address: str) -> bool:
    """内部向け（外部から到達すべきでない）アドレスかどうか。"""
    ip = ipaddress.ip_address(address)
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local  # 169.254.0.0/16: クラウドのメタデータ
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def validate_llm_base_url(base_url: str | None) -> None:
    """`baseUrl` を検証する。問題があれば ValueError を送出する。

    未指定（None・空文字）は各プロバイダーの既定エンドポイントを使う意味なので
    許可する。
    """
    if not base_url or not base_url.strip():
        return

    parsed = urlparse(base_url.strip())

    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            "baseUrl は http または https で指定してください"
            f"（指定値のスキーム: {parsed.scheme or '未指定'}）"
        )

    host = parsed.hostname
    if not host:
        raise ValueError("baseUrl にホスト名が含まれていません")

    if allow_private_targets():
        return

    try:
        resolved = socket.getaddrinfo(host, parsed.port or 0, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        # 解決できない宛先は許可しない（fail closed）
        raise ValueError(f"baseUrl のホスト名を解決できません: {host}") from exc

    for info in resolved:
        address = info[4][0]
        if _is_internal(address):
            raise ValueError(
                "baseUrl に内部ネットワーク宛のアドレスは指定できません"
                f"（{host} -> {address}）。ローカルの LLM に接続する場合は "
                f"環境変数 {ALLOW_PRIVATE_ENV}=1 を設定してください。"
            )
