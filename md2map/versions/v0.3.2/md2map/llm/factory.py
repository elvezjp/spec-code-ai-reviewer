"""LLM プロバイダーファクトリ"""

import os
from typing import Optional

from md2map.llm.base_provider import BaseLLMProvider
from md2map.llm.config import LLMConfig


def get_llm_provider(config: LLMConfig) -> BaseLLMProvider:
    """LLMConfig に基づいて適切なプロバイダーを返す

    Args:
        config: LLM 設定

    Returns:
        BaseLLMProvider インスタンス

    Raises:
        ValueError: 未知のプロバイダーが指定された場合
    """
    # 循環インポートを避けるためにここでインポート
    from md2map.llm.anthropic_provider import AnthropicProvider
    from md2map.llm.bedrock_provider import BedrockProvider
    from md2map.llm.openai_provider import OpenAIProvider

    if config.provider == "openai":
        return OpenAIProvider(config)
    elif config.provider == "anthropic":
        return AnthropicProvider(config)
    elif config.provider == "bedrock":
        return BedrockProvider(config)
    else:
        raise ValueError(f"Unknown provider: {config.provider}")


def build_llm_config_from_env(
    provider: str = "bedrock",
    model: Optional[str] = None,
    region: Optional[str] = None,
) -> LLMConfig:
    """環境変数から LLMConfig を構築する（CLI / 後方互換用）

    Args:
        provider: プロバイダー名
        model: モデルID（未指定時は環境変数またはデフォルト値）
        region: リージョン（Bedrock 用）

    Returns:
        LLMConfig インスタンス

    Raises:
        RuntimeError: 必要な環境変数が設定されていない場合
    """
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OpenAI provider requires OPENAI_API_KEY environment variable."
            )
        resolved_model = (
            model
            or os.getenv("MD2MAP_AI_MODEL")
            or os.getenv("OPENAI_MODEL")
            or "gpt-4o-mini"
        )
        return LLMConfig(provider="openai", model=resolved_model, api_key=api_key)

    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Anthropic provider requires ANTHROPIC_API_KEY environment variable."
            )
        resolved_model = (
            model
            or os.getenv("MD2MAP_AI_MODEL")
            or "claude-haiku-4-5-20251001"
        )
        return LLMConfig(provider="anthropic", model=resolved_model, api_key=api_key)

    elif provider == "bedrock":
        resolved_region = region or os.getenv("AWS_REGION", "ap-northeast-1")
        resolved_model = (
            model
            or os.getenv("MD2MAP_AI_MODEL")
            or "global.anthropic.claude-haiku-4-5-20251001-v1:0"
        )
        return LLMConfig(
            provider="bedrock",
            model=resolved_model,
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region=resolved_region,
        )

    else:
        raise ValueError(f"Unknown provider: {provider}")
