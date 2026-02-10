"""review.py の分割レビューAPI単体テスト

テストケース:
- UT-RSP-001: structure_matching() - 正常系（基本的なマッチング）
- UT-RSP-002: structure_matching() - 正常系（複数グループ）
- UT-RSP-003: structure_matching() - エラー（JSON解析失敗）
- UT-RSP-004: structure_matching() - エラー（LLMエラー）
- UT-RSP-005: review_group() - 正常系（基本的なグループレビュー）
- UT-RSP-006: review_group() - 正常系（カスタムシステムプロンプト）
- UT-RSP-007: review_group() - エラー（LLMエラー）
- UT-RSP-008: integrate_reviews() - 正常系（基本的な統合）
- UT-RSP-009: integrate_reviews() - 正常系（カスタムシステムプロンプト）
- UT-RSP-010: integrate_reviews() - エラー（LLMエラー）
- UT-RSP-011: _extract_json() - JSON抽出テスト
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    StructureMatchingRequest,
    DocumentStructure,
    CodeFileStructure,
    GroupReviewRequest,
    IntegrateRequest,
    GroupReviewSummary,
    SystemPrompt,
    LLMConfig,
)

client = TestClient(app)


class TestStructureMatchingAPI:
    """structure_matching() のテスト"""

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rsp_001_success_basic(self, mock_get_provider):
        """UT-RSP-001: 正常系（基本的なマッチング）"""
        # モックLLMレスポンス
        mock_response = json.dumps({
            "groups": [
                {
                    "id": "group1",
                    "name": "ユーザー管理",
                    "doc_sections": [
                        {"id": "MD1", "title": "ユーザー管理機能", "path": "ユーザー管理機能"}
                    ],
                    "code_symbols": [
                        {"id": "CD1", "filename": "user_service.py", "symbol": "UserService"}
                    ],
                    "reason": "ユーザー管理に関連する設計とコード"
                }
            ]
        })

        mock_provider = MagicMock()
        mock_provider.send_message.return_value = (mock_response, 100, 50)
        mock_get_provider.return_value = mock_provider

        request = StructureMatchingRequest(
            document=DocumentStructure(
                indexMd="# INDEX\n- MD1: ユーザー管理機能",
                mapJson={
                    "sections": [
                        {"id": "MD1", "title": "ユーザー管理機能", "level": 1, "path": "ユーザー管理機能", "startLine": 1, "endLine": 10}
                    ]
                }
            ),
            codeFiles=[
                CodeFileStructure(
                    filename="user_service.py",
                    indexMd="# CODE INDEX\n- CD1: UserService",
                    mapJson={
                        "symbols": [
                            {"id": "CD1", "name": "UserService", "symbolType": "class", "startLine": 1, "endLine": 50}
                        ]
                    }
                )
            ]
        )

        response = client.post(
            "/api/review/structure-matching", json=request.model_dump()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["totalGroups"] == 1
        assert len(data["groups"]) == 1
        assert data["groups"][0]["groupId"] == "group1"
        assert data["groups"][0]["groupName"] == "ユーザー管理"
        assert len(data["groups"][0]["docSections"]) == 1
        assert len(data["groups"][0]["codeSymbols"]) == 1
        assert data["tokensUsed"]["input"] == 100
        assert data["tokensUsed"]["output"] == 50

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rsp_002_success_multiple_groups(self, mock_get_provider):
        """UT-RSP-002: 正常系（複数グループ）"""
        mock_response = json.dumps({
            "groups": [
                {
                    "id": "group1",
                    "name": "ユーザー管理",
                    "doc_sections": [{"id": "MD1", "title": "ユーザー管理", "path": "ユーザー管理"}],
                    "code_symbols": [{"id": "CD1", "filename": "user.py", "symbol": "User"}],
                    "reason": "ユーザー管理"
                },
                {
                    "id": "group2",
                    "name": "認証機能",
                    "doc_sections": [{"id": "MD2", "title": "認証", "path": "認証"}],
                    "code_symbols": [{"id": "CD2", "filename": "auth.py", "symbol": "Auth"}],
                    "reason": "認証機能"
                }
            ]
        })

        mock_provider = MagicMock()
        mock_provider.send_message.return_value = (mock_response, 200, 100)
        mock_get_provider.return_value = mock_provider

        request = StructureMatchingRequest(
            document=DocumentStructure(
                indexMd="# INDEX\n- MD1: ユーザー管理\n- MD2: 認証",
                mapJson={"sections": []}
            ),
            codeFiles=[
                CodeFileStructure(
                    filename="user.py",
                    indexMd="# CODE\n- CD1: User",
                    mapJson={"symbols": []}
                ),
                CodeFileStructure(
                    filename="auth.py",
                    indexMd="# CODE\n- CD2: Auth",
                    mapJson={"symbols": []}
                )
            ]
        )

        response = client.post(
            "/api/review/structure-matching", json=request.model_dump()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["totalGroups"] == 2

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rsp_003_json_parse_error(self, mock_get_provider):
        """UT-RSP-003: エラー（JSON解析失敗）"""
        # 不正なJSONを返す
        mock_provider = MagicMock()
        mock_provider.send_message.return_value = ("not valid json {", 100, 50)
        mock_get_provider.return_value = mock_provider

        request = StructureMatchingRequest(
            document=DocumentStructure(
                indexMd="# INDEX",
                mapJson={"sections": []}
            ),
            codeFiles=[]
        )

        response = client.post(
            "/api/review/structure-matching", json=request.model_dump()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "JSON" in data["error"]

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rsp_004_llm_error(self, mock_get_provider):
        """UT-RSP-004: エラー（LLMエラー）"""
        mock_provider = MagicMock()
        mock_provider.send_message.side_effect = RuntimeError("LLM connection failed")
        mock_get_provider.return_value = mock_provider

        request = StructureMatchingRequest(
            document=DocumentStructure(
                indexMd="# INDEX",
                mapJson={"sections": []}
            ),
            codeFiles=[]
        )

        response = client.post(
            "/api/review/structure-matching", json=request.model_dump()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "LLM connection failed" in data["error"]


class TestGroupReviewAPI:
    """review_group() のテスト"""

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rsp_005_success_basic(self, mock_get_provider):
        """UT-RSP-005: 正常系（基本的なグループレビュー）"""
        mock_report = """## サマリー
