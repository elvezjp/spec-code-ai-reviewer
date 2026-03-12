"""Anthropic プロバイダー"""

from md2map.llm.base_provider import BaseLLMProvider
from md2map.llm.config import LLMConfig


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API を使用する LLM プロバイダー"""

    def __init__(self, config: LLMConfig) -> None:
        try:
            import anthropic  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "Anthropic provider requires 'anthropic' package. "
                "Install with: pip install md2map[ai-anthropic]"
            ) from exc

        self._model = config.model
        self._max_tokens = config.max_tokens
        self._client = anthropic.Anthropic(api_key=config.api_key)

    def send_message(self, system_prompt: str, user_message: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message},
            ],
        )
        if not response.content or not response.content[0].text:
            raise RuntimeError("Anthropic API returned empty response")
        return response.content[0].text
