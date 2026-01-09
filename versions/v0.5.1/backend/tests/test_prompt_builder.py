"""prompt_builder.py の単体テスト

テストケース（旧bedrock_service.pyから移行）:
- UT-BED-001: build_system_prompt() - 全項目指定時のプロンプト生成
- UT-BED-002: build_user_message() - 単一ファイル
- UT-BED-003: build_user_message() - 複数ファイル
- UT-BED-004: build_review_info_markdown() - 設計書・プログラム指定
- UT-BED-005: build_review_meta() - 設計書・プログラム指定
"""

import pytest

from app.services.prompt_builder import (
    build_review_info_markdown,
    build_review_meta,
    build_system_prompt,
    build_user_message,
)


class TestBuildSystemPrompt:
    """build_system_prompt() のテスト"""

    def test_ut_bed_001_all_fields(self):
        """UT-BED-001: 全項目指定時のプロンプト生成"""
        result = build_system_prompt(
            role="あなたはレビュアーです。",
            purpose="設計書とコードを突合してください。",
            format="マークダウン形式で出力してください。",
            notes="重要度順に報告してください。",
        )

        assert "## 役割" in result
        assert "あなたはレビュアーです。" in result
        assert "## 目的" in result
        assert "設計書とコードを突合してください。" in result
        assert "## 出力形式" in result
        assert "マークダウン形式で出力してください。" in result
        assert "## 注意事項" in result
        assert "重要度順に報告してください。" in result

    def test_build_system_prompt_empty_fields(self):
        """空のフィールドでもプロンプトが生成される"""
        result = build_system_prompt(role="", purpose="", format="", notes="")

        assert "## 役割" in result
        assert "## 目的" in result
        assert "## 出力形式" in result
        assert "## 注意事項" in result


class TestBuildUserMessage:
    """build_user_message() のテスト"""

    def test_ut_bed_002_single_file(self):
        """UT-BED-002: 単一ファイル"""
        result = build_user_message(
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
        )

        # レビュー対象一覧が含まれる
        assert "# レビュー対象一覧" in result
        assert "設計書: spec.xlsx" in result
        assert "プログラム: main.py" in result

        # 設計書詳細が含まれる
        assert "# 設計書詳細" in result
        assert "## 設計書: spec.xlsx" in result
        assert "種別: 設計書" in result
        assert "役割: メイン" in result
        assert "## 機能仕様" in result

        # プログラム詳細が含まれる
        assert "# プログラム詳細" in result
        assert "## プログラム: main.py" in result
        assert "def main():" in result

    def test_ut_bed_003_multiple_files(self):
        """UT-BED-003: 複数ファイル"""
        result = build_user_message(
            spec_markdown=None,
            spec_filename=None,
            designs=[
                {
                    "filename": "spec1.xlsx",
                    "content": "# 仕様書1",
                    "isMain": True,
                    "type": "設計書",
                },
                {
                    "filename": "api.xlsx",
                    "content": "# API仕様",
                    "isMain": False,
                    "type": "要件定義書",
                },
            ],
            codes=[
                {
                    "filename": "main.py",
                    "contentWithLineNumbers": "   1: main",
                },
                {
                    "filename": "util.py",
                    "contentWithLineNumbers": "   1: util",
                },
                {
                    "filename": "test.py",
                    "contentWithLineNumbers": "   1: test",
                },
            ],
        )

        # 設計書のセクション
        assert "## 設計書: spec1.xlsx" in result
        assert "## 設計書: api.xlsx" in result

        # プログラムのセクション
        assert "## プログラム: main.py" in result
        assert "## プログラム: util.py" in result
        assert "## プログラム: test.py" in result

        # レビュー対象一覧
        assert "設計書: spec1.xlsx" in result
        assert "設計書: api.xlsx" in result
        assert "プログラム: main.py" in result
        assert "プログラム: util.py" in result
        assert "プログラム: test.py" in result

    def test_build_user_message_legacy_format(self):
        """後方互換: 旧形式のフィールドからメッセージ生成"""
        result = build_user_message(
            spec_markdown="# 設計書\n旧形式",
            spec_filename="legacy_spec.xlsx",
            designs=[],
            codes=[],
            legacy_code_with_line_numbers="   1: legacy code",
            legacy_code_filename="legacy.py",
        )

        assert "設計書: legacy_spec.xlsx" in result
        assert "プログラム: legacy.py" in result
        assert "旧形式" in result
        assert "legacy code" in result

    def test_build_user_message_no_codes_raises(self):
        """コードなしでValueError"""
        with pytest.raises(ValueError, match="コードファイル"):
            build_user_message(
                spec_markdown=None,
                spec_filename=None,
                designs=[{"filename": "spec.xlsx", "content": "# spec"}],
                codes=[],
            )

    def test_build_user_message_no_designs_raises(self):
        """設計書なしでValueError"""
        with pytest.raises(ValueError, match="設計書"):
            build_user_message(
                spec_markdown=None,
                spec_filename=None,
                designs=[],
                codes=[{"filename": "main.py", "contentWithLineNumbers": "   1: code"}],
            )


