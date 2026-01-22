"""OpenAI API 連携サービス"""

from typing import TYPE_CHECKING

from openai import APIError, AuthenticationError, OpenAI

from app.models.schemas import LLMConfig, ReviewMeta, ReviewResponse
from app.services.llm_service import LLMProvider
from app.services.prompt_builder import (
    build_review_info_markdown,
    build_review_meta,
    build_system_prompt,
    build_user_message,
)
from app.services.markdown_organizer import (
    build_markdown_organize_system_prompt,
    build_markdown_organize_user_message,
)

if TYPE_CHECKING:
    from app.models.schemas import ReviewRequest


class OpenAIProvider(LLMProvider):
    """OpenAI API プロバイダー

    ユーザー指定のAPIキーを使用してOpenAI APIを呼び出す。
    """

    def __init__(self, llm_config: LLMConfig):
        """OpenAIProviderを初期化する

        Args:
            llm_config: LLM設定（apiKeyが必須）

        Raises:
            ValueError: APIキーが指定されていない場合
        """
        if not llm_config.apiKey:
            raise ValueError("OpenAI APIキーが指定されていません")

        self._client = OpenAI(api_key=llm_config.apiKey)
        self._model_id = llm_config.model
        self._max_tokens = llm_config.maxTokens

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
        # システムプロンプトを組み立て
        system_prompt = build_system_prompt(
            role=request.systemPrompt.role,
            purpose=request.systemPrompt.purpose,
            format=request.systemPrompt.format,
            notes=request.systemPrompt.notes,
        )

        # 設計書とコードのブロックを取得
        designs = request.get_design_blocks()
        codes = request.get_code_blocks()

        # ユーザーメッセージを組み立て
        user_message = build_user_message(
            spec_markdown=request.specMarkdown,
            spec_filename=request.specFilename,
            designs=designs,
            codes=codes,
            legacy_code_with_line_numbers=request.codeWithLineNumbers,
            legacy_code_filename=request.codeFilename,
        )

        try:
            response = self._client.chat.completions.create(
                model=self._model_id,
                max_completion_tokens=self._max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )

            llm_output = response.choices[0].message.content or ""

            # トークン数を取得
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0

            # ReviewMetaを構築
            review_meta_dict = build_review_meta(
                version=version,
                model_id=self._model_id,
                provider=self.provider_name,
                designs=designs,
                codes=codes,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                executed_at=request.executedAt,
            )

            # レビュー情報セクションを構築してLLM出力と結合
            review_info_markdown = build_review_info_markdown(review_meta_dict)
            report = review_info_markdown + llm_output

            # ReviewMetaオブジェクトを作成
            review_meta = ReviewMeta(**review_meta_dict)

            return ReviewResponse(
                success=True,
                report=report,
                reviewMeta=review_meta,
            )

        except AuthenticationError:
            return ReviewResponse(
                success=False,
                error="OpenAI API 認証エラー: APIキーが無効です",
            )
        except APIError as e:
            return ReviewResponse(
                success=False,
                error=f"OpenAI API エラー: {e.message}",
            )
        except Exception as e:
            return ReviewResponse(
                success=False,
                error=f"レビュー実行中にエラーが発生しました: {str(e)}",
            )

    def test_connection(self) -> dict:
        """OpenAI API接続状態を確認する

        Returns:
            dict: {"status": "connected"} または {"status": "error", "error": "..."}
        """
        try:
            # 最小限のトークンでAPIを呼び出して接続確認
            # GPT-5.2系は出力トークン数が少なすぎるとエラーになるため、余裕を持たせる
            self._client.chat.completions.create(
                model=self._model_id,
                max_completion_tokens=16,
                messages=[{"role": "user", "content": "Hi"}],
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
        system_prompt = build_markdown_organize_system_prompt(policy)
        user_message = build_markdown_organize_user_message(markdown)

        try:
            response = self._client.chat.completions.create(
                model=self._model_id,
                max_completion_tokens=self._max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"Markdown整理中にエラーが発生しました: {str(e)}") from e
