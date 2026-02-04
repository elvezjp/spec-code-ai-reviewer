"""Anthropic API 連携サービス"""

from typing import TYPE_CHECKING

from anthropic import Anthropic, APIError, AuthenticationError

from app.models.schemas import LLMConfig, ReviewResponse
from app.services.llm_service import LLMProvider

if TYPE_CHECKING:
    from app.models.schemas import ReviewRequest


class AnthropicProvider(LLMProvider):
    """Anthropic API プロバイダー

    ユーザー指定のAPIキーを使用してAnthropic APIを呼び出す。
    """

    def __init__(self, llm_config: LLMConfig):
        """AnthropicProviderを初期化する

        Args:
            llm_config: LLM設定（apiKeyが必須）

        Raises:
            ValueError: APIキーが指定されていない場合
        """
        if not llm_config.apiKey:
            raise ValueError("Anthropic APIキーが指定されていません")

        self._client = Anthropic(api_key=llm_config.apiKey)
        self._model_id = llm_config.model
        self._max_tokens = llm_config.maxTokens

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_id(self) -> str:
        return self._model_id

    def execute_review(
        self,
        request: "ReviewRequest",
        version: str,
    ) -> ReviewResponse:
        """Anthropic APIを呼び出してレビューを実行する

        Args:
            request: レビューリクエスト
            version: アプリケーションのバージョン番号

        Returns:
            ReviewResponse: レビュー結果
        """
        system_prompt, user_message = self._build_prompts(request)

        try:
            response = self._client.messages.create(
                model=self._model_id,
                max_tokens=self._max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            return self._build_success_response(
                request=request,
                version=version,
                llm_output=response.content[0].text,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

        except AuthenticationError:
            return self._build_error_response(
                "Anthropic API 認証エラー: APIキーが無効です"
            )
        except APIError as e:
            return self._build_error_response(f"Anthropic API エラー: {e.message}")
        except Exception as e:
            return self._build_error_response(
                f"レビュー実行中にエラーが発生しました: {str(e)}"
            )

    def test_connection(self) -> dict:
        """Anthropic API接続状態を確認する

        Returns:
            dict: {"status": "connected"} または {"status": "error", "error": "..."}
        """
        try:
            # 最小限のトークンでAPIを呼び出して接続確認
            self._client.messages.create(
                model=self._model_id,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}],
            )
            return {"status": "connected"}
        except AuthenticationError:
            return {"status": "error", "error": "APIキーが無効です"}
        except APIError as e:
            return {"status": "error", "error": e.message}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def organize_markdown(self, markdown: str, policy: str) -> str:
        """Anthropic APIを呼び出してMarkdown整理を実行する"""
        system_prompt, user_message = self._build_markdown_organize_prompts(
            markdown, policy
        )

        try:
            response = self._client.messages.create(
                model=self._model_id,
                max_tokens=self._max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Markdown整理中にエラーが発生しました: {str(e)}") from e
