"""openai_service.py の単体テスト

テストケース:
- UT-OAI-001: invoke() - 正常なリクエスト（モック）
- UT-OAI-002: invoke() - APIキー未設定
- UT-OAI-003: invoke() - 無効なモデルID（モック）
- UT-OAI-004: test_connection() - 正常な接続（モック）
- UT-OAI-005: test_connection() - 接続失敗（モック）
"""

from unittest.mock import MagicMock, patch

import pytest
from openai import APIError, AuthenticationError

from app.models.schemas import LLMConfig, SystemPrompt
from app.services.openai_service import OpenAIProvider


class TestOpenAIProviderInit:
    """OpenAIProvider初期化のテスト"""

    def test_ut_oai_002_no_api_key(self):
        """UT-OAI-002: APIキー未設定でValueError"""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o",
            apiKey=None,
        )

        with pytest.raises(ValueError, match="APIキー"):
            OpenAIProvider(config)

    def test_init_with_valid_config(self):
        """有効な設定で初期化成功"""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o",
            apiKey="test-api-key",
            maxTokens=8192,
        )

        provider = OpenAIProvider(config)

        assert provider.provider_name == "openai"
        assert provider.model_id == "gpt-4o"
        assert provider._max_tokens == 8192


class TestOpenAIProviderTestConnection:
    """OpenAIProvider.test_connection()のテスト"""

    @patch("app.services.openai_service.OpenAI")
    def test_ut_oai_004_connection_success(self, mock_openai_class):
        """UT-OAI-004: 正常な接続"""
        # モックの設定
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock()

        config = LLMConfig(
            provider="openai",
            model="gpt-4o",
            apiKey="test-api-key",
        )
        provider = OpenAIProvider(config)

        result = provider.test_connection()

        assert result["status"] == "connected"
        assert "error" not in result

    @patch("app.services.openai_service.OpenAI")
    def test_ut_oai_005_connection_failure_auth(self, mock_openai_class):
        """UT-OAI-005: 認証失敗"""
        # モックの設定
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = AuthenticationError(
            message="Invalid API Key",
            response=MagicMock(status_code=401),
            body=None,
        )

        config = LLMConfig(
            provider="openai",
            model="gpt-4o",
            apiKey="invalid-api-key",
        )
        provider = OpenAIProvider(config)

        result = provider.test_connection()

        assert result["status"] == "error"
        assert "APIキー" in result["error"]

    @patch("app.services.openai_service.OpenAI")
    def test_connection_failure_api_error(self, mock_openai_class):
        """API エラー時"""
        # モックの設定
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = APIError(
            message="Model not found",
            request=MagicMock(),
            body=None,
        )

        config = LLMConfig(
            provider="openai",
            model="invalid-model",
            apiKey="test-api-key",
        )
        provider = OpenAIProvider(config)

        result = provider.test_connection()

        assert result["status"] == "error"
        assert "Model not found" in result["error"]


class TestOpenAIProviderExecuteReview:
    """OpenAIProvider.execute_review()のテスト（モック使用）"""

    @patch("app.services.openai_service.OpenAI")
    def test_ut_oai_001_execute_review_success(self, mock_openai_class):
        """UT-OAI-001: 正常なリクエスト"""
        # モックの設定
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "## レビュー結果\n問題ありません。"
        mock_response.usage.prompt_tokens = 1000
        mock_response.usage.completion_tokens = 200
        mock_client.chat.completions.create.return_value = mock_response

        config = LLMConfig(
            provider="openai",
            model="gpt-4o",
            apiKey="test-api-key",
        )
        provider = OpenAIProvider(config)

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
        assert result.reviewMeta.provider == "openai"
        assert result.reviewMeta.modelId == "gpt-4o"
        assert result.reviewMeta.inputTokens == 1000
        assert result.reviewMeta.outputTokens == 200

    @patch("app.services.openai_service.OpenAI")
    def test_execute_review_auth_error(self, mock_openai_class):
        """認証エラー時"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = AuthenticationError(
            message="Invalid API Key",
            response=MagicMock(status_code=401),
            body=None,
        )

        config = LLMConfig(
            provider="openai",
            model="gpt-4o",
            apiKey="invalid-api-key",
        )
        provider = OpenAIProvider(config)

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
        assert "認証エラー" in result.error
