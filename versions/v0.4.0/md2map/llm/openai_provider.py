"""OpenAI プロバイダー"""

from md2map.llm.base_provider import BaseLLMProvider
from md2map.llm.config import LLMConfig


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API を使用する LLM プロバイダー"""

    def __init__(self, config: LLMConfig) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI provider requires 'openai' package. "
                "Install with: pip install md2map[ai]"
            ) from exc

        self._model = config.model
        self._max_tokens = config.max_tokens
        self._client = OpenAI(api_key=config.api_key)

    def send_message(self, system_prompt: str, user_message: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=self._max_tokens,
        )
        if not response.choices or not response.choices[0].message.content:
            raise RuntimeError("OpenAI API returned empty response")
        return response.choices[0].message.content
