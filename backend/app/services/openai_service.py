"""OpenAI API 連携サービス"""

from typing import TYPE_CHECKING

from openai import APIError, AuthenticationError, OpenAI

from app.models.schemas import LLMConfig, ReviewResponse
from app.services.llm_service import LLMProvider

if TYPE_CHECKING:
    from app.models.schemas import ReviewRequest


class OpenAIProvider(LLMProvider):
    """OpenAI API プロバイダー

    ユーザー指定のAPIキーを使用してOpenAI APIを呼び出す。
    baseUrlを指定した場合はOpenAI互換API（Moonshot AI等）に接続する。
    """

    def __init__(self, llm_config: LLMConfig):
        """OpenAIProviderを初期化する

        Args:
            llm_config: LLM設定（apiKeyが必須、baseUrlは任意）

        Raises:
            ValueError: APIキーが指定されていない場合
        """
        if not llm_config.apiKey:
            raise ValueError("OpenAI APIキーが指定されていません")

        self._base_url = llm_config.baseUrl
        if llm_config.baseUrl:
            self._client = OpenAI(
                api_key=llm_config.apiKey, base_url=llm_config.baseUrl
            )
        else:
            self._client = OpenAI(api_key=llm_config.apiKey)
        self._model_id = llm_config.model
        self._max_tokens = llm_config.maxTokens

    def _create_chat_completion(self, messages: list[dict], max_tokens: int):
        """Chat Completions APIを呼び出す

        OpenAI互換APIにはmax_completion_tokens未対応のものがあるため、
        baseUrl指定時は従来のmax_tokensパラメータを使用する。
        """
        if self._base_url:
            return self._client.chat.completions.create(
                model=self._model_id,
                max_tokens=max_tokens,
                messages=messages,
            )
        return self._client.chat.completions.create(
            model=self._model_id,
            max_completion_tokens=max_tokens,
            messages=messages,
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_id(self) -> str:
        return self._model_id

    def execute_review(
        self,
        request: "ReviewRequest",
        version: str,
    ) -> ReviewResponse:
        """OpenAI APIを呼び出してレビューを実行する

        Args:
            request: レビューリクエスト
            version: アプリケーションのバージョン番号

        Returns:
            ReviewResponse: レビュー結果
        """
        system_prompt, user_message = self._build_prompts(request)

        try:
            response = self._create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=self._max_tokens,
            )

            usage = response.usage

            return self._build_success_response(
                request=request,
                version=version,
                llm_output=response.choices[0].message.content or "",
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
            )

        except AuthenticationError:
            return self._build_error_response(
                "OpenAI API 認証エラー: APIキーが無効です"
            )
        except APIError as e:
            return self._build_error_response(f"OpenAI API エラー: {e.message}")
        except Exception as e:
            return self._build_error_response(
                f"レビュー実行中にエラーが発生しました: {str(e)}"
            )

    def send_message(
        self, system_prompt: str, user_message: str
    ) -> tuple[str, int, int]:
        try:
            response = self._create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=self._max_tokens,
            )
            usage = response.usage
            return (
                response.choices[0].message.content or "",
                usage.prompt_tokens if usage else 0,
                usage.completion_tokens if usage else 0,
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API エラー: {str(e)}") from e

    def test_connection(self) -> dict:
        """OpenAI API接続状態を確認する

        Returns:
            dict: {"status": "connected"} または {"status": "error", "error": "..."}
        """
        try:
            # 最小限のトークンでAPIを呼び出して接続確認
            # GPT-5.2系は出力トークン数が少なすぎるとエラーになるため、余裕を持たせる
            self._create_chat_completion(
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=16,
            )
            return {"status": "connected"}
        except AuthenticationError:
            return {"status": "error", "error": "APIキーが無効です"}
        except APIError as e:
            return {"status": "error", "error": e.message}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def organize_markdown(self, markdown: str, policy: str) -> str:
        """OpenAI APIを呼び出してMarkdown整理を実行する"""
        system_prompt, user_message = self._build_markdown_organize_prompts(
            markdown, policy
        )

        try:
            response = self._create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=self._max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"Markdown整理中にエラーが発生しました: {str(e)}") from e
