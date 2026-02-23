"""CLI 統合テスト"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestCLIBuild:
    """build コマンドのテスト"""

    def test_build_simple_document(self):
        """基本的なビルド"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["uv", "run", "md2map", "build", str(FIXTURES_DIR / "simple.md"), "--out", tmpdir],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0

            # 出力ファイルの確認
            assert (Path(tmpdir) / "INDEX.md").exists()
            assert (Path(tmpdir) / "MAP.json").exists()
            assert (Path(tmpdir) / "parts").is_dir()

            # パートファイルの数を確認
            parts = list((Path(tmpdir) / "parts").glob("*.md"))
            assert len(parts) == 5  # H1 + 3 H2 + 1 H3

    def test_build_with_max_depth(self):
        """--max-depth オプション"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    "uv", "run", "md2map", "build",
                    str(FIXTURES_DIR / "nested.md"),
                    "--out", tmpdir,
                    "--max-depth", "2",
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0

            # H3 以下は含まれない
            map_path = Path(tmpdir) / "MAP.json"
            data = json.loads(map_path.read_text())
            levels = [entry["level"] for entry in data]
            assert 3 not in levels

    def test_build_dry_run(self):
        """--dry-run オプション"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    "uv", "run", "md2map", "build",
                    str(FIXTURES_DIR / "simple.md"),
                    "--out", tmpdir,
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0

            # ファイルは作成されない
            assert not (Path(tmpdir) / "INDEX.md").exists()
            assert not (Path(tmpdir) / "MAP.json").exists()

            # 出力にセクション情報が含まれる
            assert "Detected Sections" in result.stdout
            assert "Files to be generated" in result.stdout

    def test_build_verbose(self):
        """--verbose オプション"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    "uv", "run", "md2map", "build",
                    str(FIXTURES_DIR / "simple.md"),
                    "--out", tmpdir,
                    "--verbose",
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0

            # 詳細ログが出力される
            assert "Generated:" in result.stderr or "Generating" in result.stderr

    def test_build_nonexistent_file(self):
        """存在しないファイル"""
        result = subprocess.run(
            ["uv", "run", "md2map", "build", "/nonexistent/file.md"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_build_no_headings_warning(self):
        """見出しなしファイルで警告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    "uv", "run", "md2map", "build",
                    str(FIXTURES_DIR / "no_headings.md"),
                    "--out", tmpdir,
                ],
                capture_output=True,
                text=True,
            )

            # 終了コード 2（警告あり）
            assert result.returncode == 2

            # 警告メッセージ
            assert "warning" in result.stderr.lower()

    def test_build_with_id_prefix(self):
        """--id-prefix オプション"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    "uv", "run", "md2map", "build",
                    str(FIXTURES_DIR / "simple.md"),
                    "--out", tmpdir,
                    "--id-prefix", "DOC",
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0

            # MAP.json にカスタムプレフィックスのIDが含まれる
            map_path = Path(tmpdir) / "MAP.json"
            data = json.loads(map_path.read_text())
            ids = [entry.get("id") for entry in data]
            assert "DOC1" in ids
            assert "DOC2" in ids

            # INDEX.md にもカスタムプレフィックスのIDが含まれる
            index_path = Path(tmpdir) / "INDEX.md"
            content = index_path.read_text()
            assert "[DOC1]" in content
            assert "[DOC2]" in content


class TestCLIOutput:
    """出力内容のテスト"""

    def test_index_md_content(self):
        """INDEX.md の内容"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                ["uv", "run", "md2map", "build", str(FIXTURES_DIR / "simple.md"), "--out", tmpdir],
                capture_output=True,
            )

            index_path = Path(tmpdir) / "INDEX.md"
            content = index_path.read_text()

            # 必須セクション
            assert "# Index:" in content
            assert "## 構造ツリー" in content
            assert "## セクション詳細" in content

            # セクション情報
            assert "Simple Document" in content
            assert "Section One" in content

    def test_map_json_content(self):
        """MAP.json の内容"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                ["uv", "run", "md2map", "build", str(FIXTURES_DIR / "simple.md"), "--out", tmpdir],
                capture_output=True,
            )

            map_path = Path(tmpdir) / "MAP.json"
            data = json.loads(map_path.read_text())

            assert isinstance(data, list)
            assert len(data) > 0

            # 必須フィールド
            entry = data[0]
            assert "id" in entry
            assert "section" in entry
            assert "level" in entry
            assert "path" in entry
            assert "original_file" in entry
            assert "original_start_line" in entry
            assert "original_end_line" in entry
            assert "word_count" in entry
            assert "part_file" in entry
            assert "checksum" in entry

            # ID のフォーマット確認
            assert entry["id"].startswith("MD")
            assert entry["id"][2:].isdigit()

    def test_parts_file_content(self):
        """パートファイルの内容"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                ["uv", "run", "md2map", "build", str(FIXTURES_DIR / "simple.md"), "--out", tmpdir],
                capture_output=True,
            )

            parts_dir = Path(tmpdir) / "parts"
            part_files = list(parts_dir.glob("*.md"))
            assert len(part_files) > 0

            # 最初のパートファイルを確認
            content = part_files[0].read_text()

            # ヘッダ
            assert "<!--" in content
            assert "md2map fragment" in content
            assert "original:" in content
            assert "lines:" in content
            assert "section:" in content
            assert "level:" in content
            assert "-->" in content


class TestCLIJapanese:
    """日本語ファイルのテスト"""

    def test_build_japanese_document(self):
        """日本語ドキュメントのビルド"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["uv", "run", "md2map", "build", str(FIXTURES_DIR / "japanese.md"), "--out", tmpdir],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0

            # INDEX.md に日本語が含まれる
            index_path = Path(tmpdir) / "INDEX.md"
            content = index_path.read_text()
            assert "日本語ドキュメント" in content
            assert "概要" in content

            # MAP.json に日本語が含まれる
            map_path = Path(tmpdir) / "MAP.json"
            data = json.loads(map_path.read_text())
            sections = [entry["section"] for entry in data]
            assert "日本語ドキュメント" in sections

            # パートファイル名に日本語
            parts_dir = Path(tmpdir) / "parts"
            part_names = [p.name for p in parts_dir.glob("*.md")]
            assert any("日本語" in name for name in part_names)
