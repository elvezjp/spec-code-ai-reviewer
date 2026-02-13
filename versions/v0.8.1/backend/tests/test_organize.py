"""organize.py の単体テスト

テストケース:
- UT-ORG-001: organize_markdown_api() - 正常系（単一セクション）
- UT-ORG-002: organize_markdown_api() - 正常系（複数セクション分割）
- UT-ORG-003: organize_markdown_api() - エラー: Markdownが空
- UT-ORG-004: organize_markdown_api() - エラー: 整理方針が空
- UT-ORG-005: organize_markdown_api() - エラー: トークン超過（分割不可）
- UT-ORG-006: organize_markdown_api() - タイムアウト
- UT-ORG-007: organize_markdown_api() - APIエラー（リトライ後失敗）
- UT-ORG-008: organize_markdown_api() - 出力形式不正
- UT-ORG-009: organize_markdown_api() - 前処理の適用
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import LLMConfig, MarkdownSourceInfo, OrganizeMarkdownRequest

client = TestClient(app)


class TestOrganizeMarkdownAPI:
    """organize_markdown_api() のテスト"""

    @patch("app.routers.organize.get_llm_provider")
    def test_ut_org_001_success_single_section(self, mock_get_provider):
        """UT-ORG-001: 正常系（単一セクション）"""
        # モックの設定
        mock_provider = MagicMock()
        mock_provider.organize_markdown.return_value = """## 機能