class TestBuildReviewMeta:
    """build_review_meta() のテスト"""

    def test_ut_bed_005_build_review_meta(self):
        """UT-BED-005: 設計書・プログラム指定"""
        result = build_review_meta(
            version="v0.4.0",
            model_id="claude-haiku-4-5-20251001",
            provider="bedrock",
            designs=[
                {
                    "filename": "spec.xlsx",
                    "isMain": True,
                    "type": "設計書",
                    "tool": "markitdown",
                },
                {
                    "filename": "api.xlsx",
                    "isMain": False,
                    "type": "要件定義書",
                    "tool": "excel2md",
                },
            ],
            codes=[
                {"filename": "main.py"},
                {"filename": "util.py"},
            ],
            input_tokens=12500,
            output_tokens=3200,
        )

        assert result["version"] == "v0.4.0"
        assert result["modelId"] == "claude-haiku-4-5-20251001"
        assert result["provider"] == "bedrock"
        assert "executedAt" in result
        assert result["inputTokens"] == 12500
        assert result["outputTokens"] == 3200
        assert len(result["designs"]) == 2
        assert result["designs"][0]["filename"] == "spec.xlsx"
        assert result["designs"][0]["role"] == "メイン"
        assert result["designs"][0]["isMain"] is True
        assert result["designs"][0]["tool"] == "MarkItDown"
        assert result["designs"][1]["role"] == "参照"
        assert result["designs"][1]["isMain"] is False
        assert result["designs"][1]["tool"] == "excel2md"
        assert len(result["programs"]) == 2
        assert result["programs"][0]["filename"] == "main.py"

    def test_build_review_meta_default_values(self):
        """デフォルト値のテスト"""
        result = build_review_meta(
            version="v0.4.0",
            model_id="claude-haiku-4-5-20251001",
            provider="anthropic",
            designs=[{"filename": "spec.xlsx"}],
            codes=[{"filename": "main.py"}],
            input_tokens=100,
            output_tokens=50,
        )

        assert result["designs"][0]["role"] == "参照"  # デフォルトはFalse→参照
        assert result["designs"][0]["isMain"] is False
        assert result["designs"][0]["type"] == "設計書"
        assert result["designs"][0]["tool"] == "MarkItDown"
        assert result["provider"] == "anthropic"


class TestBuildReviewInfoMarkdown:
    """build_review_info_markdown() のテスト"""

    def test_ut_bed_004_build_review_info_markdown(self):
        """UT-BED-004: 設計書・プログラム指定"""
        review_meta = {
            "version": "v0.4.0",
            "modelId": "claude-haiku-4-5-20251001",
            "provider": "bedrock",
            "executedAt": "2024/12/21 14:30",
            "designs": [
                {
                    "filename": "spec.xlsx",
                    "role": "メイン",
                    "isMain": True,
                    "type": "設計書",
                    "tool": "MarkItDown",
                },
            ],
            "programs": [
                {"filename": "main.py"},
            ],
            "inputTokens": 12345,
            "outputTokens": 1234,
        }

        result = build_review_info_markdown(review_meta)

        assert "# 設計書-Javaプログラム突合 AIレビュアー レビューレポート" in result
        assert "## レビュー情報" in result
        assert "v0.4.0" in result
        assert "claude-haiku-4-5-20251001" in result
        assert "bedrock" in result
        assert "2024/12/21 14:30" in result
        assert "12,345" in result
        assert "1,234" in result
        assert "spec.xlsx" in result
        assert "main.py" in result
        assert "## AIによるレビュー結果" in result
        assert "以下はAIが出力したレビュー結果です。" in result

    def test_build_review_info_markdown_empty_lists(self):
        """空のリストでもエラーにならない"""
        review_meta = {
            "version": "v0.4.0",
            "modelId": "claude-haiku-4-5-20251001",
            "provider": "openai",
            "executedAt": "2024/12/21 14:30",
            "designs": [],
            "programs": [],
            "inputTokens": 0,
            "outputTokens": 0,
        }

        result = build_review_info_markdown(review_meta)

        assert "# 設計書-Javaプログラム突合 AIレビュアー レビューレポート" in result
        assert "## レビュー情報" in result
        assert "openai" in result
        assert "### 設計書" not in result
        assert "### プログラム" not in result
