#!/usr/bin/env python3
"""
add_line_numbers.py のユニットテスト

テスト対象:
- 行番号付与処理
- ディレクトリ構造保持
- README.md自動生成
- エラーハンドリング
"""

import tempfile
import shutil
from pathlib import Path

import pytest

from add_line_numbers import (
    add_line_numbers_to_file,
    generate_directory_tree,
    generate_readme,
    process_directory,
)


class TestAddLineNumbersToFile:
    """add_line_numbers_to_file関数のテスト"""

    def test_basic_line_numbering(self, tmp_path):
        """基本的な行番号付与のテスト"""
        # 入力ファイル作成
        input_file = tmp_path / "input.txt"
        input_file.write_text("line1\nline2\nline3\n", encoding="utf-8")

        # 出力ファイル
        output_file = tmp_path / "output.txt"

        # 処理実行
        add_line_numbers_to_file(input_file, output_file)

        # 結果確認
        result = output_file.read_text(encoding="utf-8")
        lines = result.split("\n")

        assert lines[0] == "   1: line1"
        assert lines[1] == "   2: line2"
        assert lines[2] == "   3: line3"

    def test_line_number_format_single_digit(self, tmp_path):
        """1桁の行番号形式テスト（右揃え4桁）"""
        input_file = tmp_path / "input.txt"
        input_file.write_text("first line\n", encoding="utf-8")

        output_file = tmp_path / "output.txt"
        add_line_numbers_to_file(input_file, output_file)

        result = output_file.read_text(encoding="utf-8")
        # 形式: "   1: " (スペース3つ + 数字1つ + コロン + スペース)
        assert result.startswith("   1: ")

    def test_line_number_format_double_digit(self, tmp_path):
        """2桁の行番号形式テスト"""
        input_file = tmp_path / "input.txt"
        # 10行のファイルを作成
        content = "\n".join([f"line{i}" for i in range(1, 11)]) + "\n"
        input_file.write_text(content, encoding="utf-8")

        output_file = tmp_path / "output.txt"
        add_line_numbers_to_file(input_file, output_file)

        result = output_file.read_text(encoding="utf-8")
        lines = result.split("\n")

        # 10行目は "  10: " 形式
        assert lines[9].startswith("  10: ")

    def test_line_number_format_triple_digit(self, tmp_path):
        """3桁の行番号形式テスト"""
        input_file = tmp_path / "input.txt"
        # 100行のファイルを作成
        content = "\n".join([f"line{i}" for i in range(1, 101)]) + "\n"
        input_file.write_text(content, encoding="utf-8")

        output_file = tmp_path / "output.txt"
        add_line_numbers_to_file(input_file, output_file)

        result = output_file.read_text(encoding="utf-8")
        lines = result.split("\n")

        # 100行目は " 100: " 形式
        assert lines[99].startswith(" 100: ")

    def test_line_number_format_four_digit(self, tmp_path):
        """4桁の行番号形式テスト"""
        input_file = tmp_path / "input.txt"
        # 1000行のファイルを作成
        content = "\n".join([f"line{i}" for i in range(1, 1001)]) + "\n"
        input_file.write_text(content, encoding="utf-8")

        output_file = tmp_path / "output.txt"
        add_line_numbers_to_file(input_file, output_file)

        result = output_file.read_text(encoding="utf-8")
        lines = result.split("\n")

        # 1000行目は "1000: " 形式
        assert lines[999].startswith("1000: ")

    def test_empty_line_handling(self, tmp_path):
        """空行の処理テスト"""
        input_file = tmp_path / "input.txt"
        input_file.write_text("line1\n\nline3\n", encoding="utf-8")

        output_file = tmp_path / "output.txt"
        add_line_numbers_to_file(input_file, output_file)

        result = output_file.read_text(encoding="utf-8")
        lines = result.split("\n")

        # 空行にも行番号が付与される
        assert lines[1] == "   2: "

    def test_japanese_content(self, tmp_path):
        """日本語を含むファイルのテスト"""
        input_file = tmp_path / "input.txt"
        input_file.write_text("日本語テスト\n漢字とひらがな\n", encoding="utf-8")

        output_file = tmp_path / "output.txt"
        add_line_numbers_to_file(input_file, output_file)

        result = output_file.read_text(encoding="utf-8")
        lines = result.split("\n")

        assert lines[0] == "   1: 日本語テスト"
        assert lines[1] == "   2: 漢字とひらがな"

    def test_creates_output_directory(self, tmp_path):
        """出力ディレクトリが自動作成されることのテスト"""
        input_file = tmp_path / "input.txt"
        input_file.write_text("test\n", encoding="utf-8")

        # 存在しないディレクトリへの出力
        output_file = tmp_path / "subdir" / "nested" / "output.txt"

        add_line_numbers_to_file(input_file, output_file)

        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == "   1: test\n"


