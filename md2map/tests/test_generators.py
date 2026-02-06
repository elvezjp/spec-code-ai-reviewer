"""ジェネレーターのテスト"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from md2map.models.section import Section
from md2map.generators.parts_generator import (
    generate_parts,
    sanitize_filename,
    build_filename,
    generate_header,
)
from md2map.generators.index_generator import generate_index
from md2map.generators.map_generator import generate_map, calculate_checksum


class TestSanitizeFilename:
    """sanitize_filename のテスト"""

    def test_replace_spaces(self):
        """スペースをアンダースコアに置換"""
        assert sanitize_filename("hello world") == "hello_world"
        assert sanitize_filename("a b c") == "a_b_c"

    def test_remove_special_chars(self):
        """特殊文字を削除"""
        assert sanitize_filename("file/name") == "filename"
        assert sanitize_filename("file:name") == "filename"
        assert sanitize_filename('file"name') == "filename"
        assert sanitize_filename("file<name>") == "filename"

    def test_japanese_preserved(self):
        """日本語は保持"""
        assert sanitize_filename("日本語") == "日本語"
        assert sanitize_filename("テスト ファイル") == "テスト_ファイル"

    def test_consecutive_underscores(self):
        """連続するアンダースコアを1つに"""
        assert sanitize_filename("a  b") == "a_b"
        assert sanitize_filename("a___b") == "a_b"


class TestBuildFilename:
    """build_filename のテスト"""

    def test_simple_section(self):
        """単純なセクションのファイル名"""
        section = Section(
            title="Test Section",
            level=1,
            start_line=1,
            end_line=10,
            original_file="test.md",
        )
        section.path = "Test Section"

        filename = build_filename(section, set())
        assert filename == "Test_Section.md"

    def test_nested_section(self):
        """ネストしたセクションのファイル名"""
        parent = Section(
            title="Parent",
            level=1,
            start_line=1,
            end_line=20,
            original_file="test.md",
        )
        parent.path = "Parent"

        child = Section(
            title="Child",
            level=2,
            start_line=5,
            end_line=15,
            original_file="test.md",
        )
        child.parent = parent
        child.path = "Parent > Child"

        filename = build_filename(child, set())
        assert filename == "Parent_Child.md"

    def test_collision_avoidance(self):
        """ファイル名衝突の回避"""
        section = Section(
            title="Test",
            level=1,
            start_line=1,
            end_line=10,
            original_file="test.md",
        )
        section.path = "Test"

        existing = {"Test.md"}
        filename = build_filename(section, existing)
        assert filename == "Test_1.md"

        existing.add("Test_1.md")
        filename = build_filename(section, existing)
        assert filename == "Test_2.md"


class TestGenerateHeader:
    """generate_header のテスト"""

    def test_header_format(self):
        """ヘッダのフォーマット"""
        section = Section(
            title="Test Section",
            level=2,
            start_line=10,
            end_line=20,
            original_file="test.md",
        )

        header = generate_header(section)

        assert "md2map fragment" in header
        assert "original: test.md" in header
        assert "lines: 10-20" in header
        assert "section: Test Section" in header
        assert "level: 2" in header
        assert header.startswith("<!--")
        assert "-->" in header

    def test_header_with_id(self):
        """ID付きヘッダのフォーマット"""
        section = Section(
            title="Test Section",
            level=2,
            start_line=10,
            end_line=20,
            original_file="test.md",
            id="MD1",
        )

        header = generate_header(section)

        assert "id: MD1" in header
        assert "md2map fragment" in header

    def test_header_without_id(self):
        """IDなしの場合はid行を出力しない"""
        section = Section(
            title="Test Section",
            level=2,
            start_line=10,
            end_line=20,
            original_file="test.md",
        )

        header = generate_header(section)

        assert "id:" not in header


class TestGenerateParts:
    """generate_parts のテスト"""

    def test_generate_parts_creates_files(self):
        """パートファイルが生成される"""
        sections = [
            Section(
                title="Section One",
                level=1,
                start_line=1,
                end_line=3,
                original_file="test.md",
                path="Section One",
            ),
            Section(
                title="Section Two",
                level=1,
                start_line=4,
                end_line=6,
                original_file="test.md",
                path="Section Two",
            ),
        ]
        lines = [
            "# Section One\n",
            "Content one.\n",
            "\n",
            "# Section Two\n",
            "Content two.\n",
            "\n",
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            results = generate_parts(sections, lines, tmpdir)

            assert len(results) == 2

            # ファイルが存在する
            parts_dir = Path(tmpdir) / "parts"
            assert parts_dir.exists()
            assert (parts_dir / "Section_One.md").exists()
            assert (parts_dir / "Section_Two.md").exists()

            # part_file が設定される
            assert sections[0].part_file == "parts/Section_One.md"
            assert sections[1].part_file == "parts/Section_Two.md"

    def test_dry_run_no_files(self):
        """dry_run モードではファイルを作成しない"""
        sections = [
            Section(
                title="Test",
                level=1,
                start_line=1,
                end_line=2,
                original_file="test.md",
                path="Test",
            ),
        ]
        lines = ["# Test\n", "Content.\n"]

        with tempfile.TemporaryDirectory() as tmpdir:
            results = generate_parts(sections, lines, tmpdir, dry_run=True)

            assert len(results) == 1
            parts_dir = Path(tmpdir) / "parts"
            assert not parts_dir.exists()


class TestGenerateIndex:
    """generate_index のテスト"""

    def test_generate_index_structure(self):
        """INDEX.md の構造"""
        sections = [
            Section(
                title="Main",
                level=1,
                start_line=1,
                end_line=10,
                original_file="test.md",
                path="Main",
                summary="This is the main section.",
                keywords=["important"],
                part_file="parts/Main.md",
            ),
            Section(
                title="Sub",
                level=2,
                start_line=5,
                end_line=10,
                original_file="test.md",
                path="Main > Sub",
                part_file="parts/Main_Sub.md",
            ),
        ]
        sections[1].parent = sections[0]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "INDEX.md"
            generate_index(sections, [], str(output_path), "test.md")

            content = output_path.read_text()

            # ヘッダ
            assert "# Index: test.md" in content

            # 構造ツリー
            assert "## 構造ツリー" in content
            assert "Main (L1–L10)" in content
            assert "Sub (L5–L10)" in content

            # セクション詳細
            assert "## セクション詳細" in content
            assert "### Main (H1)" in content
            assert "- summary: This is the main section." in content
            assert "- keywords: important" in content

    def test_generate_index_with_warnings(self):
        """警告付きの INDEX.md"""
        sections = []
        warnings = ["Test warning 1", "Test warning 2"]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "INDEX.md"
            generate_index(sections, warnings, str(output_path), "test.md")

            content = output_path.read_text()

            assert "## Warnings" in content
            assert "[WARNING] Test warning 1" in content
            assert "[WARNING] Test warning 2" in content

    def test_generate_index_with_ids(self):
        """ID付きの INDEX.md"""
        sections = [
            Section(
                title="Main",
                level=1,
                start_line=1,
                end_line=10,
                original_file="test.md",
                path="Main",
                part_file="parts/Main.md",
                id="MD1",
            ),
            Section(
                title="Sub",
                level=2,
                start_line=5,
                end_line=10,
                original_file="test.md",
                path="Main > Sub",
                part_file="parts/Main_Sub.md",
                id="MD2",
            ),
        ]
        sections[1].parent = sections[0]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "INDEX.md"
            generate_index(sections, [], str(output_path), "test.md")

            content = output_path.read_text()

            # 構造ツリーにIDが含まれる
            assert "[MD1] Main (L1–L10)" in content
            assert "[MD2] Sub (L5–L10)" in content

            # セクション詳細にIDが含まれる
            assert "### [MD1] Main (H1)" in content
            assert "### [MD2] Sub (H2)" in content


class TestGenerateMap:
    """generate_map のテスト"""

    def test_generate_map_structure(self):
        """MAP.json の構造"""
        sections = [
            Section(
                title="Test Section",
                level=1,
                start_line=1,
                end_line=10,
                original_file="test.md",
                path="Test Section",
                word_count=50,
                part_file="parts/Test_Section.md",
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            # パートファイルを作成
            parts_dir = Path(tmpdir) / "parts"
            parts_dir.mkdir()
            part_file = parts_dir / "Test_Section.md"
            part_file.write_text("# Test Section\nContent here.")

            output_path = Path(tmpdir) / "MAP.json"
            generate_map(sections, tmpdir, str(output_path))

            # JSON をパース
            data = json.loads(output_path.read_text())

            assert len(data) == 1
            entry = data[0]

            assert entry["section"] == "Test Section"
            assert entry["level"] == 1
            assert entry["path"] == "Test Section"
            assert entry["original_file"] == "test.md"
            assert entry["original_start_line"] == 1
            assert entry["original_end_line"] == 10
            assert entry["word_count"] == 50
            assert entry["part_file"] == "parts/Test_Section.md"
            assert "checksum" in entry
            assert len(entry["checksum"]) == 64  # SHA-256

    def test_generate_map_with_id(self):
        """ID付きの MAP.json"""
        sections = [
            Section(
                title="Test Section",
                level=1,
                start_line=1,
                end_line=10,
                original_file="test.md",
                path="Test Section",
                word_count=50,
                part_file="parts/Test_Section.md",
                id="MD1",
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            # パートファイルを作成
            parts_dir = Path(tmpdir) / "parts"
            parts_dir.mkdir()
            part_file = parts_dir / "Test_Section.md"
            part_file.write_text("# Test Section\nContent here.")

            output_path = Path(tmpdir) / "MAP.json"
            generate_map(sections, tmpdir, str(output_path))

            # JSON をパース
            data = json.loads(output_path.read_text())

            assert len(data) == 1
            entry = data[0]

            # ID が先頭に含まれる
            assert entry["id"] == "MD1"
            # IDが最初のキーであることを確認
            assert list(entry.keys())[0] == "id"

    def test_generate_map_without_id(self):
        """IDなしの場合はidフィールドを含まない"""
        sections = [
            Section(
                title="Test Section",
                level=1,
                start_line=1,
                end_line=10,
                original_file="test.md",
                path="Test Section",
                word_count=50,
                part_file="parts/Test_Section.md",
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            # パートファイルを作成
            parts_dir = Path(tmpdir) / "parts"
            parts_dir.mkdir()
            part_file = parts_dir / "Test_Section.md"
            part_file.write_text("# Test Section\nContent here.")

            output_path = Path(tmpdir) / "MAP.json"
            generate_map(sections, tmpdir, str(output_path))

            # JSON をパース
            data = json.loads(output_path.read_text())

            assert len(data) == 1
            entry = data[0]

            # IDフィールドが存在しない
            assert "id" not in entry


class TestCalculateChecksum:
    """calculate_checksum のテスト"""

    def test_checksum_format(self):
        """チェックサムのフォーマット"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            f.write("Test content")
            f.flush()

            checksum = calculate_checksum(f.name)

            assert len(checksum) == 64
            assert all(c in "0123456789abcdef" for c in checksum)

            os.unlink(f.name)

    def test_checksum_deterministic(self):
        """同じ内容で同じチェックサム"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            f.write("Same content")
            f.flush()

            checksum1 = calculate_checksum(f.name)
            checksum2 = calculate_checksum(f.name)

            assert checksum1 == checksum2

            os.unlink(f.name)