整合性は概ね良好です。

## 突合結果一覧
| 設計書 | コード | 判定 | 指摘 |
|--------|--------|------|------|
| ユーザー登録 | register() | OK | - |

## 詳細
特に問題ありません。
"""

        mock_provider = MagicMock()
        mock_provider.send_message.return_value = (mock_report, 500, 200)
        mock_get_provider.return_value = mock_provider

        request = GroupReviewRequest(
            groupId="group1",
            groupName="ユーザー管理",
            documentContent="### ユーザー登録 (L1-L20)\n\n## ユーザー登録\n\nユーザーを登録する機能",
            codeContent="### user_service.py:register (method, L10-L25)\n\n```\ndef register(self, user):\n    # 登録処理\n```",
        )

        response = client.post("/api/review/group", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["groupId"] == "group1"
        assert data["reviewResult"]["report"] == mock_report
        assert data["tokensUsed"]["input"] == 500
        assert data["tokensUsed"]["output"] == 200

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rsp_006_with_system_prompt(self, mock_get_provider):
        """UT-RSP-006: 正常系（カスタムシステムプロンプト）"""
        mock_report = "カスタムフォーマットでのレビュー結果"

        mock_provider = MagicMock()
        mock_provider.send_message.return_value = (mock_report, 300, 100)
        mock_get_provider.return_value = mock_provider

        request = GroupReviewRequest(
            groupId="group1",
            groupName="テストグループ",
            documentContent="### テスト (L1-L5)\n\nテスト内容",
            codeContent="### test.py:test_func (function, L1-L3)\n\n```\ndef test_func(): pass\n```",
            systemPrompt=SystemPrompt(
                role="カスタムレビュアー",
                purpose="カスタム目的",
                format="カスタムフォーマット",
                notes="カスタム注意事項"
            )
        )

        response = client.post("/api/review/group", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # システムプロンプトが使用されていることを確認
        call_args = mock_provider.send_message.call_args
        assert "カスタムレビュアー" in call_args[0][0]  # system_prompt に含まれる

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rsp_007_llm_error(self, mock_get_provider):
        """UT-RSP-007: エラー（LLMエラー）"""
        mock_provider = MagicMock()
        mock_provider.send_message.side_effect = RuntimeError("API rate limit exceeded")
        mock_get_provider.return_value = mock_provider

        request = GroupReviewRequest(
            groupId="group1",
            groupName="テスト",
            documentContent="",
            codeContent=""
        )

        response = client.post("/api/review/group", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["groupId"] == "group1"
        assert "API rate limit exceeded" in data["error"]


class TestIntegrateReviewsAPI:
    """integrate_reviews() のテスト"""

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rsp_008_success_basic(self, mock_get_provider):
        """UT-RSP-008: 正常系（基本的な統合）"""
        mock_report = """# 統合レビューレポート

## 全体サマリー
2グループのレビューを統合しました。

## 主要な指摘事項
1. ユーザー管理で軽微な不整合

