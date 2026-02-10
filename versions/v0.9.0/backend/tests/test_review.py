"""review.py のマッピングモード・構造マップテスト

テストケース:
- UT-REV-001: test_review_mode_parameter - モードパラメータのテスト
- UT-REV-002: test_mapping_user_message - マッピング用ユーザーメッセージの生成テスト
- UT-REV-003: test_structure_matching_with_mapping_mode - マッピングモードでの構造マッチングテスト
- UT-REV-004: test_group_review_with_mapping_mode - マッピングモードでのグループレビューテスト
- UT-REV-005: test_integrate_with_mapping_mode - マッピングモードでの統合テスト
- UT-REV-006: test_review_with_structure_map - 構造マップ付きレビューのテスト
- UT-REV-007: test_structure_map_prompt_inclusion - useStructureMap=true時のプロンプト確認
- UT-REV-008: test_structure_map_prompt_exclusion - useStructureMap=false時のプロンプト確認
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    ReviewMode,
    StructureMapInfo,
    DocumentMapEntry,
    CodeMapEntry,
    CodeFileMap,
    StructureMatchingRequest,
    DocumentStructure,
    CodeFileStructure,
    GroupReviewRequest,
    IntegrateRequest,
    GroupReviewSummary,
    SystemPrompt,
)
from app.services.prompt_builder import build_user_message

client = TestClient(app)


# テスト用のサンプルデータ
def _create_sample_structure_map() -> StructureMapInfo:
    """テスト用の構造マップを生成"""
    return StructureMapInfo(
        documentMap=[
            DocumentMapEntry(
                id="MD1",
                section="概要",
                level=1,
                path="概要",
                original_file="spec.md",
                original_start_line=1,
                original_end_line=10,
                word_count=100,
                part_file="part1.md",
                checksum="abc123",
            ),
            DocumentMapEntry(
                id="MD2",
                section="機能仕様",
                level=2,
                path="概要 > 機能仕様",
                original_file="spec.md",
                original_start_line=11,
                original_end_line=50,
                word_count=500,
                part_file="part2.md",
                checksum="def456",
            ),
        ],
        codeMaps=[
            CodeFileMap(
                filename="main.py",
                entries=[
                    CodeMapEntry(
                        id="CD1",
                        symbol="main",
                        type="function",
                        original_file="main.py",
                        original_start_line=1,
                        original_end_line=20,
                        part_file="code_part1.py",
                        checksum="ghi789",
                    ),
                    CodeMapEntry(
                        id="CD2",
                        symbol="UserService",
                        type="class",
                        original_file="main.py",
                        original_start_line=25,
                        original_end_line=100,
                        part_file="code_part2.py",
                        checksum="jkl012",
                    ),
                ],
            ),
        ],
    )


class TestReviewModeParameter:
    """モードパラメータのテスト"""

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rev_001_review_mode_parameter(self, mock_get_provider):
        """UT-REV-001: モードパラメータのテスト（review/mapping両方）"""
        from app.models.schemas import ReviewResponse, ReviewMeta

        mock_review_meta = ReviewMeta(
            version="v0.9.0",
            modelId="test-model",
            provider="test-provider",
            executedAt="2026-02-10 12:00",
            designs=[],
            programs=[],
            inputTokens=100,
            outputTokens=50,
        )
        mock_response = ReviewResponse(
            success=True,
            report="テストレポート",
            reviewMeta=mock_review_meta,
        )
        mock_provider = MagicMock()
        mock_provider.execute_review.return_value = mock_response
        mock_get_provider.return_value = mock_provider

        base_request = {
            "specMarkdown": "# 設計書",
            "specFilename": "spec.md",
            "codeWithLineNumbers": "   1: def main():\n   2:     pass",
            "codeFilename": "main.py",
            "systemPrompt": {
                "role": "レビュアー",
                "purpose": "レビュー",
                "format": "Markdown",
                "notes": "なし",
            },
        }

        # 突合モード（デフォルト）
        response = client.post("/api/review", json=base_request)
        assert response.status_code == 200

        # 突合モード（明示的）
        request_review = {**base_request, "mode": "review"}
        response = client.post("/api/review", json=request_review)
        assert response.status_code == 200

        # マッピングモード
        request_mapping = {**base_request, "mode": "mapping"}
        response = client.post("/api/review", json=request_mapping)
        assert response.status_code == 200


class TestMappingUserMessage:
    """マッピング用ユーザーメッセージのテスト"""

    def test_ut_rev_002_mapping_user_message(self):
        """UT-REV-002: マッピング用ユーザーメッセージの生成テスト"""
        message = build_user_message(
            spec_markdown=None,
            spec_filename=None,
            designs=[
                {
                    "filename": "spec.xlsx",
                    "content": "## 機能仕様\n| 機能 | 説明 |",
                    "isMain": True,
                    "type": "設計書",
                }
            ],
            codes=[
                {
                    "filename": "main.py",
                    "contentWithLineNumbers": "   1: def main():\n   2:     pass",
                }
            ],
            mode=ReviewMode.MAPPING,
        )

        # マッピングモードのキーワードが含まれる
        assert "マッピング" in message
        assert "設計書の各項目がどこで実装されているか" in message
        assert "未マッピング項目" in message

    def test_ut_rev_002_review_user_message(self):
        """突合モードのユーザーメッセージには「突合レビュー」が含まれる"""
        message = build_user_message(
            spec_markdown=None,
            spec_filename=None,
            designs=[
                {
                    "filename": "spec.xlsx",
                    "content": "## 機能仕様\n| 機能 | 説明 |",
                    "isMain": True,
                    "type": "設計書",
                }
            ],
            codes=[
                {
                    "filename": "main.py",
                    "contentWithLineNumbers": "   1: def main():\n   2:     pass",
                }
            ],
            mode=ReviewMode.REVIEW,
        )

        # 突合モードのキーワードが含まれる
        assert "突合レビュー" in message
        # マッピング固有のキーワードは含まれない
        assert "設計書の各項目がどこで実装されているか" not in message


class TestStructureMatchingWithMappingMode:
    """マッピングモードでの構造マッチングテスト"""

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rev_003_structure_matching_with_mapping_mode(self, mock_get_provider):
        """UT-REV-003: マッピングモードでの構造マッチングテスト"""
        mock_response = json.dumps({
            "groups": [
                {
                    "id": "group1",
                    "name": "マッピンググループ",
                    "doc_sections": [
                        {"id": "MD1", "title": "概要", "path": "概要"}
                    ],
                    "code_symbols": [
                        {"id": "CD1", "filename": "main.py", "symbol": "main"}
                    ],
                    "reason": "概要とmain関数のマッピング"
                }
            ]
        })

        mock_provider = MagicMock()
        mock_provider.send_message.return_value = (mock_response, 100, 50)
        mock_get_provider.return_value = mock_provider

        request = StructureMatchingRequest(
            document=DocumentStructure(
                indexMd="# INDEX\n- MD1: 概要",
                mapJson={"sections": [{"id": "MD1", "title": "概要", "level": 1}]}
            ),
            codeFiles=[
                CodeFileStructure(
                    filename="main.py",
                    indexMd="# CODE INDEX\n- CD1: main",
                    mapJson={"symbols": [{"id": "CD1", "name": "main", "symbolType": "function"}]}
                )
            ],
            mode=ReviewMode.MAPPING,
        )

        response = client.post(
            "/api/review/structure-matching",
            json=request.model_dump()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["groups"]) == 1


class TestGroupReviewWithMappingMode:
    """マッピングモードでのグループレビューテスト"""

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rev_004_group_review_with_mapping_mode(self, mock_get_provider):
        """UT-REV-004: マッピングモードでのグループレビューテスト"""
        mock_provider = MagicMock()
        mock_provider.send_message.return_value = (
            "# マッピング結果\n設計項目1 -> main.py:10",
            100,
            50
        )
        mock_get_provider.return_value = mock_provider

        request = GroupReviewRequest(
            groupId="group1",
            groupName="テストグループ",
            documentContent="# 機能仕様\nユーザー管理機能",
            codeContent="def user_create():\n    pass",
            mode=ReviewMode.MAPPING,
        )

        response = client.post(
            "/api/review/group",
            json=request.model_dump()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["groupId"] == "group1"


class TestIntegrateWithMappingMode:
    """マッピングモードでの統合テスト"""

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rev_005_integrate_with_mapping_mode(self, mock_get_provider):
        """UT-REV-005: マッピングモードでの統合テスト"""
        mock_provider = MagicMock()
        mock_provider.send_message.return_value = (
            "# 統合マッピングレポート\n全体カバレッジ: 85%",
            200,
            100
        )
        mock_provider.model_id = "test-model"
        mock_provider.provider_name = "test-provider"
        mock_get_provider.return_value = mock_provider

        request = IntegrateRequest(
            structureMatching={"groups": []},
            groupReviews=[
                GroupReviewSummary(
                    groupId="group1",
                    groupName="グループ1",
                    report="# グループ1のマッピング結果",
                )
            ],
            mode=ReviewMode.MAPPING,
        )

        response = client.post(
            "/api/review/integrate",
            json=request.model_dump()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report" in data


class TestReviewWithStructureMap:
    """構造マップ付きレビューのテスト"""

    @patch("app.routers.review.get_llm_provider")
    def test_ut_rev_006_review_with_structure_map(self, mock_get_provider):
        """UT-REV-006: 構造マップ付きレビューのテスト"""
        from app.models.schemas import ReviewResponse, ReviewMeta

        mock_review_meta = ReviewMeta(
            version="v0.9.0",
            modelId="test-model",
            provider="test-provider",
            executedAt="2026-02-10 12:00",
            designs=[],
            programs=[],
            inputTokens=100,
            outputTokens=50,
        )
        mock_response = ReviewResponse(
            success=True,
            report="テストレポート",
            reviewMeta=mock_review_meta,
        )
        mock_provider = MagicMock()
        mock_provider.execute_review.return_value = mock_response
        mock_get_provider.return_value = mock_provider

        structure_map = {
            "documentMap": [
                {
                    "id": "MD1",
                    "section": "概要",
                    "level": 1,
                    "path": "概要",
                    "original_file": "spec.md",
                    "original_start_line": 1,
                    "original_end_line": 10,
                    "word_count": 100,
                    "part_file": "part1.md",
                    "checksum": "abc123",
                }
            ],
            "codeMaps": [
                {
                    "filename": "main.py",
                    "entries": [
                        {
                            "id": "CD1",
                            "symbol": "main",
                            "type": "function",
                            "original_file": "main.py",
                            "original_start_line": 1,
                            "original_end_line": 20,
                            "part_file": "code_part1.py",
                            "checksum": "ghi789",
                        }
                    ]
                }
            ]
        }

        request = {
            "specMarkdown": "# 設計書",
            "specFilename": "spec.md",
            "codeWithLineNumbers": "   1: def main():\n   2:     pass",
            "codeFilename": "main.py",
            "systemPrompt": {
                "role": "レビュアー",
                "purpose": "レビュー",
                "format": "Markdown",
                "notes": "なし",
            },
            "mode": "mapping",
            "useStructureMap": True,
            "structureMap": structure_map,
        }

        response = client.post("/api/review", json=request)
        assert response.status_code == 200


class TestStructureMapPromptInclusion:
    """構造マップのプロンプト組み込みテスト"""

    def test_ut_rev_007_structure_map_prompt_inclusion(self):
        """UT-REV-007: useStructureMap=true時にプロンプトに構造マップが含まれることを確認"""
        structure_map = _create_sample_structure_map()

        message = build_user_message(
            spec_markdown=None,
            spec_filename=None,
            designs=[
                {
                    "filename": "spec.md",
                    "content": "# 設計書",
                    "isMain": True,
                }
            ],
            codes=[
                {
                    "filename": "main.py",
                    "contentWithLineNumbers": "   1: def main():\n   2:     pass",
                }
            ],
            mode=ReviewMode.MAPPING,
            use_structure_map=True,
            structure_map=structure_map,
        )

        # 構造マップのキーワードが含まれる
        assert "設計書構造マップ" in message
        assert "コード構造マップ" in message
        assert "MD1" in message
        assert "MD2" in message
        assert "CD1" in message
        assert "CD2" in message
        assert "概要" in message
        assert "機能仕様" in message
        assert "main" in message
        assert "UserService" in message


class TestStructureMapPromptExclusion:
    """構造マップのプロンプト除外テスト"""

    def test_ut_rev_008_structure_map_prompt_exclusion(self):
        """UT-REV-008: useStructureMap=false時にプロンプトに構造マップが含まれないことを確認"""
        message = build_user_message(
            spec_markdown=None,
            spec_filename=None,
            designs=[
                {
                    "filename": "spec.md",
                    "content": "# 設計書",
                    "isMain": True,
                }
            ],
            codes=[
                {
                    "filename": "main.py",
                    "contentWithLineNumbers": "   1: def main():\n   2:     pass",
                }
            ],
            mode=ReviewMode.REVIEW,
            use_structure_map=False,
            structure_map=None,
        )

        # 構造マップのキーワードは含まれない
        assert "設計書構造マップ" not in message
        assert "コード構造マップ" not in message

    def test_structure_map_excluded_when_flag_false_even_with_data(self):
        """useStructureMap=falseの場合、構造マップデータがあってもプロンプトに含まれない"""
        structure_map = _create_sample_structure_map()

        message = build_user_message(
            spec_markdown=None,
            spec_filename=None,
            designs=[
                {
                    "filename": "spec.md",
                    "content": "# 設計書",
                    "isMain": True,
                }
            ],
            codes=[
                {
                    "filename": "main.py",
                    "contentWithLineNumbers": "   1: def main():\n   2:     pass",
                }
            ],
            mode=ReviewMode.REVIEW,
            use_structure_map=False,
            structure_map=structure_map,  # データはあるがフラグがFalse
        )

        # 構造マップのキーワードは含まれない
        assert "設計書構造マップ" not in message
        assert "コード構造マップ" not in message
