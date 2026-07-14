"""AWS Bedrock 連携サービス

Converse APIを使用してAnthropicおよびAmazon Novaモデルに対応。
"""

import logging
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

from app.models.schemas import LLMConfig, ReviewResponse
from app.services.llm_service import LLMProvider

if TYPE_CHECKING:
    from app.models.schemas import ReviewRequest

logger = logging.getLogger(__name__)

# IAMロール認証時のデフォルトリージョン
_DEFAULT_REGION = "ap-northeast-1"

# Converse API のプロンプトキャッシュ用チェックポイントブロック
_CACHE_POINT = {"cachePoint": {"type": "default"}}


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
        # プロンプトキャッシュ非対応モデルを検出した場合に False にする
        self._cache_enabled = True

    @property
    def provider_name(self) -> str:
        return "bedrock"

    @property
    def model_id(self) -> str:
        return self._model_id

    def _converse(self, system_prompt: str, user_message: str) -> dict:
        """cachePoint 付きで Converse API を呼び出す

        system・ユーザーメッセージの末尾に cachePoint を付与する。
        一括レビューは同一入力で2回実行されるため、2回目はキャッシュが
        効いて入力コストが削減される。

        プロンプトキャッシュ非対応モデルでは ValidationException になる
        ため、その場合は cachePoint なしで再試行し、以降の呼び出しでも
        キャッシュを使わない。
        """
        if self._cache_enabled:
            try:
                return self._client.converse(
                    modelId=self._model_id,
                    messages=[{
                        "role": "user",
                        "content": [{"text": user_message}, _CACHE_POINT],
                    }],
                    system=[{"text": system_prompt}, _CACHE_POINT],
                    inferenceConfig={"maxTokens": self._max_tokens},
                )
            except ClientError as e:
                if e.response["Error"]["Code"] != "ValidationException":
                    raise
                # キャッシュ非対応モデルの可能性があるため cachePoint なしで再試行
                logger.info(
                    "Bedrock prompt cache unsupported for %s; retrying without "
                    "cachePoint (%s)",
                    self._model_id,
                    e.response["Error"]["Message"],
                )
                self._cache_enabled = False

        return self._client.converse(
            modelId=self._model_id,
            messages=[{
                "role": "user",
                "content": [{"text": user_message}],
            }],
            system=[{"text": system_prompt}],
            inferenceConfig={"maxTokens": self._max_tokens},
        )

    @staticmethod
    def _input_tokens_with_cache(usage: dict) -> int:
        """キャッシュ分を含めた実効入力トークン数を返し、キャッシュ状況をログ出力する

        Converse API の inputTokens はキャッシュ対象外の残り部分のみのため、
        cacheReadInputTokens / cacheWriteInputTokens を合算して総入力トークン数とする。
        """
        cache_read = usage.get("cacheReadInputTokens", 0)
        cache_write = usage.get("cacheWriteInputTokens", 0)
        uncached = usage.get("inputTokens", 0)
        logger.info(
            "Bedrock prompt cache: write=%d, read=%d, uncached=%d",
            cache_write,
            cache_read,
            uncached,
        )
        return uncached + cache_read + cache_write

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
        system_prompt, user_message = self._build_prompts(request)

        try:
            # Converse APIを使用（Anthropic/Amazon Nova両対応）
            response = self._converse(system_prompt, user_message)

            usage = response.get("usage", {})

            return self._build_success_response(
                request=request,
                version=version,
                llm_output=response["output"]["message"]["content"][0]["text"],
                input_tokens=self._input_tokens_with_cache(usage),
                output_tokens=usage.get("outputTokens", 0),
            )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            return self._build_error_response(
                f"Bedrock API エラー ({error_code}): {error_message}"
            )
        except Exception as e:
            return self._build_error_response(
                f"レビュー実行中にエラーが発生しました: {str(e)}"
            )

    def send_message(
        self, system_prompt: str, user_message: str
    ) -> tuple[str, int, int]:
        try:
            response = self._converse(system_prompt, user_message)
            usage = response.get("usage", {})
            return (
                response["output"]["message"]["content"][0]["text"],
                self._input_tokens_with_cache(usage),
                usage.get("outputTokens", 0),
            )
        except Exception as e:
            raise RuntimeError(f"Bedrock API エラー: {str(e)}") from e

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

    def organize_markdown(self, markdown: str, policy: str) -> str:
        """Bedrock APIを呼び出してMarkdown整理を実行する"""
        system_prompt, user_message = self._build_markdown_organize_prompts(
            markdown, policy
        )

        try:
            response = self._converse(system_prompt, user_message)
            return response["output"]["message"]["content"][0]["text"]
        except Exception as e:
            raise RuntimeError(f"Markdown整理中にエラーが発生しました: {str(e)}") from e
