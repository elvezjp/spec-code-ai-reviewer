"""マークダウンパーサーのテスト"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

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


class TestExtractHeadings:
    """extract_headings() のテスト"""

    @pytest.fixture
    def parser(self):
        return MarkdownParser()

    def test_basic_extraction(self, parser):
        """H1〜H4 の見出しを含む MD から正しく一覧取得"""
        content = "# Title\n\nIntro\n\n## Section A\n\nContent A\n\n### Sub A1\n\nContent A1\n\n## Section B\n\nContent B\n"
        headings = parser.extract_headings(content, max_depth=6)

        assert len(headings) == 4
        assert headings[0]["title"] == "Title"
        assert headings[0]["level"] == 1
        assert headings[1]["title"] == "Section A"
        assert headings[1]["level"] == 2
        assert headings[2]["title"] == "Sub A1"
        assert headings[2]["level"] == 3
        assert headings[3]["title"] == "Section B"
        assert headings[3]["level"] == 2

    def test_max_depth_filtering(self, parser):
        """max_depth=2 で H3 以下が除外される"""
        content = "# Title\n\n## Section A\n\n### Sub A1\n\n#### Deep\n\n## Section B\n"
        headings = parser.extract_headings(content, max_depth=2)

        levels = [h["level"] for h in headings]
        assert 1 in levels
        assert 2 in levels
        assert 3 not in levels
        assert 4 not in levels

    def test_code_block_exclusion(self, parser):
        """コードブロック内の # が見出しとして誤検出されない"""
        content = "# Title\n\n```\n# Not a heading\n## Also not\n```\n\n## Real Section\n"
        headings = parser.extract_headings(content)

        titles = [h["title"] for h in headings]
        assert "Not a heading" not in titles
        assert "Also not" not in titles
        assert "Title" in titles
        assert "Real Section" in titles

    def test_empty_content(self, parser):
        """見出しなしで空リストが返る"""
        content = "This is just plain text.\n\nNo headings here.\n"
        headings = parser.extract_headings(content)

        assert headings == []

    def test_end_line_calculation(self, parser):
        """最後のセクションの end_line が文書末尾になる"""
        content = "# Title\n\nIntro\n\n## Section A\n\nContent A\n\n## Section B\n\nContent B\nMore content\n"
        headings = parser.extract_headings(content)
        total_lines = len(content.splitlines(keepends=True))

        assert headings[-1]["end_line"] == total_lines

    def test_estimated_chars(self, parser):
        """文字数が正しく算出される"""
        content = "# Title\n\n## Section A\n\n12345\n"
        headings = parser.extract_headings(content)

        # Section A: "## Section A\n" + "\n" + "12345\n" の合計文字数
        section_a = [h for h in headings if h["title"] == "Section A"][0]
        assert section_a["estimated_chars"] > 0

    def test_consistency_with_build(self, parser):
        """extract_headings() の start_line が build 実行時と一致する"""
        content = (FIXTURES_DIR / "simple.md").read_text(encoding="utf-8")
        headings = parser.extract_headings(content, max_depth=3)
        sections, _ = parser.parse(str(FIXTURES_DIR / "simple.md"), max_depth=3)

        assert len(headings) == len(sections)
        for h, s in zip(headings, sections):
            assert h["start_line"] == s.start_line
            assert h["end_line"] == s.end_line
            assert h["title"] == s.title