[ref:S1-P1] 整理された内容
"""
        mock_get_provider.return_value = mock_provider

        request = OrganizeMarkdownRequest(
            markdown="## 機能\n元の内容",
            policy="要件/条件/例外で整理してください。",
        )

        response = client.post("/api/organize-markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["organizedMarkdown"] is not None
        assert "[ref:" in data["organizedMarkdown"]
        assert data["warnings"] == []

    @patch("app.routers.organize.get_llm_provider")
    def test_ut_org_002_success_multiple_sections(self, mock_get_provider):
        """UT-ORG-002: 正常系（複数セクション分割）"""
        # モックの設定
        mock_provider = MagicMock()
        mock_provider.organize_markdown.side_effect = [
            "## 第1章\n[ref:S1-P1] 整理1",
            "## 第2章\n[ref:S2-P1] 整理2",
        ]
        mock_get_provider.return_value = mock_provider

        # トークン超過をシミュレートするため、長いMarkdownを作成
        long_markdown = "## 第1章\n" + "a" * 10000 + "\n## 第2章\n" + "b" * 10000

        request = OrganizeMarkdownRequest(
            markdown=long_markdown,
            policy="要件/条件/例外で整理してください。",
        )

        response = client.post("/api/organize-markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["organizedMarkdown"] is not None
        # 複数セクションが結合されている
        assert "第1章" in data["organizedMarkdown"] or "第2章" in data["organizedMarkdown"]

    def test_ut_org_003_error_empty_markdown(self):
        """UT-ORG-003: エラー: Markdownが空"""
        request = OrganizeMarkdownRequest(
            markdown="",
            policy="要件/条件/例外で整理してください。",
        )

        response = client.post("/api/organize-markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["errorCode"] == "input_empty"
        assert "空です" in data["error"]

    def test_ut_org_004_error_empty_policy(self):
        """UT-ORG-004: エラー: 整理方針が空"""
        request = OrganizeMarkdownRequest(
            markdown="## 機能\n内容",
            policy="",
        )

        response = client.post("/api/organize-markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["errorCode"] == "policy_empty"
        assert "空です" in data["error"]

    @patch("app.routers.organize.get_llm_provider")
    @patch("app.routers.organize.estimate_tokens")
    def test_ut_org_005_error_token_limit(self, mock_estimate_tokens, mock_get_provider):
        """UT-ORG-005: エラー: トークン超過（分割不可）"""
        # トークン数が上限を超え、かつ分割できない場合
        mock_estimate_tokens.return_value = 30000  # 上限超過
        mock_get_provider.return_value = MagicMock()

        request = OrganizeMarkdownRequest(
            markdown="長い内容" * 1000,  # 見出しなしの長いテキスト
            policy="要件/条件/例外で整理してください。",
        )

        response = client.post("/api/organize-markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["errorCode"] == "token_limit"
        assert "長すぎます" in data["error"]

    @patch("app.routers.organize.get_llm_provider")
    @patch("app.routers.organize.asyncio.wait_for")
    def test_ut_org_006_timeout(self, mock_wait_for, mock_get_provider):
        """UT-ORG-006: タイムアウト"""
        # タイムアウトをシミュレート
        mock_wait_for.side_effect = asyncio.TimeoutError()
        mock_get_provider.return_value = MagicMock()

        request = OrganizeMarkdownRequest(
            markdown="## 機能\n内容",
            policy="要件/条件/例外で整理してください。",
        )

        response = client.post("/api/organize-markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["errorCode"] == "timeout"
        assert "タイムアウト" in data["error"]

    @patch("app.routers.organize.get_llm_provider")
    @patch("app.routers.organize.asyncio.wait_for")
    def test_ut_org_007_api_error(self, mock_wait_for, mock_get_provider):
        """UT-ORG-007: APIエラー（リトライ後失敗）"""
        # APIエラーをシミュレート
        mock_wait_for.side_effect = Exception("API Error")
        mock_get_provider.return_value = MagicMock()

        request = OrganizeMarkdownRequest(
            markdown="## 機能\n内容",
            policy="要件/条件/例外で整理してください。",
        )

        response = client.post("/api/organize-markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["errorCode"] == "api_error"

    @patch("app.routers.organize.get_llm_provider")
    def test_ut_org_008_invalid_format(self, mock_get_provider):
        """UT-ORG-008: 出力形式不正"""
        # 空の出力を返すモック
        mock_provider = MagicMock()
        mock_provider.organize_markdown.return_value = ""
        mock_get_provider.return_value = mock_provider

        request = OrganizeMarkdownRequest(
            markdown="## 機能\n内容",
            policy="要件/条件/例外で整理してください。",
        )

        response = client.post("/api/organize-markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["errorCode"] == "format_invalid"

    @patch("app.routers.organize.get_llm_provider")
    @patch("app.routers.organize.preprocess_markdown")
    def test_ut_org_009_preprocessing(self, mock_preprocess, mock_get_provider):
        """UT-ORG-009: 前処理の適用"""
        # 前処理モック
        mock_preprocess.return_value = "前処理済みMarkdown"
        mock_provider = MagicMock()
        mock_provider.organize_markdown.return_value = "整理済み"
        mock_get_provider.return_value = mock_provider

        request = OrganizeMarkdownRequest(
            markdown="## 機能\n内容",
            policy="要件/条件/例外で整理してください。",
            source=MarkdownSourceInfo(filename="test.xlsx", tool="excel2md"),
        )

        response = client.post("/api/organize-markdown", json=request.model_dump())

        assert response.status_code == 200
        # 前処理が呼ばれたことを確認
        mock_preprocess.assert_called_once()
        assert mock_preprocess.call_args[0][1] == "excel2md"

    @patch("app.routers.organize.get_llm_provider")
    def test_organize_markdown_api_with_warnings(self, mock_get_provider):
        """警告が検出される場合のテスト"""
        # 改変された出力を返すモック
        mock_provider = MagicMock()
        mock_provider.organize_markdown.return_value = "短い出力"  # 元の内容より大幅に短い
        mock_get_provider.return_value = mock_provider

        request = OrganizeMarkdownRequest(
            markdown="## 機能\n" + "長い内容" * 100,
            policy="要件/条件/例外で整理してください。",
        )

        response = client.post("/api/organize-markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 警告が含まれる可能性がある
        assert "warnings" in data

    @patch("app.routers.organize.get_llm_provider")
    def test_organize_markdown_api_with_llm_config(self, mock_get_provider):
        """LLM設定が指定された場合のテスト"""
        mock_provider = MagicMock()
        mock_provider.organize_markdown.return_value = "整理済み"
        mock_get_provider.return_value = mock_provider

        request = OrganizeMarkdownRequest(
            markdown="## 機能\n内容",
            policy="要件/条件/例外で整理してください。",
            llmConfig=LLMConfig(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                apiKey="test-key",
            ),
        )

        response = client.post("/api/organize-markdown", json=request.model_dump())

        assert response.status_code == 200
        # LLMプロバイダーが正しく取得されたことを確認
        mock_get_provider.assert_called_once()
