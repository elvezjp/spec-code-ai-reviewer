"""bedrock_service.py の単体テスト

BedrockProviderクラスのテスト。
プロンプト組み立て等の共通ロジックはtest_prompt_builder.pyでテストする。

テストケース:
- UT-BED-PROVIDER-001: BedrockProvider初期化（システムLLM）
- UT-BED-PROVIDER-002: BedrockProvider初期化（ユーザー指定）
- UT-BED-PROVIDER-003: test_connection() - 正常な接続
- UT-BED-PROVIDER-004: execute_review() - 正常なリクエスト（モック）
"""

from unittest.mock import MagicMock, patch

import pytest

from app.models.schemas import LLMConfig, SystemPrompt
from app.services.bedrock_service import BedrockProvider


class TestBedrockProviderInit:
    """BedrockProvider初期化のテスト"""

    @patch("app.services.bedrock_service.boto3")
    def test_ut_bed_provider_001_system_llm(self, mock_boto3):
        """UT-BED-PROVIDER-001: システムLLM使用時（llmConfig=None）"""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        provider = BedrockProvider()

        assert provider.provider_name == "bedrock"
        assert provider.model_id is not None
        mock_boto3.client.assert_called_once()

    @patch("app.services.bedrock_service.boto3")
    def test_ut_bed_provider_002_user_config(self, mock_boto3):
        """UT-BED-PROVIDER-002: ユーザー指定設定"""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        config = LLMConfig(
            provider="bedrock",
            model="anthropic.claude-4-5-sonnet-20241022-v2:0",
            accessKeyId="test-access-key",
            secretAccessKey="test-secret-key",
            region="us-east-1",
            maxTokens=8192,
        )

        provider = BedrockProvider(config)

        assert provider.provider_name == "bedrock"
        assert provider.model_id == "anthropic.claude-4-5-sonnet-20241022-v2:0"
        assert provider._max_tokens == 8192
        mock_boto3.client.assert_called_once_with(
            "bedrock-runtime",
            region_name="us-east-1",
            aws_access_key_id="test-access-key",
            aws_secret_access_key="test-secret-key",
        )


class TestBedrockProviderTestConnection:
    """BedrockProvider.test_connection()のテスト"""

    @patch("app.services.bedrock_service.boto3")
    def test_ut_bed_provider_003_connection_success(self, mock_boto3):
        """UT-BED-PROVIDER-003: 正常な接続（invoke_modelでAPIを呼び出して確認）"""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        # invoke_modelが正常に返る
        mock_client.invoke_model.return_value = {}

        provider = BedrockProvider()

        result = provider.test_connection()

        assert result["status"] == "connected"
        assert "error" not in result
        # invoke_modelが呼び出されたことを確認
        mock_client.invoke_model.assert_called_once()

    @patch("app.services.bedrock_service.boto3")
    def test_connection_failure_client_error(self, mock_boto3):
        """接続失敗時（ClientError）"""
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        # invoke_modelでClientErrorを発生させる
        mock_client.invoke_model.side_effect = ClientError(
            error_response={
                "Error": {
                    "Code": "UnrecognizedClientException",
                    "Message": "The security token included in the request is invalid.",
                }
            },
            operation_name="InvokeModel",
        )

        provider = BedrockProvider()

        result = provider.test_connection()

        assert result["status"] == "error"
        assert "UnrecognizedClientException" in result["error"]
        assert "security token" in result["error"]

    @patch("app.services.bedrock_service.boto3")
    def test_connection_failure_general_exception(self, mock_boto3):
        """接続失敗時（一般的な例外）"""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        # invoke_modelで一般的な例外を発生させる
        mock_client.invoke_model.side_effect = Exception("Connection failed")

        provider = BedrockProvider()

        result = provider.test_connection()

        assert result["status"] == "error"
        assert "Connection failed" in result["error"]


class TestBedrockProviderExecuteReview:
    """BedrockProvider.execute_review()のテスト（モック使用）"""

    @patch("app.services.bedrock_service.boto3")
    def test_ut_bed_provider_004_execute_review_success(self, mock_boto3):
        """UT-BED-PROVIDER-004: 正常なリクエスト"""
        import json

        # モックの設定
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_response_body = MagicMock()
        mock_response_body.read.return_value = json.dumps(
            {
                "content": [{"text": "## レビュー結果\n問題ありません。"}],
                "usage": {"input_tokens": 1000, "output_tokens": 200},
            }
        ).encode()
        mock_client.invoke_model.return_value = {"body": mock_response_body}

        provider = BedrockProvider()

        # ReviewRequestのモック
        mock_request = MagicMock()
        mock_request.systemPrompt = SystemPrompt(
            role="レビュアー",
            purpose="設計書とコードの突合",
            format="マークダウン",
            notes="注意事項",
        )
        mock_request.specMarkdown = None
        mock_request.specFilename = None
        mock_request.codeWithLineNumbers = None
        mock_request.codeFilename = None
        mock_request.executedAt = "2024/12/21 14:30"
        mock_request.get_design_blocks.return_value = [
            {"filename": "spec.xlsx", "content": "# 仕様", "isMain": True, "type": "設計書"}
        ]
        mock_request.get_code_blocks.return_value = [
            {"filename": "main.py", "contentWithLineNumbers": "   1: code"}
        ]

        result = provider.execute_review(mock_request, "v0.4.0")

        assert result.success is True
        assert result.report is not None
        assert "問題ありません" in result.report
        assert result.reviewMeta is not None
        assert result.reviewMeta.provider == "bedrock"
        assert result.reviewMeta.inputTokens == 1000
        assert result.reviewMeta.outputTokens == 200

    @patch("app.services.bedrock_service.boto3")
    def test_execute_review_client_error(self, mock_boto3):
        """ClientError時"""
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.invoke_model.side_effect = ClientError(
            error_response={
                "Error": {
                    "Code": "ValidationException",
                    "Message": "Invalid model ID",
                }
            },
            operation_name="InvokeModel",
        )

        provider = BedrockProvider()

        mock_request = MagicMock()
        mock_request.systemPrompt = SystemPrompt(
            role="レビュアー",
            purpose="設計書とコードの突合",
            format="マークダウン",
            notes="注意事項",
        )
        mock_request.specMarkdown = None
        mock_request.specFilename = None
        mock_request.codeWithLineNumbers = None
        mock_request.codeFilename = None
        mock_request.get_design_blocks.return_value = [
            {"filename": "spec.xlsx", "content": "# 仕様", "isMain": True}
        ]
        mock_request.get_code_blocks.return_value = [
            {"filename": "main.py", "contentWithLineNumbers": "   1: code"}
        ]

        result = provider.execute_review(mock_request, "v0.4.0")

        assert result.success is False
        assert "ValidationException" in result.error
