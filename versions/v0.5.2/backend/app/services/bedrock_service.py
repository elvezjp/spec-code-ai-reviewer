"""AWS Bedrock (Claude) 連携サービス"""

import json
import os
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

from app.models.schemas import ReviewMeta, ReviewResponse
from app.services.llm_service import LLMProvider
from app.services.prompt_builder import (
    build_review_info_markdown,
    build_review_meta,
    build_system_prompt,
    build_user_message,
)

if TYPE_CHECKING:
    from app.models.schemas import LLMConfig, ReviewRequest

# デフォルト設定（システムLLM用）
DEFAULT_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
DEFAULT_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0"
)
DEFAULT_MAX_TOKENS = int(os.environ.get("BEDROCK_MAX_TOKENS", "16384"))


class BedrockProvider(LLMProvider):
    """AWS Bedrock プロバイダー

    システムLLM（環境変数で設定）またはユーザー指定の認証情報を使用して
    AWS Bedrock APIを呼び出す。
    """

    def __init__(self, llm_config: "LLMConfig | None" = None):
        """BedrockProviderを初期化する

        Args:
            llm_config: LLM設定。Noneの場合はシステムLLM（環境変数）を使用。
        """
        if llm_config:
            # ユーザー指定の認証情報を使用
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=llm_config.region or DEFAULT_REGION,
                aws_access_key_id=llm_config.accessKeyId,
                aws_secret_access_key=llm_config.secretAccessKey,
            )
            self._model_id = llm_config.model
            self._max_tokens = llm_config.maxTokens
        else:
            # システムLLM（環境変数から）
            self._client = boto3.client("bedrock-runtime", region_name=DEFAULT_REGION)
            self._model_id = DEFAULT_MODEL_ID
            self._max_tokens = DEFAULT_MAX_TOKENS

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

        # リクエストボディ
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self._max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }

        try:
            response = self._client.invoke_model(
                modelId=self._model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read())
            llm_output = response_body["content"][0]["text"]

            # トークン数を取得
            usage = response_body.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

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

        最小限のトークン（max_tokens=1）でAPIを呼び出し、
        認証情報の有効性を検証する。

        Returns:
            dict: {"status": "connected"} または {"status": "error", "error": "..."}
        """
        try:
            # 最小限のトークンでAPIを呼び出して接続確認
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "test"}],
            }
            self._client.invoke_model(
                modelId=self._model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )
            return {"status": "connected"}
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            return {"status": "error", "error": f"{error_code}: {error_message}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