class TestSectionOverrides:
    """section_overrides のテスト"""

    def test_no_overrides_backward_compatible(self):
        """override なし: 従来と同じ動作（後方互換性）"""
        parser_without = MarkdownParser()
        parser_with = MarkdownParser(section_overrides=None)

        sections_without, _ = parser_without.parse(str(FIXTURES_DIR / "simple.md"))
        sections_with, _ = parser_with.parse(str(FIXTURES_DIR / "simple.md"))

        assert len(sections_without) == len(sections_with)
        for s1, s2 in zip(sections_without, sections_with):
            assert s1.title == s2.title
            assert s1.start_line == s2.start_line

    def test_resolve_settings_no_override(self):
        """override マップにないセクションはコンストラクタ引数を返す"""
        parser = MarkdownParser(
            split_mode="ai",
            split_threshold=300,
            max_subsections=10,
            ai_prompt_extra_notes="test note",
            section_overrides=[{"start_line": 999, "split_mode": "heading"}],
        )
        # 存在しない start_line のセクション → デフォルト設定
        from md2map.models.section import Section
        section = Section(title="Test", level=1, start_line=1, end_line=10, original_file="test.md")
        settings = parser._resolve_settings(section)

        assert settings["split_mode"] == "ai"
        assert settings["split_threshold"] == 300
        assert settings["max_subsections"] == 10
        assert settings["ai_prompt_extra_notes"] == "test note"

    def test_resolve_settings_with_override(self):
        """override があるセクションは上書きされる"""
        parser = MarkdownParser(
            split_mode="ai",
            split_threshold=500,
            max_subsections=5,
            section_overrides=[
                {"start_line": 5, "max_subsections": 10, "split_threshold": 300},
            ],
        )
        from md2map.models.section import Section
        section = Section(title="Test", level=2, start_line=5, end_line=10, original_file="test.md")
        settings = parser._resolve_settings(section)

        assert settings["split_mode"] == "ai"  # 継承
        assert settings["split_threshold"] == 300  # 上書き
        assert settings["max_subsections"] == 10  # 上書き

    def test_override_split_mode_to_heading(self):
        """特定セクションを heading にオーバーライドするとサブスプリットされない"""
        # simple.md の Section One (start_line=5) を heading にオーバーライド
        # デフォルトは heading なので、全セクションが heading になる
        parser = MarkdownParser(
            split_mode="heading",
            section_overrides=[
                {"start_line": 5, "split_mode": "heading"},
            ],
        )
        sections, _ = parser.parse(str(FIXTURES_DIR / "simple.md"))

        # heading モードなのでサブスプリットなし
        subsplits = [s for s in sections if s.is_subsplit]
        assert len(subsplits) == 0

    def test_nonexistent_start_line_ignored(self):
        """存在しない start_line の override はコンストラクタ引数の設定で処理される"""
        parser = MarkdownParser(
            section_overrides=[
                {"start_line": 99999, "split_mode": "ai", "max_subsections": 10},
            ],
        )
        sections, _ = parser.parse(str(FIXTURES_DIR / "simple.md"))

        # 通常通り動作する（エラーなし）
        assert len(sections) > 0
        subsplits = [s for s in sections if s.is_subsplit]
        assert len(subsplits) == 0  # heading モードなのでサブスプリットなし

    def test_empty_overrides_list(self):
        """空のオーバーライドリストは従来と同じ動作"""
        parser = MarkdownParser(section_overrides=[])
        sections, _ = parser.parse(str(FIXTURES_DIR / "simple.md"))

        parser_default = MarkdownParser()
        sections_default, _ = parser_default.parse(str(FIXTURES_DIR / "simple.md"))

        assert len(sections) == len(sections_default)

    def test_constructor_args_as_default(self):
        """コンストラクタ引数がデフォルト設定として使われる"""
        parser = MarkdownParser(
            split_mode="heading",
            split_threshold=1000,
            max_subsections=3,
        )
        from md2map.models.section import Section
        section = Section(title="T", level=1, start_line=1, end_line=10, original_file="t.md")
        settings = parser._resolve_settings(section)

        assert settings["split_mode"] == "heading"
        assert settings["split_threshold"] == 1000
        assert settings["max_subsections"] == 3

    @patch("md2map.parsers.markdown_parser.MarkdownParser._ensure_llm_provider")
    def test_lazy_init_ai_called_on_override(self, mock_ensure):
        """デフォルト heading だが override で AI 指定時、遅延初期化が呼ばれる"""
        # japanese.md の最初のセクション (start_line=1) を AI にオーバーライド
        # split_threshold を非常に小さくしてサブスプリット条件を満たすようにする
        parser = MarkdownParser(
            split_mode="heading",
            section_overrides=[
                {"start_line": 1, "split_mode": "ai", "split_threshold": 1, "max_subsections": 3},
            ],
        )
        # _llm_provider が None なので _select_chunks_ai は空を返し、
        # フォールバック分割になるが、_ensure_llm_provider は呼ばれるはず
        parser.parse(str(FIXTURES_DIR / "japanese.md"))
        mock_ensure.assert_called()

    @patch("md2map.parsers.markdown_parser.MarkdownParser._ensure_nlp_tokenizer")
    def test_lazy_init_nlp_called_on_override(self, mock_ensure):
        """デフォルト heading だが override で NLP 指定時、遅延初期化が呼ばれる"""
        parser = MarkdownParser(
            split_mode="heading",
            section_overrides=[
                {"start_line": 1, "split_mode": "nlp", "split_threshold": 1, "max_subsections": 3},
            ],
        )
        parser.parse(str(FIXTURES_DIR / "japanese.md"))
        mock_ensure.assert_called()
