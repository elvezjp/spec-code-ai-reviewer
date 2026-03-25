"""split.py の単体テスト

テストケース:
- UT-SPL-001: split_markdown() - 正常系（基本的なMarkdown分割）
- UT-SPL-002: split_markdown() - 正常系（maxDepth指定）
- UT-SPL-003: split_markdown() - セクションなし
- UT-SPL-004: split_markdown() - エラー（パースエラー）
- UT-SPL-005: split_code() - 正常系（Python）
- UT-SPL-006: split_code() - 正常系（Java）
- UT-SPL-007: split_code() - シンボルなし
- UT-SPL-008: split_code() - エラー（未対応言語）
- UT-SPL-009: split_code() - エラー（パースエラー）
- UT-SPL-010: _estimate_tokens() - トークン数推定
- UT-SPL-011: split_headings() - 正常系（見出し一覧取得）
- UT-SPL-012: split_headings() - 見出しなし
- UT-SPL-013: split_headings() - エラー
- UT-SPL-014: split_markdown() - 事前重要指定あり（pre_important_sections）
- UT-SPL-015: split_markdown() - 事前重要指定なし（後方互換性）
- UT-SPL-016: split_markdown() - 事前除外のみ指定（pre_excluded_sections）
- UT-SPL-017: split_markdown() - 事前重要 + 事前除外を同時指定
- UT-SPL-018: split_markdown() - 全セクションを事前除外
- UT-SPL-019: split_markdown() - preExcludedSections 未指定（後方互換性）
- UT-SPL-020: split_markdown() - summaryMode/summaryMaxChars デフォルト（後方互換性）
- UT-SPL-021: split_markdown() - maxSubsections をリクエストから取得
- UT-SPL-022: split_markdown() - summaryMode/summaryMaxChars を section_overrides に渡す
- UT-SPL-023: split_markdown() - summaryMode "ai" で LLM 設定が初期化される
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import SplitMarkdownRequest, SplitCodeRequest, HeadingsRequest

client = TestClient(app)


class TestSplitMarkdownAPI:
    """split_markdown() のテスト"""

    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.map_generator.generate_map")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_001_success_basic(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_map, mock_gen_parts
    ):
        """UT-SPL-001: 正常系（基本的なMarkdown分割）"""
        import json
        import os

        # モックセクション
        mock_section = MagicMock()
        mock_section.title = "概要"
        mock_section.display_name.return_value = "概要"
        mock_section.level = 1
        mock_section.path = "概要"
        mock_section.start_line = 1
        mock_section.end_line = 5
        mock_section.id = "MD1"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_section], [])
        mock_parser_cls.return_value = mock_parser

        mock_read_file.return_value = (
            ["# 概要\n", "\n", "これは概要です。\n", "\n", "詳細説明\n"],
            None,
        )

        # generate_partsがoutputディレクトリを作成する動作をシミュレート
        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        # generate_indexがINDEX.mdを書き込む動作をシミュレート
        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("# INDEX\n\n- MD1: 概要\n")

        mock_gen_index.side_effect = write_index

        # generate_mapがMAP.jsonを書き込む動作をシミュレート
        def write_map(sections, out_dir, map_path):
            map_data = [{"id": "MD1", "section": "概要", "level": 1, "path": "概要"}]
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump(map_data, f)
            return True

        mock_gen_map.side_effect = write_map

        request = SplitMarkdownRequest(
            content="# 概要\n\nこれは概要です。\n\n詳細説明",
            filename="test.md",
            maxDepth=2,
        )

        response = client.post("/api/split/markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["parts"]) == 1
        assert data["parts"][0]["section"] == "概要"
        assert data["parts"][0]["displayName"] == "概要"
        assert data["parts"][0]["level"] == 1
        assert data["parts"][0]["id"] == "MD1"
        assert data["indexContent"] is not None
        assert "INDEX" in data["indexContent"]
        assert data["mapJson"] is not None
        assert len(data["mapJson"]) == 1
        assert data["mapJson"][0]["id"] == "MD1"

    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.map_generator.generate_map")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_002_success_max_depth(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_map, mock_gen_parts
    ):
        """UT-SPL-002: 正常系（maxDepth指定）"""
        import json
        import os

        # H1とH2の両方を含むセクション
        mock_section1 = MagicMock()
        mock_section1.title = "第1章"
        mock_section1.display_name.return_value = "第1章"
        mock_section1.level = 1
        mock_section1.path = "第1章"
        mock_section1.start_line = 1
        mock_section1.end_line = 3
        mock_section1.id = "MD1"

        mock_section2 = MagicMock()
        mock_section2.title = "1.1 概要"
        mock_section2.display_name.return_value = "1.1 概要"
        mock_section2.level = 2
        mock_section2.path = "第1章 > 1.1 概要"
        mock_section2.start_line = 4
        mock_section2.end_line = 6
        mock_section2.id = "MD2"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_section1, mock_section2], [])
        mock_parser_cls.return_value = mock_parser

        mock_read_file.return_value = (
            ["# 第1章\n", "\n", "章の説明\n", "## 1.1 概要\n", "\n", "概要の説明\n"],
            None,
        )

        # generate_partsがoutputディレクトリを作成する動作をシミュレート
        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("# INDEX\n\n- MD1: 第1章\n- MD2: 1.1 概要\n")

        mock_gen_index.side_effect = write_index

        # generate_mapがMAP.jsonを書き込む動作をシミュレート
        def write_map(sections, out_dir, map_path):
            map_data = [
                {"id": "MD1", "section": "第1章", "level": 1, "path": "第1章"},
                {"id": "MD2", "section": "1.1 概要", "level": 2, "path": "第1章 > 1.1 概要"},
            ]
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump(map_data, f)
            return True

        mock_gen_map.side_effect = write_map

        request = SplitMarkdownRequest(
            content="# 第1章\n\n章の説明\n## 1.1 概要\n\n概要の説明",
            filename="test.md",
            maxDepth=3,  # H3まで分割
        )

        response = client.post("/api/split/markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["parts"]) == 2
        # maxDepthがパーサーに渡されていることを確認
        mock_parser.parse.assert_called_once()
        call_args = mock_parser.parse.call_args
        assert call_args[0][1] == 3  # maxDepth

    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_003_no_sections(self, mock_parser_cls, mock_read_file):
        """UT-SPL-003: セクションなし"""
        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([], [])  # セクションなし
        mock_parser_cls.return_value = mock_parser

        request = SplitMarkdownRequest(
            content="見出しのないテキスト",
            filename="test.md",
        )

        response = client.post("/api/split/markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["parts"] == []
        assert "No sections found" in data["indexContent"]

    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_004_parse_error(self, mock_parser_cls):
        """UT-SPL-004: エラー（パースエラー）"""
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = Exception("Parse error")
        mock_parser_cls.return_value = mock_parser

        request = SplitMarkdownRequest(
            content="# 壊れたMarkdown",
            filename="test.md",
        )

        response = client.post("/api/split/markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "エラー" in data["error"]

    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.map_generator.generate_map")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_010_token_estimation(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_map, mock_gen_parts
    ):
        """UT-SPL-010: トークン数推定"""
        import json
        import os

        mock_section = MagicMock()
        mock_section.title = "日本語セクション"
        mock_section.display_name.return_value = "日本語セクション"
        mock_section.level = 1
        mock_section.path = "日本語セクション"
        mock_section.start_line = 1
        mock_section.end_line = 2
        mock_section.id = "MD1"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_section], [])
        mock_parser_cls.return_value = mock_parser

        # 日本語と英語の混在テキスト
        japanese_content = "# 日本語セクション\nこれは日本語のテストです。This is English."
        lines = japanese_content.split("\n")
        mock_read_file.return_value = ([line + "\n" for line in lines], None)

        # generate_partsがoutputディレクトリを作成する動作をシミュレート
        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w") as f:
                f.write("# INDEX\n")

        mock_gen_index.side_effect = write_index

        # generate_mapがMAP.jsonを書き込む動作をシミュレート
        def write_map(sections, out_dir, map_path):
            map_data = [{"id": "MD1", "section": "日本語セクション", "level": 1}]
            with open(map_path, "w") as f:
                json.dump(map_data, f)
            return True

        mock_gen_map.side_effect = write_map

        request = SplitMarkdownRequest(
            content=japanese_content,
            filename="test.md",
        )

        response = client.post("/api/split/markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["parts"]) == 1
        # トークン数が推定されていることを確認
        assert data["parts"][0]["estimatedTokens"] > 0


class TestSplitCodeAPI:
    """split_code() のテスト"""

    @patch("code2map.generators.map_generator.generate_map")
    @patch("code2map.generators.parts_generator.generate_parts")
    @patch("code2map.generators.index_generator.generate_index")
    @patch("code2map.utils.file_utils.read_lines")
    @patch("code2map.utils.file_utils.slice_lines")
    @patch("code2map.parsers.python_parser.PythonParser")
    def test_ut_spl_005_success_python(
        self, mock_parser_cls, mock_slice, mock_read_lines, mock_gen_index, mock_gen_parts, mock_gen_map
    ):
        """UT-SPL-005: 正常系（Python）"""
        import json
        import os

        # モックシンボル
        mock_symbol = MagicMock()
        mock_symbol.name = "hello"
        mock_symbol.kind = "function"
        mock_symbol.parent = None
        mock_symbol.start_line = 1
        mock_symbol.end_line = 3
        mock_symbol.id = "CD1"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_symbol], [])
        mock_parser_cls.return_value = mock_parser

        mock_read_lines.return_value = ["def hello():", "    print('hello')", ""]
        mock_slice.return_value = "def hello():\n    print('hello')\n"

        # generate_partsがoutputディレクトリを作成しfragmentsを返す動作をシミュレート
        def create_output_dir_and_return_fragments(symbols, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)
            return [(mock_symbol, "def hello():\n    print('hello')\n")]

        mock_gen_parts.side_effect = create_output_dir_and_return_fragments

        def write_index(symbols, warnings, lines, index_path, filename):
            with open(index_path, "w") as f:
                f.write("# CODE INDEX\n\n- CD1: hello (function)\n")

        mock_gen_index.side_effect = write_index

        # generate_mapがMAP.jsonを書き込む動作をシミュレート
        def write_map(fragments, map_path):
            map_data = [{"id": "CD1", "symbol": "hello", "type": "function"}]
            with open(map_path, "w") as f:
                json.dump(map_data, f)

        mock_gen_map.side_effect = write_map

        request = SplitCodeRequest(
            content="def hello():\n    print('hello')\n",
            filename="test.py",
        )

        response = client.post("/api/split/code", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["language"] == "python"
        assert len(data["parts"]) == 1
        assert data["parts"][0]["symbol"] == "hello"
        assert data["parts"][0]["symbolType"] == "function"
        assert data["parts"][0]["id"] == "CD1"
        assert data["indexContent"] is not None
        assert data["mapJson"] is not None
        assert len(data["mapJson"]) == 1
        assert data["mapJson"][0]["id"] == "CD1"

    @patch("code2map.generators.map_generator.generate_map")
    @patch("code2map.generators.parts_generator.generate_parts")
    @patch("code2map.generators.index_generator.generate_index")
    @patch("code2map.utils.file_utils.read_lines")
    @patch("code2map.utils.file_utils.slice_lines")
    @patch("code2map.parsers.java_parser.JavaParser")
    def test_ut_spl_006_success_java(
        self, mock_parser_cls, mock_slice, mock_read_lines, mock_gen_index, mock_gen_parts, mock_gen_map
    ):
        """UT-SPL-006: 正常系（Java）"""
        import json
        import os

        # モッククラスシンボル
        mock_class = MagicMock()
        mock_class.name = "HelloWorld"
        mock_class.kind = "class"
        mock_class.parent = None
        mock_class.start_line = 1
        mock_class.end_line = 7
        mock_class.id = "CD1"

        # モックメソッドシンボル
        mock_method = MagicMock()
        mock_method.name = "main"
        mock_method.kind = "method"
        mock_method.parent = "HelloWorld"
        mock_method.start_line = 2
        mock_method.end_line = 5
        mock_method.id = "CD2"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_class, mock_method], [])
        mock_parser_cls.return_value = mock_parser

        java_code = """public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}"""
        mock_read_lines.return_value = java_code.split("\n")
        mock_slice.side_effect = [java_code, "public static void main(String[] args) {\n        System.out.println(\"Hello\");\n    }"]

        # generate_partsがoutputディレクトリを作成しfragmentsを返す動作をシミュレート
        def create_output_dir_and_return_fragments(symbols, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)
            return [(mock_class, java_code), (mock_method, "public static void main(String[] args) {\n        System.out.println(\"Hello\");\n    }")]

        mock_gen_parts.side_effect = create_output_dir_and_return_fragments

        def write_index(symbols, warnings, lines, index_path, filename):
            with open(index_path, "w") as f:
                f.write("# CODE INDEX\n\n- CD1: HelloWorld (class)\n  - CD2: main (method)\n")

        mock_gen_index.side_effect = write_index

        # generate_mapがMAP.jsonを書き込む動作をシミュレート
        def write_map(fragments, map_path):
            map_data = [
                {"id": "CD1", "symbol": "HelloWorld", "type": "class"},
                {"id": "CD2", "symbol": "main", "type": "method"},
            ]
            with open(map_path, "w") as f:
                json.dump(map_data, f)

        mock_gen_map.side_effect = write_map

        request = SplitCodeRequest(
            content=java_code,
            filename="HelloWorld.java",
        )

        response = client.post("/api/split/code", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["language"] == "java"
        assert len(data["parts"]) == 2
        assert data["parts"][0]["symbol"] == "HelloWorld"
        assert data["parts"][0]["symbolType"] == "class"
        assert data["parts"][1]["symbol"] == "main"
        assert data["parts"][1]["symbolType"] == "method"
        assert data["mapJson"] is not None
        assert len(data["mapJson"]) == 2
        assert data["parts"][1]["parentSymbol"] == "HelloWorld"

    @patch("code2map.utils.file_utils.read_lines")
    @patch("code2map.parsers.python_parser.PythonParser")
    def test_ut_spl_007_no_symbols(self, mock_parser_cls, mock_read_lines):
        """UT-SPL-007: シンボルなし"""
        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([], [])  # シンボルなし
        mock_parser_cls.return_value = mock_parser

        request = SplitCodeRequest(
            content="# コメントのみ\n# シンボルなし",
            filename="empty.py",
        )

        response = client.post("/api/split/code", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["parts"] == []
        assert data["language"] == "python"
        assert "No symbols found" in data["indexContent"]

    def test_ut_spl_008_unsupported_language(self):
        """UT-SPL-008: エラー（未対応言語）"""
        request = SplitCodeRequest(
            content="console.log('hello');",
            filename="test.js",  # JavaScript は未対応
        )

        response = client.post("/api/split/code", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "未対応" in data["error"]
        assert ".js" in data["error"]

    @patch("code2map.parsers.python_parser.PythonParser")
    def test_ut_spl_009_parse_error(self, mock_parser_cls):
        """UT-SPL-009: エラー（パースエラー）"""
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = Exception("Syntax error")
        mock_parser_cls.return_value = mock_parser

        request = SplitCodeRequest(
            content="def broken(",  # 構文エラーのあるコード
            filename="broken.py",
        )

        response = client.post("/api/split/code", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "エラー" in data["error"]


class TestEstimateTokens:
    """_estimate_tokens() のテスト"""

    def test_estimate_tokens_english(self):
        """英語のみのトークン推定"""
        from app.routers.split import _estimate_tokens

        # 英語は約0.25トークン/文字
        text = "Hello World"  # 11文字
        tokens = _estimate_tokens(text)
        assert tokens == int(11 * 0.25)

    def test_estimate_tokens_japanese(self):
        """日本語のみのトークン推定"""
        from app.routers.split import _estimate_tokens

        # 日本語は約1.5トークン/文字
        text = "こんにちは"  # 5文字（全て0x3000以上）
        tokens = _estimate_tokens(text)
        assert tokens == int(5 * 1.5)

    def test_estimate_tokens_mixed(self):
        """日本語と英語の混在"""
        from app.routers.split import _estimate_tokens

        text = "Hello世界"  # Hello(5文字) + 世界(2文字)
        tokens = _estimate_tokens(text)
        expected = int(2 * 1.5 + 5 * 0.25)  # 日本語2文字 + 英語5文字
        assert tokens == expected


class TestSplitHeadingsAPI:
    """split_headings() のテスト"""

    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_011_success_headings(self, mock_parser_cls):
        """UT-SPL-011: 正常系（見出し一覧取得）"""
        mock_parser = MagicMock()
        mock_parser.extract_headings.return_value = [
            {
                "title": "概要",
                "level": 1,
                "start_line": 1,
                "end_line": 5,
                "estimated_chars": 104,
            },
            {
                "title": "業務フロー",
                "level": 2,
                "start_line": 6,
                "end_line": 10,
                "estimated_chars": 41,
            },
        ]
        mock_parser_cls.return_value = mock_parser

        request = HeadingsRequest(content="# 概要\n\nテスト\n\n## 業務フロー\n\n内容")

        response = client.post("/api/split/headings", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["headings"]) == 2
        assert data["headings"][0]["title"] == "概要"
        assert data["headings"][0]["level"] == 1
        assert data["headings"][0]["startLine"] == 1
        assert data["headings"][0]["endLine"] == 5
        assert data["headings"][0]["estimatedChars"] == 104
        assert data["headings"][1]["title"] == "業務フロー"
        assert data["headings"][1]["level"] == 2

        # extract_headings が max_depth=2 で呼ばれたことを確認
        mock_parser.extract_headings.assert_called_once()
        call_args = mock_parser.extract_headings.call_args
        assert call_args[1]["max_depth"] == 2

    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_012_no_headings(self, mock_parser_cls):
        """UT-SPL-012: 見出しなし"""
        mock_parser = MagicMock()
        mock_parser.extract_headings.return_value = []
        mock_parser_cls.return_value = mock_parser

        request = HeadingsRequest(content="見出しのないテキスト")

        response = client.post("/api/split/headings", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["headings"] == []

    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_013_headings_error(self, mock_parser_cls):
        """UT-SPL-013: エラー"""
        mock_parser = MagicMock()
        mock_parser.extract_headings.side_effect = Exception("Parse error")
        mock_parser_cls.return_value = mock_parser

        request = HeadingsRequest(content="# テスト")

        response = client.post("/api/split/headings", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "エラー" in data["error"]


class TestSplitMarkdownPreImportantAPI:
    """split_markdown() の事前重要指定テスト"""

    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.map_generator.generate_map")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_014_pre_important_sections(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_map, mock_gen_parts
    ):
        """UT-SPL-014: 事前重要指定あり"""
        import json
        import os

        # モックセクション（事前重要指定セクションの範囲内）
        mock_section1 = MagicMock()
        mock_section1.title = "概要"
        mock_section1.display_name.return_value = "概要"
        mock_section1.level = 2
        mock_section1.path = "概要"
        mock_section1.start_line = 1
        mock_section1.end_line = 5
        mock_section1.id = "MD1"

        # 事前重要指定セクション内のサブスプリット
        mock_section2 = MagicMock()
        mock_section2.title = "変更履歴"
        mock_section2.display_name.return_value = "変更履歴"
        mock_section2.level = 2
        mock_section2.path = "変更履歴"
        mock_section2.start_line = 6
        mock_section2.end_line = 20
        mock_section2.id = "MD2"

        # 通常セクション
        mock_section3 = MagicMock()
        mock_section3.title = "その他"
        mock_section3.display_name.return_value = "その他"
        mock_section3.level = 2
        mock_section3.path = "その他"
        mock_section3.start_line = 21
        mock_section3.end_line = 30
        mock_section3.id = "MD3"

        # MarkdownParser のインスタンスを2つ作る必要がある
        # 1つ目は parse 用（section_overrides付き）
        # 2つ目は extract_headings 用
        mock_parser_parse = MagicMock()
        mock_parser_parse.parse.return_value = ([mock_section1, mock_section2, mock_section3], [])

        mock_parser_headings = MagicMock()
        mock_parser_headings.extract_headings.return_value = [
            {"title": "概要", "level": 2, "start_line": 1, "end_line": 5, "estimated_chars": 50},
            {"title": "変更履歴", "level": 2, "start_line": 6, "end_line": 20, "estimated_chars": 200},
            {"title": "その他", "level": 2, "start_line": 21, "end_line": 30, "estimated_chars": 100},
        ]

        # MarkdownParser() の呼び出しを順序で区別
        mock_parser_cls.side_effect = [mock_parser_parse, mock_parser_headings]

        lines = ["line\n"] * 30
        mock_read_file.return_value = (lines, None)

        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("# INDEX\n")

        mock_gen_index.side_effect = write_index

        def write_map(sections, out_dir, map_path):
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump([], f)

        mock_gen_map.side_effect = write_map

        request_data = {
            "content": "\n".join(["line"] * 30),
            "filename": "test.md",
            "maxDepth": 2,
            "splitMode": "heading",
            "preImportantSections": [6],  # 変更履歴セクション（start_line=6）を事前重要指定
            "preImportantSplitSettings": {
                "splitMode": "ai",
                "maxSubsections": 10,
                "splitInstructions": "詳細に分割",
            },
            "normalSplitSettings": {
                "splitMode": "heading",
                "maxSubsections": 5,
            },
        }

        response = client.post("/api/split/markdown", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["parts"]) == 3

        # 概要セクション（start_line=1）は事前重要指定ではない
        assert data["parts"][0]["preImportant"] is False
        # 変更履歴セクション（start_line=6）は事前重要指定
        assert data["parts"][1]["preImportant"] is True
        # その他セクション（start_line=21）は事前重要指定ではない
        assert data["parts"][2]["preImportant"] is False

        # MarkdownParser のコンストラクタ引数を確認
        # 1つ目の呼び出し（parse用）: section_overrides が渡されている
        first_call_kwargs = mock_parser_cls.call_args_list[0][1]
        assert first_call_kwargs["split_mode"] == "heading"  # 通常セクション設定
        assert first_call_kwargs["max_subsections"] == 5
        assert first_call_kwargs["section_overrides"] is not None
        assert len(first_call_kwargs["section_overrides"]) == 1
        assert first_call_kwargs["section_overrides"][0]["start_line"] == 6
        assert first_call_kwargs["section_overrides"][0]["split_mode"] == "ai"
        assert first_call_kwargs["section_overrides"][0]["max_subsections"] == 10

    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.map_generator.generate_map")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_015_backward_compatibility(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_map, mock_gen_parts
    ):
        """UT-SPL-015: 事前重要指定なし（後方互換性）"""
        import json
        import os

        mock_section = MagicMock()
        mock_section.title = "概要"
        mock_section.display_name.return_value = "概要"
        mock_section.level = 1
        mock_section.path = "概要"
        mock_section.start_line = 1
        mock_section.end_line = 5
        mock_section.id = "MD1"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_section], [])
        mock_parser_cls.return_value = mock_parser

        mock_read_file.return_value = (
            ["# 概要\n", "\n", "これは概要です。\n", "\n", "詳細説明\n"],
            None,
        )

        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("# INDEX\n\n- MD1: 概要\n")

        mock_gen_index.side_effect = write_index

        def write_map(sections, out_dir, map_path):
            map_data = [{"id": "MD1", "section": "概要", "level": 1, "path": "概要"}]
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump(map_data, f)

        mock_gen_map.side_effect = write_map

        # 従来のリクエスト（pre_important_sections なし）
        request = SplitMarkdownRequest(
            content="# 概要\n\nこれは概要です。\n\n詳細説明",
            filename="test.md",
            maxDepth=2,
        )

        response = client.post("/api/split/markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["parts"]) == 1
        # pre_important はデフォルト False
        assert data["parts"][0]["preImportant"] is False

        # MarkdownParser に section_overrides が渡されていないことを確認
        call_kwargs = mock_parser_cls.call_args[1]
        assert call_kwargs.get("section_overrides") is None


class TestSplitMarkdownPreExcludedAPI:
    """split_markdown() の事前除外指定テスト"""

    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.map_generator.generate_map")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_016_pre_excluded_only(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_map, mock_gen_parts
    ):
        """UT-SPL-016: 事前除外のみ指定 - 除外セクションが結果に含まれないこと"""
        import json
        import os

        # 除外されなかったセクションのみ parse() が返す
        mock_section1 = MagicMock()
        mock_section1.title = "概要"
        mock_section1.display_name.return_value = "概要"
        mock_section1.level = 2
        mock_section1.path = "概要"
        mock_section1.start_line = 1
        mock_section1.end_line = 5
        mock_section1.id = "MD1"

        # start_line=6 の「変更履歴」セクションは skip: True で parse() から除外される
        # start_line=21 の「その他」セクションは結果に含まれる
        mock_section3 = MagicMock()
        mock_section3.title = "その他"
        mock_section3.display_name.return_value = "その他"
        mock_section3.level = 2
        mock_section3.path = "その他"
        mock_section3.start_line = 21
        mock_section3.end_line = 30
        mock_section3.id = "MD2"

        mock_parser = MagicMock()
        # skip されたセクションは parse() の結果に含まれない
        mock_parser.parse.return_value = ([mock_section1, mock_section3], [])
        mock_parser_cls.return_value = mock_parser

        lines = ["line\n"] * 30
        mock_read_file.return_value = (lines, None)

        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("# INDEX\n\n- MD1: 概要\n- MD2: その他\n")

        mock_gen_index.side_effect = write_index

        def write_map(sections, out_dir, map_path):
            map_data = [
                {"id": "MD1", "section": "概要", "level": 2, "path": "概要"},
                {"id": "MD2", "section": "その他", "level": 2, "path": "その他"},
            ]
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump(map_data, f)

        mock_gen_map.side_effect = write_map

        request_data = {
            "content": "\n".join(["line"] * 30),
            "filename": "test.md",
            "maxDepth": 2,
            "preExcludedSections": [6],  # 変更履歴セクション（start_line=6）を事前除外
        }

        response = client.post("/api/split/markdown", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["parts"]) == 2

        # 除外されたセクション（変更履歴）が含まれていないことを確認
        section_titles = [p["section"] for p in data["parts"]]
        assert "概要" in section_titles
        assert "その他" in section_titles
        assert "変更履歴" not in section_titles

        # MarkdownParser に section_overrides が正しく渡されていることを確認
        call_kwargs = mock_parser_cls.call_args[1]
        assert call_kwargs["section_overrides"] is not None
        assert len(call_kwargs["section_overrides"]) == 1
        assert call_kwargs["section_overrides"][0]["start_line"] == 6
        assert call_kwargs["section_overrides"][0]["skip"] is True

    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.map_generator.generate_map")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_017_pre_important_and_pre_excluded(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_map, mock_gen_parts
    ):
        """UT-SPL-017: 事前重要 + 事前除外を同時指定 - 重要は結果に含まれ、除外は含まれない"""
        import json
        import os

        # 事前重要セクション（start_line=1）
        mock_section1 = MagicMock()
        mock_section1.title = "概要"
        mock_section1.display_name.return_value = "概要"
        mock_section1.level = 2
        mock_section1.path = "概要"
        mock_section1.start_line = 1
        mock_section1.end_line = 5
        mock_section1.id = "MD1"

        # 通常セクション（start_line=21）
        mock_section3 = MagicMock()
        mock_section3.title = "その他"
        mock_section3.display_name.return_value = "その他"
        mock_section3.level = 2
        mock_section3.path = "その他"
        mock_section3.start_line = 21
        mock_section3.end_line = 30
        mock_section3.id = "MD2"

        # MarkdownParser のインスタンスを2つ作る（parse用 + extract_headings用）
        mock_parser_parse = MagicMock()
        # skip されたセクション（start_line=6）は parse() の結果に含まれない
        mock_parser_parse.parse.return_value = ([mock_section1, mock_section3], [])

        mock_parser_headings = MagicMock()
        mock_parser_headings.extract_headings.return_value = [
            {"title": "概要", "level": 2, "start_line": 1, "end_line": 5, "estimated_chars": 50},
            {"title": "変更履歴", "level": 2, "start_line": 6, "end_line": 20, "estimated_chars": 200},
            {"title": "その他", "level": 2, "start_line": 21, "end_line": 30, "estimated_chars": 100},
        ]

        mock_parser_cls.side_effect = [mock_parser_parse, mock_parser_headings]

        lines = ["line\n"] * 30
        mock_read_file.return_value = (lines, None)

        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("# INDEX\n")

        mock_gen_index.side_effect = write_index

        def write_map(sections, out_dir, map_path):
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump([], f)

        mock_gen_map.side_effect = write_map

        request_data = {
            "content": "\n".join(["line"] * 30),
            "filename": "test.md",
            "maxDepth": 2,
            "splitMode": "heading",
            "preImportantSections": [1],  # 概要セクション（start_line=1）を事前重要指定
            "preImportantSplitSettings": {
                "splitMode": "ai",
                "maxSubsections": 10,
                "splitInstructions": "詳細に分割",
            },
            "normalSplitSettings": {
                "splitMode": "heading",
                "maxSubsections": 5,
            },
            "preExcludedSections": [6],  # 変更履歴セクション（start_line=6）を事前除外
        }

        response = client.post("/api/split/markdown", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["parts"]) == 2

        # 概要セクション（事前重要指定）は結果に含まれ、preImportant=True
        assert data["parts"][0]["section"] == "概要"
        assert data["parts"][0]["preImportant"] is True

        # その他セクション（通常）は結果に含まれ、preImportant=False
        assert data["parts"][1]["section"] == "その他"
        assert data["parts"][1]["preImportant"] is False

        # 除外されたセクション（変更履歴）が含まれていないことを確認
        section_titles = [p["section"] for p in data["parts"]]
        assert "変更履歴" not in section_titles

        # section_overrides に事前重要と事前除外の両方が含まれていることを確認
        first_call_kwargs = mock_parser_cls.call_args_list[0][1]
        overrides = first_call_kwargs["section_overrides"]
        assert overrides is not None
        assert len(overrides) == 2

        # 事前重要のoverride
        important_overrides = [o for o in overrides if o.get("split_mode") == "ai"]
        assert len(important_overrides) == 1
        assert important_overrides[0]["start_line"] == 1

        # 事前除外のoverride
        skip_overrides = [o for o in overrides if o.get("skip") is True]
        assert len(skip_overrides) == 1
        assert skip_overrides[0]["start_line"] == 6

    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_018_all_sections_excluded(self, mock_parser_cls, mock_read_file):
        """UT-SPL-018: 全セクションを事前除外 - 結果が空になること"""
        mock_parser = MagicMock()
        # 全セクションが skip されたため parse() は空リストを返す
        mock_parser.parse.return_value = ([], [])
        mock_parser_cls.return_value = mock_parser

        request_data = {
            "content": "## 概要\n\nテスト\n\n## 変更履歴\n\n内容",
            "filename": "test.md",
            "maxDepth": 2,
            "preExcludedSections": [1, 5],  # 全セクションを除外
        }

        response = client.post("/api/split/markdown", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["parts"] == []
        assert "No sections found" in data["indexContent"]

        # section_overrides に skip: True が正しく渡されていることを確認
        call_kwargs = mock_parser_cls.call_args[1]
        overrides = call_kwargs["section_overrides"]
        assert overrides is not None
        assert len(overrides) == 2
        assert all(o["skip"] is True for o in overrides)
        assert {o["start_line"] for o in overrides} == {1, 5}

    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.map_generator.generate_map")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_019_no_pre_excluded_backward_compat(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_map, mock_gen_parts
    ):
        """UT-SPL-019: preExcludedSections 未指定（後方互換性）"""
        import json
        import os

        mock_section = MagicMock()
        mock_section.title = "概要"
        mock_section.display_name.return_value = "概要"
        mock_section.level = 1
        mock_section.path = "概要"
        mock_section.start_line = 1
        mock_section.end_line = 5
        mock_section.id = "MD1"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_section], [])
        mock_parser_cls.return_value = mock_parser

        mock_read_file.return_value = (
            ["# 概要\n", "\n", "これは概要です。\n", "\n", "詳細説明\n"],
            None,
        )

        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("# INDEX\n\n- MD1: 概要\n")

        mock_gen_index.side_effect = write_index

        def write_map(sections, out_dir, map_path):
            map_data = [{"id": "MD1", "section": "概要", "level": 1, "path": "概要"}]
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump(map_data, f)

        mock_gen_map.side_effect = write_map

        # preExcludedSections を指定しないリクエスト
        request = SplitMarkdownRequest(
            content="# 概要\n\nこれは概要です。\n\n詳細説明",
            filename="test.md",
            maxDepth=2,
        )

        response = client.post("/api/split/markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["parts"]) == 1
        assert data["parts"][0]["section"] == "概要"

        # MarkdownParser に section_overrides が渡されていないことを確認
        call_kwargs = mock_parser_cls.call_args[1]
        assert call_kwargs.get("section_overrides") is None


class TestSplitMarkdownSummaryAPI:
    """summaryMode / summaryMaxChars / maxSubsections のテスト"""

    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.map_generator.generate_map")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_020_summary_default_backward_compat(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_map, mock_gen_parts
    ):
        """UT-SPL-020: summaryMode/summaryMaxChars 未指定時のデフォルト（後方互換性）"""
        import json
        import os

        mock_section = MagicMock()
        mock_section.title = "概要"
        mock_section.display_name.return_value = "概要"
        mock_section.level = 1
        mock_section.path = "概要"
        mock_section.start_line = 1
        mock_section.end_line = 5
        mock_section.id = "MD1"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_section], [])
        mock_parser_cls.return_value = mock_parser

        mock_read_file.return_value = (
            ["# 概要\n", "\n", "これは概要です。\n", "\n", "詳細説明\n"],
            None,
        )

        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("# INDEX\n\n- MD1: 概要\n")

        mock_gen_index.side_effect = write_index

        def write_map(sections, out_dir, map_path):
            map_data = [{"id": "MD1", "section": "概要", "level": 1, "path": "概要"}]
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump(map_data, f)

        mock_gen_map.side_effect = write_map

        # summaryMode / summaryMaxChars を指定しないリクエスト
        request = SplitMarkdownRequest(
            content="# 概要\n\nこれは概要です。\n\n詳細説明",
            filename="test.md",
            maxDepth=2,
        )

        response = client.post("/api/split/markdown", json=request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # MarkdownParser が呼ばれていることを確認（既存パラメータのみ）
        call_kwargs = mock_parser_cls.call_args[1]
        assert call_kwargs.get("section_overrides") is None
        # max_subsections はデフォルト 5
        assert call_kwargs["max_subsections"] == 5

    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.map_generator.generate_map")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_021_max_subsections_from_request(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_map, mock_gen_parts
    ):
        """UT-SPL-021: maxSubsections をリクエストから取得（環境変数フォールバック削除確認）"""
        import json
        import os

        mock_section = MagicMock()
        mock_section.title = "概要"
        mock_section.display_name.return_value = "概要"
        mock_section.level = 1
        mock_section.path = "概要"
        mock_section.start_line = 1
        mock_section.end_line = 5
        mock_section.id = "MD1"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_section], [])
        mock_parser_cls.return_value = mock_parser

        mock_read_file.return_value = (
            ["# 概要\n", "\n", "これは概要です。\n", "\n", "詳細説明\n"],
            None,
        )

        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("# INDEX\n\n- MD1: 概要\n")

        mock_gen_index.side_effect = write_index

        def write_map(sections, out_dir, map_path):
            map_data = [{"id": "MD1", "section": "概要", "level": 1, "path": "概要"}]
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump(map_data, f)

        mock_gen_map.side_effect = write_map

        # maxSubsections=8 を指定（preImportantSections なし）
        request_data = {
            "content": "# 概要\n\nこれは概要です。\n\n詳細説明",
            "filename": "test.md",
            "maxDepth": 2,
            "splitMode": "heading",
            "maxSubsections": 8,
        }

        response = client.post("/api/split/markdown", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # MarkdownParser に max_subsections=8 が渡されていることを確認
        call_kwargs = mock_parser_cls.call_args[1]
        assert call_kwargs["max_subsections"] == 8

    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.map_generator.generate_map")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_022_summary_in_section_overrides(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_map, mock_gen_parts
    ):
        """UT-SPL-022: summaryMode/summaryMaxChars が section_overrides に渡される"""
        import json
        import os

        # モックセクション
        mock_section1 = MagicMock()
        mock_section1.title = "概要"
        mock_section1.display_name.return_value = "概要"
        mock_section1.level = 2
        mock_section1.path = "概要"
        mock_section1.start_line = 1
        mock_section1.end_line = 5
        mock_section1.id = "MD1"

        mock_section2 = MagicMock()
        mock_section2.title = "変更履歴"
        mock_section2.display_name.return_value = "変更履歴"
        mock_section2.level = 2
        mock_section2.path = "変更履歴"
        mock_section2.start_line = 6
        mock_section2.end_line = 20
        mock_section2.id = "MD2"

        # MarkdownParser のインスタンスを2つ作る（parse用 + extract_headings用）
        mock_parser_parse = MagicMock()
        mock_parser_parse.parse.return_value = ([mock_section1, mock_section2], [])

        mock_parser_headings = MagicMock()
        mock_parser_headings.extract_headings.return_value = [
            {"title": "概要", "level": 2, "start_line": 1, "end_line": 5, "estimated_chars": 50},
            {"title": "変更履歴", "level": 2, "start_line": 6, "end_line": 20, "estimated_chars": 200},
        ]

        mock_parser_cls.side_effect = [mock_parser_parse, mock_parser_headings]

        lines = ["line\n"] * 20
        mock_read_file.return_value = (lines, None)

        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("# INDEX\n")

        mock_gen_index.side_effect = write_index

        def write_map(sections, out_dir, map_path):
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump([], f)

        mock_gen_map.side_effect = write_map

        request_data = {
            "content": "\n".join(["line"] * 20),
            "filename": "test.md",
            "maxDepth": 2,
            "splitMode": "heading",
            "preImportantSections": [6],
            "preImportantSplitSettings": {
                "splitMode": "heading",
                "summaryMode": "ai",
                "summaryMaxChars": 200,
            },
            "normalSplitSettings": {
                "splitMode": "heading",
                "summaryMode": "text",
                "summaryMaxChars": 150,
            },
        }

        response = client.post("/api/split/markdown", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 1つ目の呼び出し（parse用）の引数を確認
        first_call_kwargs = mock_parser_cls.call_args_list[0][1]

        # section_overrides に summary_mode / summary_max_chars が含まれている
        assert first_call_kwargs["section_overrides"] is not None
        assert len(first_call_kwargs["section_overrides"]) == 1
        override = first_call_kwargs["section_overrides"][0]
        assert override["start_line"] == 6
        assert override["summary_mode"] == "ai"
        assert override["summary_max_chars"] == 200

    @patch("app.routers.split._convert_to_md2map_llm_config")
    @patch("md2map.generators.parts_generator.generate_parts")
    @patch("md2map.generators.map_generator.generate_map")
    @patch("md2map.generators.index_generator.generate_index")
    @patch("md2map.utils.file_utils.read_file")
    @patch("md2map.parsers.markdown_parser.MarkdownParser")
    def test_ut_spl_023_summary_ai_triggers_llm_config(
        self, mock_parser_cls, mock_read_file, mock_gen_index, mock_gen_map,
        mock_gen_parts, mock_convert_llm
    ):
        """UT-SPL-023: summaryMode 'ai' で LLM 設定が初期化される"""
        import json
        import os

        mock_convert_llm.return_value = MagicMock()

        mock_section = MagicMock()
        mock_section.title = "概要"
        mock_section.display_name.return_value = "概要"
        mock_section.level = 1
        mock_section.path = "概要"
        mock_section.start_line = 1
        mock_section.end_line = 5
        mock_section.id = "MD1"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = ([mock_section], [])
        mock_parser_cls.return_value = mock_parser

        mock_read_file.return_value = (
            ["# 概要\n", "\n", "これは概要です。\n", "\n", "詳細説明\n"],
            None,
        )

        def create_output_dir(sections, lines, out_dir):
            os.makedirs(out_dir, exist_ok=True)

        mock_gen_parts.side_effect = create_output_dir

        def write_index(sections, warnings, index_path, filename):
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("# INDEX\n\n- MD1: 概要\n")

        mock_gen_index.side_effect = write_index

        def write_map(sections, out_dir, map_path):
            map_data = [{"id": "MD1", "section": "概要", "level": 1, "path": "概要"}]
            with open(map_path, "w", encoding="utf-8") as f:
                json.dump(map_data, f)

        mock_gen_map.side_effect = write_map

        # splitMode=heading だが summaryMode=ai を指定
        request_data = {
            "content": "# 概要\n\nこれは概要です。\n\n詳細説明",
            "filename": "test.md",
            "maxDepth": 2,
            "splitMode": "heading",
            "summaryMode": "ai",
        }

        response = client.post("/api/split/markdown", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # splitMode=heading なので split 自体は LLM 不要だが、
        # summaryMode=ai なので _convert_to_md2map_llm_config が呼ばれる
        mock_convert_llm.assert_called_once()