class TestGenerateDirectoryTree:
    """generate_directory_tree関数のテスト"""

    def test_simple_directory_tree(self, tmp_path):
        """シンプルなディレクトリツリー生成テスト"""
        # ディレクトリ構造を作成
        (tmp_path / "file1.txt").write_text("content", encoding="utf-8")
        (tmp_path / "file2.txt").write_text("content", encoding="utf-8")

        tree = generate_directory_tree(tmp_path)

        assert "file1.txt" in tree
        assert "file2.txt" in tree

    def test_nested_directory_tree(self, tmp_path):
        """ネストしたディレクトリツリー生成テスト"""
        # ネストしたディレクトリ構造を作成
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested_file.txt").write_text("content", encoding="utf-8")
        (tmp_path / "root_file.txt").write_text("content", encoding="utf-8")

        tree = generate_directory_tree(tmp_path)

        assert "subdir/" in tree
        assert "nested_file.txt" in tree
        assert "root_file.txt" in tree

    def test_max_depth_limit(self, tmp_path):
        """最大深度制限のテスト"""
        # 深いディレクトリ構造を作成
        current = tmp_path
        for i in range(10):
            current = current / f"level{i}"
            current.mkdir()
            (current / f"file{i}.txt").write_text("content", encoding="utf-8")

        # max_depth=2でツリー生成
        tree = generate_directory_tree(tmp_path, max_depth=2)

        # 深い階層のファイルは含まれない
        assert "level0/" in tree
        assert "level1/" in tree
        assert "level9/" not in tree

    def test_tree_symbols(self, tmp_path):
        """ツリー記号のテスト"""
        (tmp_path / "file1.txt").write_text("content", encoding="utf-8")
        (tmp_path / "file2.txt").write_text("content", encoding="utf-8")

        tree = generate_directory_tree(tmp_path)

        # ツリー記号が含まれていることを確認
        assert "├── " in tree or "└── " in tree


