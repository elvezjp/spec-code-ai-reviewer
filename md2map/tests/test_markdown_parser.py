"""マークダウンパーサーのテスト"""

import os
from pathlib import Path

import pytest

from md2map.parsers.markdown_parser import MarkdownParser


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestMarkdownParser:
    """MarkdownParser のテスト"""

    @pytest.fixture
    def parser(self):
        """パーサーインスタンスを返す"""
        return MarkdownParser()

    def test_parse_simple_document(self, parser):
        """基本的なマークダウンファイルのパース"""
        sections, warnings = parser.parse(str(FIXTURES_DIR / "simple.md"))

        assert len(warnings) == 0
        assert len(sections) == 5  # H1 + 3 H2 + 1 H3

        # H1
        assert sections[0].title == "Simple Document"
        assert sections[0].level == 1
        assert sections[0].start_line == 1

        # H2
        assert sections[1].title == "Section One"
        assert sections[1].level == 2

        # H3
        assert sections[3].title == "Subsection"
        assert sections[3].level == 3

    def test_parse_with_code_blocks(self, parser):
        """コードブロック内の見出しをスキップする"""
        sections, warnings = parser.parse(str(FIXTURES_DIR / "with_code.md"))

        # コードブロック内の # はスキップされる
        titles = [s.title for s in sections]
        assert "This is a comment with ## heading-like text" not in titles
        assert "Another code block" not in titles

        # 通常の見出しは検出される
        assert "Document with Code" in titles
        assert "Code Example" in titles
        assert "Another Section" in titles

    def test_parse_japanese_document(self, parser):
        """日本語ドキュメントのパース"""
        sections, warnings = parser.parse(str(FIXTURES_DIR / "japanese.md"))

        assert len(warnings) == 0
        assert sections[0].title == "日本語ドキュメント"
        assert sections[1].title == "概要"

        # 日本語の文字数カウント
        assert sections[1].word_count > 0

    def test_parse_nested_document(self, parser):
        """深くネストした見出しのパース"""
        sections, warnings = parser.parse(str(FIXTURES_DIR / "nested.md"))

        # H1, H2, H3 のみ（デフォルト max_depth=3）
        levels = [s.level for s in sections]
        assert 1 in levels
        assert 2 in levels
        assert 3 in levels
        assert 4 not in levels  # H4 は含まれない

    def test_parse_with_max_depth(self, parser):
        """max_depth オプションの動作"""
        sections_depth2, _ = parser.parse(str(FIXTURES_DIR / "nested.md"), max_depth=2)
        sections_depth4, _ = parser.parse(str(FIXTURES_DIR / "nested.md"), max_depth=4)

        levels_depth2 = set(s.level for s in sections_depth2)
        levels_depth4 = set(s.level for s in sections_depth4)

        assert 3 not in levels_depth2
        assert 4 in levels_depth4

    def test_parse_no_headings(self, parser):
        """見出しがないドキュメント"""
        sections, warnings = parser.parse(str(FIXTURES_DIR / "no_headings.md"))

        assert len(warnings) == 1
        assert "No headings found" in warnings[0]
        assert len(sections) == 1  # 文書全体を1セクションとして扱う

    def test_hierarchy_path(self, parser):
        """階層パスの構築"""
        sections, _ = parser.parse(str(FIXTURES_DIR / "simple.md"))

        # H1
        assert sections[0].path == "Simple Document"
        assert sections[0].parent is None

        # H2
        assert sections[1].path == "Simple Document > Section One"
        assert sections[1].parent == sections[0]

        # H3
        subsection = [s for s in sections if s.title == "Subsection"][0]
        assert "Section Two" in subsection.path
        assert subsection.parent.title == "Section Two"

    def test_line_range(self, parser):
        """行範囲の検出"""
        sections, _ = parser.parse(str(FIXTURES_DIR / "simple.md"))

        # 各セクションの start_line < end_line
        for section in sections:
            assert section.start_line <= section.end_line
            assert section.start_line >= 1

        # 連続するセクションの境界
        for i in range(len(sections) - 1):
            assert sections[i].end_line == sections[i + 1].start_line - 1

    def test_extract_summary(self, parser):
        """要約の抽出"""
        sections, _ = parser.parse(str(FIXTURES_DIR / "simple.md"))

        # H1 の要約
        assert sections[0].summary is not None
        assert "simple markdown document" in sections[0].summary

        # Section One の要約
        section_one = [s for s in sections if s.title == "Section One"][0]
        assert section_one.summary is not None
        assert "first section" in section_one.summary

    def test_extract_keywords(self, parser):
        """キーワードの抽出（太字）"""
        sections, _ = parser.parse(str(FIXTURES_DIR / "simple.md"))

        section_one = [s for s in sections if s.title == "Section One"][0]
        assert "important" in section_one.keywords

    def test_extract_links(self, parser):
        """リンクの抽出"""
        sections, _ = parser.parse(str(FIXTURES_DIR / "simple.md"))

        section_two = [s for s in sections if s.title == "Section Two"][0]
        assert len(section_two.links) > 0
        assert ("link", "https://example.com") in section_two.links

    def test_nonexistent_file(self, parser):
        """存在しないファイルの処理"""
        sections, warnings = parser.parse("/nonexistent/path/file.md")

        assert len(sections) == 0
        assert len(warnings) > 0
        assert "not found" in warnings[0].lower() or "failed" in warnings[0].lower()


class TestEdgeCases:
    """エッジケースのテスト"""

    @pytest.fixture
    def parser(self):
        return MarkdownParser()

    def test_special_characters_in_title(self, parser):
        """タイトル内の特殊文字"""
        sections, _ = parser.parse(str(FIXTURES_DIR / "edge_cases.md"))

        # 特殊文字を含むタイトルが正しくパースされる
        titles = [s.title for s in sections]
        assert any("/\\" in t or ":*?" in t for t in titles)

    def test_duplicate_section_names(self, parser):
        """同名セクションの処理"""
        sections, _ = parser.parse(str(FIXTURES_DIR / "edge_cases.md"))

        # 同名セクションが両方検出される
        same_name_sections = [s for s in sections if s.title == "同名セクション"]
        assert len(same_name_sections) == 2

        # 行番号が異なる
        assert same_name_sections[0].start_line != same_name_sections[1].start_line

    def test_title_with_extra_spaces(self, parser):
        """タイトルの余分なスペース"""
        sections, _ = parser.parse(str(FIXTURES_DIR / "edge_cases.md"))

        # スペースがトリムされる
        titles = [s.title for s in sections]
        assert "Extra Spaces" in titles
        assert "   Extra Spaces" not in titles
