"""LLMプロバイダー抽象化レイヤー

マルチプロバイダー対応（Bedrock / Anthropic / OpenAI）のための
抽象インターフェースとプロバイダー選択ロジックを提供する。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.schemas import LLMConfig, ReviewRequest, ReviewResponse


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


def get_llm_provider(llm_config: "LLMConfig | None") -> LLMProvider:
    """LLMConfigに基づいて適切なプロバイダーを返す

    Args:
        llm_config: LLM設定。Noneの場合はシステムLLM（Bedrock）を使用。

    Returns:
        LLMProvider: プロバイダーインスタンス

    Raises:
        ValueError: 未知のプロバイダーが指定された場合
    """
    # 循環インポートを避けるためにここでインポート
    from app.services.anthropic_service import AnthropicProvider
    from app.services.bedrock_service import BedrockProvider
    from app.services.openai_service import OpenAIProvider

    if llm_config is None:
        # システムLLM（環境変数で設定されたBedrock）を使用
        return BedrockProvider()

    if llm_config.provider == "anthropic":
        return AnthropicProvider(llm_config)
    elif llm_config.provider == "openai":
        return OpenAIProvider(llm_config)
    elif llm_config.provider == "bedrock":
        return BedrockProvider(llm_config)
    else:
        raise ValueError(f"Unknown provider: {llm_config.provider}")