## 結論
全体的に整合性は良好です。
"""

        mock_provider = MagicMock()
        mock_provider.send_message.return_value = (mock_report, 800, 300)
        mock_provider.model_id = "claude-sonnet-4-20250514"
        mock_provider.provider_name = "anthropic"
        mock_get_provider.return_value = mock_provider

        request = IntegrateRequest(
            structureMatching={
                "groups": [
                    {"groupId": "group1", "groupName": "ユーザー管理"},
                    {"groupId": "group2", "groupName": "認証"}
                ]
            },
            groupReviews=[
                GroupReviewSummary(
                    groupId="group1",
                    groupName="ユーザー管理",
                    report="ユーザー管理のレビュー結果"
                ),
                GroupReviewSummary(
                    groupId="group2",
                    groupName="認証",
                    report="認証のレビュー結果"
                )
            ]
        )

        response = client.post("/api/review/integrate", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["report"] == mock_report
        assert data["integratedReport"]["overallSummary"] == "レビュー対象: 2グループ"
        assert data["tokensUsed"]["input"] == 800
        assert data["tokensUsed"]["output"] == 300
        assert data["reviewMeta"] is not None
        assert data["reviewMeta"]["provider"] == "anthropic"

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rsp_009_with_system_prompt(self, mock_get_provider):
        """UT-RSP-009: 正常系（カスタムシステムプロンプト）"""
        mock_report = "カスタムフォーマットの統合レポート"

        mock_provider = MagicMock()
        mock_provider.send_message.return_value = (mock_report, 400, 150)
        mock_provider.model_id = "gpt-4"
        mock_provider.provider_name = "openai"
        mock_get_provider.return_value = mock_provider

        request = IntegrateRequest(
            structureMatching={"groups": []},
            groupReviews=[
                GroupReviewSummary(
                    groupId="group1",
                    groupName="テスト",
                    report="テストレポート"
                )
            ],
            systemPrompt=SystemPrompt(
                role="カスタム統合者",
                purpose="カスタム統合目的",
                format="カスタム出力形式",
                notes="カスタム注意事項"
            )
        )

        response = client.post("/api/review/integrate", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # システムプロンプトが使用されていることを確認
        call_args = mock_provider.send_message.call_args
        assert "カスタム統合者" in call_args[0][0]

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rsp_010_llm_error(self, mock_get_provider):
        """UT-RSP-010: エラー（LLMエラー）"""
        mock_provider = MagicMock()
        mock_provider.send_message.side_effect = RuntimeError("Service unavailable")
        mock_get_provider.return_value = mock_provider

        request = IntegrateRequest(
            structureMatching={"groups": []},
            groupReviews=[]
        )

        response = client.post("/api/review/integrate", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Service unavailable" in data["error"]


class TestExtractJson:
    """_extract_json() のテスト"""

    def test_ut_rsp_011_extract_json_code_block(self):
        """UT-RSP-011: JSONコードブロックからの抽出"""
        from app.routers.review import _extract_json

        text = '''ここにテキスト

```json
{"key": "value", "number": 123}
```

追加テキスト'''

        result = _extract_json(text)
        assert result == {"key": "value", "number": 123}

    def test_extract_json_plain(self):
        """プレーンJSONの抽出"""
        from app.routers.review import _extract_json

        text = '{"key": "value"}'
        result = _extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_with_whitespace(self):
        """前後の空白を含むJSONの抽出"""
        from app.routers.review import _extract_json

        text = '  \n  {"key": "value"}  \n  '
        result = _extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_code_block_without_json_label(self):
        """jsonラベルなしのコードブロックからの抽出"""
        from app.routers.review import _extract_json

        text = '''```
{"key": "value"}
```'''

        result = _extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_invalid(self):
        """不正なJSONの場合は例外"""
        from app.routers.review import _extract_json

        text = "not a json"
        with pytest.raises(json.JSONDecodeError):
            _extract_json(text)


class TestStructureMatchingWithLLMConfig:
    """LLMConfig指定時のstructure_matching()テスト"""

    @patch("app.routers.review.get_llm_provider")
    def test_with_anthropic_config(self, mock_get_provider):
        """Anthropic設定でのテスト"""
        mock_response = json.dumps({"groups": []})
        mock_provider = MagicMock()
        mock_provider.send_message.return_value = (mock_response, 50, 25)
        mock_get_provider.return_value = mock_provider

        request = StructureMatchingRequest(
            document=DocumentStructure(indexMd="# INDEX", mapJson={}),
            codeFiles=[],
            llmConfig=LLMConfig(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                apiKey="test-api-key"
            )
        )

        response = client.post(
            "/api/review/structure-matching", json=request.model_dump()
        )

        assert response.status_code == 200
        # LLMConfigが渡されていることを確認
        mock_get_provider.assert_called_once()
        call_args = mock_get_provider.call_args
        assert call_args[0][0].provider == "anthropic"

    @patch("app.routers.review.get_llm_provider")
    def test_without_llm_config_uses_system_llm(self, mock_get_provider):
        """LLMConfig未指定時はシステムLLMを使用"""
        mock_response = json.dumps({"groups": []})
        mock_provider = MagicMock()
        mock_provider.send_message.return_value = (mock_response, 50, 25)
        mock_get_provider.return_value = mock_provider

        request = StructureMatchingRequest(
            document=DocumentStructure(indexMd="# INDEX", mapJson={}),
            codeFiles=[]
            # llmConfig は指定しない
        )

        response = client.post(
            "/api/review/structure-matching", json=request.model_dump()
        )

        assert response.status_code == 200
        # LLMConfigがNoneで呼ばれていることを確認
        mock_get_provider.assert_called_once()
        call_args = mock_get_provider.call_args
        assert call_args[0][0] is None