class TestGenerateReadme:
    """generate_readme関数のテスト"""

    def test_readme_created(self, tmp_path):
        """README.mdが生成されることのテスト"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        (output_dir / "test.txt").write_text("content", encoding="utf-8")

        generate_readme(output_dir, input_dir)

        readme_path = output_dir / "README.md"
        assert readme_path.exists()

    def test_readme_contains_required_sections(self, tmp_path):
        """README.mdに必要なセクションが含まれることのテスト"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        (output_dir / "test.txt").write_text("content", encoding="utf-8")

        generate_readme(output_dir, input_dir)

        readme_content = (output_dir / "README.md").read_text(encoding="utf-8")

        # 必須セクションの確認
        assert "## 概要" in readme_content
        assert "## 行番号の形式" in readme_content
        assert "## AIへの重要な指示" in readme_content
        assert "## ディレクトリ構造" in readme_content
        assert "## 生成元との関係" in readme_content
        assert "**生成日時**:" in readme_content

    def test_readme_contains_directory_tree(self, tmp_path):
        """README.mdにディレクトリツリーが含まれることのテスト"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        subdir = output_dir / "subdir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("content", encoding="utf-8")

        generate_readme(output_dir, input_dir)

        readme_content = (output_dir / "README.md").read_text(encoding="utf-8")

        assert "subdir/" in readme_content
        assert "file.txt" in readme_content


class TestProcessDirectory:
    """process_directory関数のテスト"""

    def test_processes_all_files(self, tmp_path):
        """全ファイルが処理されることのテスト"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        # 複数ファイルを作成
        (input_dir / "file1.txt").write_text("content1\n", encoding="utf-8")
        (input_dir / "file2.py").write_text("# python\n", encoding="utf-8")
        (input_dir / "file3.java").write_text("// java\n", encoding="utf-8")

        process_directory(str(input_dir), str(output_dir))

        # 全ファイルが出力されていることを確認
        assert (output_dir / "file1.txt").exists()
        assert (output_dir / "file2.py").exists()
        assert (output_dir / "file3.java").exists()

    def test_preserves_directory_structure(self, tmp_path):
        """ディレクトリ構造が保持されることのテスト"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        # ネストしたディレクトリ構造を作成
        subdir = input_dir / "sub" / "nested"
        subdir.mkdir(parents=True)
        (subdir / "deep_file.txt").write_text("content\n", encoding="utf-8")

        process_directory(str(input_dir), str(output_dir))

        # ディレクトリ構造が保持されていることを確認
        assert (output_dir / "sub" / "nested" / "deep_file.txt").exists()

    def test_line_numbers_added_to_output(self, tmp_path):
        """出力ファイルに行番号が付与されていることのテスト"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        (input_dir / "test.txt").write_text("line1\nline2\n", encoding="utf-8")

        process_directory(str(input_dir), str(output_dir))

        result = (output_dir / "test.txt").read_text(encoding="utf-8")
        assert result.startswith("   1: ")

    def test_readme_generated(self, tmp_path):
        """README.mdが生成されることのテスト"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        (input_dir / "test.txt").write_text("content\n", encoding="utf-8")

        process_directory(str(input_dir), str(output_dir))

        assert (output_dir / "README.md").exists()

    def test_nonexistent_input_directory(self, tmp_path):
        """存在しない入力ディレクトリのテスト"""
        input_dir = tmp_path / "nonexistent"
        output_dir = tmp_path / "output"

        with pytest.raises(SystemExit) as exc_info:
            process_directory(str(input_dir), str(output_dir))

        assert exc_info.value.code == 1

    def test_empty_input_directory(self, tmp_path, capsys):
        """空の入力ディレクトリのテスト"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        process_directory(str(input_dir), str(output_dir))

        captured = capsys.readouterr()
        assert "警告" in captured.out or "ファイルが見つかりません" in captured.out

    def test_skips_binary_files(self, tmp_path, capsys):
        """バイナリファイルがスキップされることのテスト"""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        # テキストファイル
        (input_dir / "text.txt").write_text("text content\n", encoding="utf-8")

        # バイナリファイル（PNG風のバイナリデータ）
        binary_file = input_dir / "image.png"
        binary_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

        process_directory(str(input_dir), str(output_dir))

        captured = capsys.readouterr()

        # テキストファイルは処理される
        assert (output_dir / "text.txt").exists()

        # バイナリファイルはスキップされる（出力されないか、エラーメッセージが出る）
        assert "スキップ" in captured.out or not (output_dir / "image.png").exists()


class TestFileTypeSupport:
    """各種ファイル形式のサポートテスト"""

    @pytest.mark.parametrize(
        "filename,content",
        [
            ("test.java", "public class Test {}\n"),
            ("test.py", "def test(): pass\n"),
            ("test.json", '{"key": "value"}\n'),
            ("test.xml", "<root></root>\n"),
            ("test.md", "# Header\n"),
            ("test.txt", "plain text\n"),
        ],
    )
    def test_various_file_types(self, tmp_path, filename, content):
        """各種ファイル形式が処理できることのテスト"""
        input_file = tmp_path / filename
        output_file = tmp_path / f"output_{filename}"

        input_file.write_text(content, encoding="utf-8")
        add_line_numbers_to_file(input_file, output_file)

        result = output_file.read_text(encoding="utf-8")
        assert result.startswith("   1: ")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
