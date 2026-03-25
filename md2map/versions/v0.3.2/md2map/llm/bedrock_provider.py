"""Amazon Bedrock プロバイダー"""

import json

from md2map.llm.base_provider import BaseLLMProvider
from md2map.llm.config import LLMConfig


class BedrockProvider(BaseLLMProvider):
    """Amazon Bedrock (Claude) を使用する LLM プロバイダー"""

    def __init__(self, config: LLMConfig) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError(
                "Bedrock provider requires 'boto3' package. "
                "Install with: pip install md2map[ai-bedrock]"
            ) from exc

        self._model = config.model
        self._max_tokens = config.max_tokens

        client_kwargs = {
            "service_name": "bedrock-runtime",
        }
        if config.region:
            client_kwargs["region_name"] = config.region
        if config.access_key_id and config.secret_access_key:
            client_kwargs["aws_access_key_id"] = config.access_key_id
            client_kwargs["aws_secret_access_key"] = config.secret_access_key

        self._client = boto3.client(**client_kwargs)

    def send_message(self, system_prompt: str, user_message: str) -> str:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self._max_tokens,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_message},
            ],
        })

        response = self._client.invoke_model(
            modelId=self._model,
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        response_body = json.loads(response["body"].read())
        content = response_body.get("content", [])
        if not content or not content[0].get("text"):
            raise RuntimeError("Bedrock API returned empty response")
        return content[0]["text"]
