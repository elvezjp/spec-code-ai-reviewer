"""LLMプロバイダー抽象化レイヤー

マルチプロバイダー対応（Bedrock / Anthropic / OpenAI）のための
抽象インターフェースとプロバイダー選択ロジックを提供する。
"""

import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.schemas import LLMConfig, ReviewRequest, ReviewResponse

# システムLLM用のデフォルト設定（環境変数から取得）
# 後方互換性のため、既存の環境変数名を維持
_SYSTEM_LLM_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
_SYSTEM_LLM_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0"
)
_SYSTEM_LLM_MAX_TOKENS = int(os.environ.get("BEDROCK_MAX_TOKENS", "16384"))


class LLMProvider(ABC):
    """LLMプロバイダーの抽象基底クラス

    各プロバイダー（Bedrock, Anthropic, OpenAI）はこのクラスを継承し、
    execute_reviewとtest_connectionを実装する。
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """プロバイダー名を返す

        Returns:
            str: プロバイダー名 (bedrock/anthropic/openai)
        """
        pass

    @property
    @abstractmethod
    def model_id(self) -> str:
        """使用するモデルIDを返す

        Returns:
            str: モデルID
        """
        pass

    @abstractmethod
    def execute_review(
        self,
        request: "ReviewRequest",
        version: str,
    ) -> "ReviewResponse":
        """レビューを実行する

        Args:
            request: レビューリクエスト
            version: アプリケーションのバージョン番号

        Returns:
            ReviewResponse: レビュー結果
        """
        pass

    @abstractmethod
    def test_connection(self) -> dict:
        """接続テストを実行する

        Returns:
            dict: {"status": "connected"} または {"status": "error", "error": "エラーメッセージ"}
        """
        pass


def get_system_llm_config() -> "LLMConfig":
    """環境変数からシステムLLM用のLLMConfigを生成する

    現在はBedrockのみサポート。将来的に環境変数で
    プロバイダーを切り替え可能にすることも可能。

    Returns:
        LLMConfig: システムLLM用の設定
    """
    from app.models.schemas import LLMConfig

    return LLMConfig(
        provider="bedrock",
        model=_SYSTEM_LLM_MODEL_ID,
        region=_SYSTEM_LLM_REGION,
        maxTokens=_SYSTEM_LLM_MAX_TOKENS,
        # accessKeyId/secretAccessKey は None（IAMロール認証を使用）
    )


def get_llm_provider(llm_config: "LLMConfig | None") -> LLMProvider:
    """LLMConfigに基づいて適切なプロバイダーを返す

    Args:
        llm_config: LLM設定。Noneの場合はシステムLLMを使用。

    Returns:
        LLMProvider: プロバイダーインスタンス

    Raises:
        ValueError: 未知のプロバイダーが指定された場合
    """
    # 循環インポートを避けるためにここでインポート
    from app.services.anthropic_service import AnthropicProvider
    from app.services.bedrock_service import BedrockProvider
    from app.services.openai_service import OpenAIProvider

    # llm_configがNoneの場合はシステムLLM設定を使用
    if llm_config is None:
        llm_config = get_system_llm_config()

    if llm_config.provider == "anthropic":
        return AnthropicProvider(llm_config)
    elif llm_config.provider == "openai":
        return OpenAIProvider(llm_config)
    elif llm_config.provider == "bedrock":
        return BedrockProvider(llm_config)
    else:
        raise ValueError(f"Unknown provider: {llm_config.provider}")
