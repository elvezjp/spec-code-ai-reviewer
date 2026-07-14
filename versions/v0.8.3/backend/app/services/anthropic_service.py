"""Anthropic API 連携サービス"""

import logging
from typing import TYPE_CHECKING

from anthropic import Anthropic, APIError, AuthenticationError

from app.models.schemas import LLMConfig, ReviewResponse
from app.services.llm_service import LLMProvider

if TYPE_CHECKING:
    from app.models.schemas import ReviewRequest

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic API プロバイダー

    ユーザー指定のAPIキーを使用してAnthropic APIを呼び出す。

    プロンプトキャッシュ:
        system・ユーザーメッセージ末尾に cache_control を付与する。
        一括レビューは同一入力で2回実行されるため、2回目はキャッシュが
        効いて入力コストが大幅に削減される（プレフィックス一致が条件）。
        最小キャッシュ対象トークン数未満の入力ではキャッシュされないが
        エラーにはならない。
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

    def _create_message(self, system_prompt: str, user_message: str):
        """cache_control 付きで messages.create を呼び出す

        system とユーザーメッセージをブロック形式にし、それぞれの末尾に
        cache_control を付与する。プロンプト全体（system + user）が
        キャッシュ対象のプレフィックスになる。
        """
        return self._client.messages.create(
            model=self._model_id,
            max_tokens=self._max_tokens,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_message,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                }
            ],
        )

    @staticmethod
    def _input_tokens_with_cache(usage) -> int:
        """キャッシュ分を含めた実効入力トークン数を返し、キャッシュ状況をログ出力する

        usage.input_tokens はキャッシュ対象外の残り部分のみのため、
        cache_creation / cache_read を合算して総入力トークン数とする。
        """
        cache_creation = getattr(usage, "cache_creation_input_tokens", 0) or 0
        cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        logger.info(
            "Anthropic prompt cache: creation=%d, read=%d, uncached=%d",
            cache_creation,
            cache_read,
            usage.input_tokens,
        )
        return usage.input_tokens + cache_creation + cache_read

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
            response = self._create_message(system_prompt, user_message)

            return self._build_success_response(
                request=request,
                version=version,
                llm_output=response.content[0].text,
                input_tokens=self._input_tokens_with_cache(response.usage),
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

    def send_message(
        self, system_prompt: str, user_message: str
    ) -> tuple[str, int, int]:
        try:
            response = self._create_message(system_prompt, user_message)
            return (
                response.content[0].text,
                self._input_tokens_with_cache(response.usage),
                response.usage.output_tokens,
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic API エラー: {str(e)}") from e

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
            response = self._create_message(system_prompt, user_message)
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Markdown整理中にエラーが発生しました: {str(e)}") from e
