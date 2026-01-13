"""AWS Bedrock 連携サービス

Converse APIを使用してAnthropicおよびAmazon Novaモデルに対応。
"""

from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

from app.models.schemas import LLMConfig, ReviewMeta, ReviewResponse
from app.services.llm_service import LLMProvider
from app.services.prompt_builder import (
    build_review_info_markdown,
    build_review_meta,
    build_system_prompt,
    build_user_message,
)

if TYPE_CHECKING:
    from app.models.schemas import ReviewRequest

# IAMロール認証時のデフォルトリージョン
_DEFAULT_REGION = "ap-northeast-1"


class BedrockProvider(LLMProvider):
    """AWS Bedrock プロバイダー

    Converse APIを使用してAnthropicおよびAmazon Novaモデルに対応。
    """

    def __init__(self, llm_config: LLMConfig):
        """BedrockProviderを初期化する

        Args:
            llm_config: LLM設定（必須）

        Note:
            accessKeyId/secretAccessKeyがNoneの場合はIAMロール認証を使用する。
            これはシステムLLM（EC2/Lambda等で実行）の場合に該当する。
        """
        region = llm_config.region or _DEFAULT_REGION

        # accessKeyId/secretAccessKeyがNoneの場合はIAMロール認証
        if llm_config.accessKeyId and llm_config.secretAccessKey:
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=region,
                aws_access_key_id=llm_config.accessKeyId,
                aws_secret_access_key=llm_config.secretAccessKey,
            )
        else:
            # IAMロール認証（システムLLM用）
            self._client = boto3.client("bedrock-runtime", region_name=region)

        self._model_id = llm_config.model
        self._max_tokens = llm_config.maxTokens

    @property
    def provider_name(self) -> str:
        return "bedrock"

    @property
    def model_id(self) -> str:
        return self._model_id

    def execute_review(
        self,
        request: "ReviewRequest",
        version: str,
    ) -> ReviewResponse:
        """Bedrock APIを呼び出してレビューを実行する

        Args:
            request: レビューリクエスト
            version: アプリケーションのバージョン番号

        Returns:
            ReviewResponse: レビュー結果

        Raises:
            RuntimeError: Bedrock API呼び出しに失敗した場合
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
            # Converse APIを使用（Anthropic/Amazon Nova両対応）
            response = self._client.converse(
                modelId=self._model_id,
                messages=[{
                    "role": "user",
                    "content": [{"text": user_message}],
                }],
                system=[{"text": system_prompt}],
                inferenceConfig={"maxTokens": self._max_tokens},
            )

            llm_output = response["output"]["message"]["content"][0]["text"]

            # トークン数を取得
            usage = response.get("usage", {})
            input_tokens = usage.get("inputTokens", 0)
            output_tokens = usage.get("outputTokens", 0)

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

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            return ReviewResponse(
                success=False,
                error=f"Bedrock API エラー ({error_code}): {error_message}",
            )
        except Exception as e:
            return ReviewResponse(
                success=False,
                error=f"レビュー実行中にエラーが発生しました: {str(e)}",
            )

    def test_connection(self) -> dict:
        """Bedrock接続状態を確認する

        最小限のトークン（maxTokens=1）でConverse APIを呼び出し、
        認証情報の有効性を検証する。

        Returns:
            dict: {"status": "connected"} または {"status": "error", "error": "..."}
        """
        try:
            # Converse APIで接続確認（Anthropic/Amazon Nova両対応）
            self._client.converse(
                modelId=self._model_id,
                messages=[{
                    "role": "user",
                    "content": [{"text": "test"}],
                }],
                inferenceConfig={"maxTokens": 1},
            )
            return {"status": "connected"}
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            return {"status": "error", "error": f"{error_code}: {error_message}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
